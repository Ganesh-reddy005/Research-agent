# Lume.ai - Post-v1 Strategic Roadmap

## The Current State
We have successfully built a high-fidelity "v1" product.
*   **Frontend:** A premium, "Modern Subtle" scholarly workbench with a high-conversion landing page.
*   **Backend:** A robust LangGraph multi-agent pipeline (Planner → Retriever → Indexer → Synthesis → Critic).
*   **Market Position:** Positioned against Perplexity (too broad) and Elicit (too focused on extraction). Lume.ai owns **Autonomous Synthesis & Verification**.

## Competitor Analysis & The "Missing Link"
Based on the 2026 AI research landscape:
1.  **Perplexity / Elicit:** Rely on public APIs (Semantic Scholar, OpenAlex). They fail when a researcher needs to analyze *paywalled* or *pre-published* proprietary data.
2.  **NotebookLM:** Excels at private data but lacks autonomous web discovery.
3.  **ResearchRabbit:** Wins on visual mapping but lacks deep text synthesis.
4.  **PapersFlow:** Wins on output format (native LaTeX).

**The Lume.ai Opportunity:** To become the ultimate sovereign research stack, we must bridge the gap between **autonomous public discovery** and **private corpus synthesis**.

---

## Phase 1: Deepening the Data Moat (The "Private Corpus" Feature)
Professors and pharma researchers have thousands of PDFs on their local machines. If we only search arXiv/OpenAlex, we miss their most valuable data.
*   **Product Action:** Implement a "Private Library" feature. Allow drag-and-drop of local PDFs.
*   **Technical Action:** Build an OCR/Parsing pipeline (e.g., unstructured.io) that feeds into our existing Qdrant Indexer Node. The `RetrieverNode` must be updated to query the *public* web and the *private* Qdrant collection simultaneously, weighting private data higher.

## Phase 2: Solving Architectural Bottlenecks (Graphify Insights)
According to our `GRAPH_REPORT.md`:
*   `ainvoke_llm()` and `OpenRouterEmbeddings` are our highest-connected "God Nodes" (central bottlenecks).
*   **The Risk:** If OpenRouter lags or rate-limits, the entire multi-agent pipeline stalls.
*   **Technical Action:** 
    1.  **Model Routing Tiering:** Stop using the heaviest model for every node. Route `Retriever` and `Indexer` tasks to ultra-fast/cheap models (Groq/Llama-3-8B). Reserve `Synthesis` and `Critic` for heavy reasoning models (Gemini 2.0 Pro).
    2.  **Decouple Embeddings:** Implement a local fallback for embeddings (e.g., `sentence-transformers` running on a background worker) to reduce API dependency on `OpenRouterEmbeddings`.

## Phase 3: The UX "Aha!" Moment (Visual Knowledge Graphs)
Users currently see a linear stream ("Intelligence Stream"). To compete with ResearchRabbit and build trust, we need to *show* them the data structure.
*   **Product Action:** As the `Retriever` and `Indexer` run, dynamically build a visual map of the papers being analyzed and how they connect.
*   **Technical Action:** Integrate `react-flow` or `d3.js` in a new `CitationGraph.tsx` panel. Feed it edges directly from the backend's metadata extraction.

## Phase 4: Professional Output Portability
Our current `html2pdf.js` export is fine for MVPs, but real academics write in LaTeX or Word.
*   **Product Action:** "Export to LaTeX / Overleaf" and "Export to Word (.docx) with active citation fields".
*   **Technical Action:** Replace the frontend PDF generator with a backend Pandoc/LaTeX compilation service. The `WriterNode` should output raw markdown with proper BibTeX citation keys.

## Summary GTM (Go-to-Market) Strategy
We don't target "students" looking for shortcuts. We target **Post-Docs, Principal Investigators, and R&D Teams**. We price high (e.g., $40/mo) based on the value of *time saved* on literature reviews and the guarantee of *Zero Hallucination* via our Integrity Auditor.