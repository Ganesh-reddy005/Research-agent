import os
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from dotenv import load_dotenv

load_dotenv()

def get_llm(agent_name: str = None, temperature: float = 0.2, streaming: bool = True):
    """
    Returns an LLM instance based on the agent name or a default.
    """
    env_map = {
        "clarification": "CLARIFICATION_MODEL",
        "planning": "PLANNING_MODEL",
        "retrieval": "RETRIEVAL_MODEL",
        "synthesis": "SYNTHESIS_MODEL",
        "writer": "WRITING_MODEL",
        "critic": "CRITIC_MODEL",
        "refinement": "REFINEMENT_MODEL",
        "brainstorm": "BRAINSTORM_MODEL",
        "assistance": "ASSISTANCE_MODEL",
        "chat": "CHAT_MODEL"
    }

    # Per-agent model -> DEFAULT_MODEL -> built-in default
    model_id = os.getenv(env_map.get(agent_name, ""), "") or os.getenv("DEFAULT_MODEL", "") or "openai/gpt-5.4-mini"
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    groq_api_key = os.getenv("GROQ_API_KEY")

    # "groq:<model>" forces Groq, even for ids containing "/" (e.g. groq:openai/gpt-oss-120b)
    if model_id.startswith("groq:"):
        return ChatGroq(
            model=model_id.removeprefix("groq:"),
            temperature=temperature,
            api_key=groq_api_key,
            max_tokens=5000,
            streaming=streaming
        )

    if "/" in model_id or (openrouter_api_key and not groq_api_key):
        return ChatOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_api_key,
            model=model_id,
            temperature=temperature,
            max_tokens=4000,
            streaming=streaming
        )
    
    return ChatGroq(
        model=model_id,
        temperature=temperature,
        api_key=groq_api_key,
        max_tokens=5000,
        streaming=streaming
    )

async def ainvoke_llm(messages, agent_name: str = None, temperature: float = 0.2):
    llm = get_llm(agent_name=agent_name, temperature=temperature)
    return await llm.ainvoke(messages)

def invoke_llm(messages, agent_name: str = None, temperature: float = 0.2):
    llm = get_llm(agent_name=agent_name, temperature=temperature, streaming=False)
    return llm.invoke(messages)

class OpenRouterEmbeddings(OpenAIEmbeddings):
    """
    Custom embeddings class for OpenRouter leveraging OpenAIEmbeddings.
    """
    def __init__(self, model: str = None):
        model_name = model or os.getenv("EMBEDDING_MODEL", "mistralai/mistral-embed-2312")
        super().__init__(
            model=model_name,
            openai_api_base="https://openrouter.ai/api/v1",
            openai_api_key=os.getenv("OPENROUTER_API_KEY"),
            check_embedding_ctx_length=False
        )
