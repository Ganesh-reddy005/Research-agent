import re
from langchain_core.messages import SystemMessage, HumanMessage
from utils.llm import ainvoke_llm

async def citation_auditor_node(state):
    print("--- CITATION AUDITOR: Verifying source integrity ---")
    final_report = state.get("final_report", "")
    sources = state.get("raw_sources", [])
    
    if not final_report or not sources:
        return {"current_step": "citation_auditor"}

    # Extract all [n] citations from the report
    citation_refs = re.findall(r'\[(\d+)\]', final_report)
    unique_refs = sorted(list(set([int(ref) for ref in citation_refs])))
    
    # Create a mapping of source index to source metadata
    source_map = {}
    for i, src in enumerate(sources):
        source_map[i + 1] = {
            "title": src.get("title"),
            "url": src.get("url"),
            "source": src.get("source")
        }

    # Identify invalid citations (where n > number of sources)
    max_source_idx = len(sources)
    invalid_refs = [ref for ref in unique_refs if ref > max_source_idx]
    
    if not invalid_refs and citation_refs:
        print(f"Verified {len(unique_refs)} citations. All mapping to valid sources.")
        return {"current_step": "citation_auditor"}

    print(f"Warning: Found citations {invalid_refs} that do not map to retrieved sources.")
    
    # Optional: We could run a final pass to "re-index" or "fix" these, 
    # but for now, we'll just log and provide an audit report in the state.
    
    audit_results = {
        "total_citations_found": len(citation_refs),
        "unique_sources_cited": len(unique_refs),
        "invalid_citations": invalid_refs,
        "citation_mapping": {ref: source_map.get(ref, "UNKNOWN") for ref in unique_refs}
    }
    
    return {
        "citation_audit_log": audit_results,
        "current_step": "citation_auditor"
    }
