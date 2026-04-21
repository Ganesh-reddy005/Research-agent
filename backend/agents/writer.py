import os
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_qdrant import QdrantVectorStore
from utils.llm import ainvoke_llm, OpenRouterEmbeddings

async def writer_node(state):
    print("--- WRITER AGENT: Commencing academic draft ---")
    topic = state.get("topic")
    plan = state.get("research_plan", {})
    synthesis = state.get("synthesis_report")
    
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    collection_name = "research_assistant"
    
    embeddings = OpenRouterEmbeddings()
    vectorstore = None
    if qdrant_url:
        vectorstore = QdrantVectorStore.from_existing_collection(
            embedding=embeddings,
            collection_name=collection_name,
            url=qdrant_url,
            api_key=qdrant_api_key
        )
    
    # Generate content section by section
    full_report = ""
    sections = plan.get("sections", [])
    
    # If no sections, fall back to default IEEE
    if not sections:
        sections = [
            {"title": "Abstract", "description": "Summary of research"},
            {"title": "Introduction", "description": "Background and motivation"},
            {"title": "Methodology", "description": "Research approach"},
            {"title": "Findings", "description": "Key results"},
            {"title": "Conclusion", "description": "Summary and future work"}
        ]
        
    for section in sections:
        title = section.get("title")
        description = section.get("description")
        
        # Query Qdrant for this specific section
        context = ""
        if vectorstore:
            results = vectorstore.similarity_search(f"{title}: {description}", k=5)
            context = "\n".join([r.page_content for r in results])
            
        system_prompt = f"""You are an elite academic writer specialized in IEEE Transactions.
Write the '{title}' section for a high-impact research paper on: '{topic}'.
Section Description: {description}

STRICT FORMATTING & LENGTH RULES:
1. NO MARKDOWN BOLDING (**text**). Use plain text for emphasis.
2. Use professional, third-person objective academic tone.
3. Use formal IEEE citation style [1], [2] based on the context provided.
4. OPTIMAL LENGTH: Be concise but rigorous. Target 250-400 words for this section. Avoid fluff.
5. TECHNICAL DEPTH: Focus on evidence and technical data over generic descriptions.
6. Provide a smooth transition to the potential next section.
7. The output must be valid text that can be directly used in a LaTeX or Word document.

Synthesis Context:
{synthesis}

Relevant Evidence & Sources:
{context}
"""
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Write the {title} section now.")
        ]
        
        print(f"Drafting section: {title}...")
        response = await ainvoke_llm(messages, agent_name="writer", temperature=0.3)
        print(f"Completed {title}. ({len(response.content)} characters)")
        full_report += f"\n\n## {title}\n\n{response.content}\n"
        
    return {"draft_report": full_report, "current_step": "writer"}
