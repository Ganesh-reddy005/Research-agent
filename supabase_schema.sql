-- Supabase Schema for Lume.ai (Post-v1)

-- 1. Profiles Table (Linked to Supabase Auth)
CREATE TABLE public.profiles (
    id UUID REFERENCES auth.users(id) PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    orcid_id TEXT UNIQUE,
    tier TEXT DEFAULT 'free' CHECK (tier IN ('free', 'pro', 'academic')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Enable RLS for profiles
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can view own profile." ON public.profiles FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update own profile." ON public.profiles FOR UPDATE USING (auth.uid() = id);

-- Trigger to automatically create a profile after Supabase signup
CREATE OR REPLACE FUNCTION public.handle_new_user() 
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (id, email, full_name)
  VALUES (new.id, new.email, new.raw_user_meta_data->>'full_name');
  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE PROCEDURE public.handle_new_user();

-- 2. Projects Table (Groups research sessions)
CREATE TABLE public.projects (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Enable RLS for projects
ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can view own projects." ON public.projects FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own projects." ON public.projects FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own projects." ON public.projects FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own projects." ON public.projects FOR DELETE USING (auth.uid() = user_id);

-- 3. Sessions Table (Maps LangGraph thread_id to user)
CREATE TABLE public.sessions (
    thread_id TEXT PRIMARY KEY,
    project_id UUID REFERENCES public.projects(id) ON DELETE CASCADE,
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    topic TEXT NOT NULL,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'completed', 'failed')),
    research_mode TEXT DEFAULT 'deep',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    last_active TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Enable RLS for sessions
ALTER TABLE public.sessions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can view own sessions." ON public.sessions FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can manage own sessions." ON public.sessions FOR ALL USING (auth.uid() = user_id);

-- 4. Private Library Table (Metadata for uploaded PDFs)
CREATE TABLE public.library (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    filename TEXT NOT NULL,
    storage_path TEXT NOT NULL, -- Path in Supabase Storage
    title TEXT,
    authors TEXT[],
    parsing_status TEXT DEFAULT 'pending' CHECK (parsing_status IN ('pending', 'processing', 'completed', 'failed')),
    qdrant_collection_name TEXT,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Enable RLS for library
ALTER TABLE public.library ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can access own library." ON public.library FOR ALL USING (auth.uid() = user_id);

-- Note: The `langgraph-checkpoint-postgres` package will automatically create 
-- its own tables (checkpoints, checkpoint_blobs, checkpoint_writes) when initialized.
