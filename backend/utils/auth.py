import os
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
from typing import Optional
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

# Initialize Supabase client lazily or with validation
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()

def validate_config():
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        print("Auth Error: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY is missing in .env")
        return False
    
    # Common mistake: Using the database URL (db.xyz...) instead of the API URL (xyz...)
    if "db." in SUPABASE_URL:
        print(f"Auth Error: SUPABASE_URL appears to be a Database URL rather than an API URL: {SUPABASE_URL}")
        return False
        
    if not SUPABASE_URL.startswith("http"):
        print(f"Auth Error: SUPABASE_URL must start with http/https: {SUPABASE_URL}")
        return False
        
    return True

# Sanitize URL: Remove trailing slash if present
clean_url = SUPABASE_URL.rstrip("/")

if validate_config():
    supabase: Client = create_client(clean_url, SUPABASE_SERVICE_ROLE_KEY)
else:
    # We define a dummy client or handle it in get_current_user to avoid crashing on import
    supabase = None

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Verifies the Supabase JWT token and returns the user object.
    """
    token = credentials.credentials
    if not token or token == "undefined":
        print("Auth Error: Token is missing or 'undefined'")
        raise HTTPException(status_code=401, detail="Token is missing or 'undefined'")
        
    if supabase is None:
        # Re-check config in case env was loaded late
        if not validate_config():
            msg = "Backend configuration error: SUPABASE_URL might be a Database URL (starting with 'db.') instead of the Project API URL."
            if "db." in (SUPABASE_URL or ""):
                 raise HTTPException(status_code=500, detail=msg)
            raise HTTPException(status_code=500, detail="Supabase configuration is missing or invalid")

    try:
        # Get user from Supabase using the provided JWT
        res = supabase.auth.get_user(token)
        if not res.user:
            print(f"Auth Error: Supabase could not find user for token. Response: {res}")
            raise HTTPException(status_code=401, detail="Invalid session")
        return res.user
    except Exception as e:
        err_msg = str(e)
        print(f"Authentication failed with exception: {err_msg}")
        
        # provide helpful hint for the "Invalid path" error
        if "Invalid path" in err_msg:
            hint = ". Hint: Check if SUPABASE_URL is the Project API URL, not the Database URL (db.xyz...)."
            err_msg += hint
            
        raise HTTPException(status_code=401, detail=f"Authentication failed: {err_msg}")

def get_supabase_client():
    return supabase
