import os
from langchain_qdrant import QdrantVectorStore
from langchain_core.messages import SystemMessage, HumanMessage
from utils.llm import ainvoke_llm, OpenRouterEmbeddings

async def synthesis_node(state):
    print("--- SYNTHESIS AGENT ---")
    topic = state.get("topic")
    brief = state.get("research_brief")
    
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    
    thread_id = state.get("thread_id", "default_thread")
    collection_name = f"research_{thread_id.replace('-', '_')}"
    
    findings = ""
    if qdrant_url:
        embeddings = OpenRouterEmbeddings()
        vectorstore = QdrantVectorStore.from_existing_collection(
            embedding=embeddings,
            collection_name=collection_name,
            url=qdrant_url,
            api_key=qdrant_api_key
        )
        
        # Search for key themes
        results = vectorstore.similarity_search(topic, k=10)
        findings = "\n".join([r.page_content for r in results])
    
    system_prompt = """You are a senior research analyst.
Analyze the following retrieved data and synthesized findings for the research topic.
Identify:
1. Core themes and patterns
2. Major scholarly disagreements
3. Current research gaps
4. Solid evidence versus assumptions

Provide a structured synthesis report (Markdown format).
Make sure you maintain max 200 words only keeping it concise and to the point, avoiding large text blocks.
"""

    input_text = f"Topic: {topic}\nBrief: {brief}\n\nRetrieved Data:\n{findings}"
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=input_text)
    ]
    
    response = await ainvoke_llm(messages, agent_name="synthesis")
    return {"synthesis_report": response.content, "current_step": "synthesis"}
