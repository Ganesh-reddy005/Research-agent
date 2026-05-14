import os
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_core.embeddings import Embeddings
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
        "brainstorm": "BRAINSTORM_MODEL"
    }
    
    model_id = os.getenv(env_map.get(agent_name, "DEFAULT_MODEL"), "llama-3.3-70b-versatile")
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    groq_api_key = os.getenv("GROQ_API_KEY")

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

class OpenRouterEmbeddings(Embeddings):
    """
    Custom embeddings class for OpenRouter.
    """
    def __init__(self, model: str = None):
        self.model = model or os.getenv("EMBEDDING_MODEL", "mistralai/mistral-embed-2312")
        self.client = ChatOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
            model=self.model
        )

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        # OpenRouter's embedding endpoint
        import requests
        headers = {
            "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
            "Content-Type": "application/json"
        }
        url = "https://openrouter.ai/api/v1/embeddings"
        response = requests.post(url, headers=headers, json={"model": self.model, "input": texts})
        data = response.json()
        if "data" not in data:
            print(f"Embedding failed: {data}")
            return [[0.0] * 1024 for _ in texts]
        return [item["embedding"] for item in data["data"]]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]
