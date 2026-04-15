import os
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

def get_llm(model="primary", temperature=0.2):
    """
    Returns an LLM instance. Tries OpenRouter first (paid), falls back to Groq.
    """
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    
    if openrouter_api_key:
        try:
            # Primary model: OpenRouter (e.g., Gemini 2.0 Pro or Claude 3.5 Sonnet)
            return ChatOpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=openrouter_api_key,
                model="z-ai/glm-5.1", 
                temperature=temperature,
                max_tokens=2000
            )
        except Exception as e:
            print(f"Error initializing OpenRouter: {e}. Falling back to Groq.")
            
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("Neither OPENROUTER_API_KEY nor GROQ_API_KEY is available.")
        
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=temperature,
        api_key=groq_api_key,
        max_tokens=2000
    )

def invoke_llm(messages, temperature=0.2):
    llm = get_llm(temperature=temperature)
    return llm.invoke(messages)
