You are a senior AI systems architect and startup CTO.

Your task is to design and implement a production-ready SaaS platform called:

"AI Research Production System"

This is NOT a generic AI chatbot. This is a structured, multi-agent system that helps researchers go from idea → publishable research paper faster, with high quality and real evidence.

---

## 🎯 CORE PRODUCT GOAL

Build a system that:

* Reduces research time by 3–5x
* Improves quality of research output
* Helps users identify research gaps, structure papers, and generate drafts with strong reasoning and citations

The system must prioritize:

* Accuracy
* Evidence-backed outputs
* Structured workflows (NOT free chat)

---

## 🧩 SYSTEM ARCHITECTURE

Use:

Frontend:

* Next.js (App Router)
* TypeScript
* TailwindCSS
* Clean dashboard UI (Notion-like structured panels)

Backend:

* FastAPI
* LangGraph (for multi-agent orchestration)
* SSE (Server-Sent Events for real-time updates)

LLM Layer:

* OpenRouter (primary)
* Groq (fallback)

Retrieval:

* Tavily (web search)
* arXiv (academic papers)
* Optional: vector DB (Qdrant)

---

## 🤖 MULTI-AGENT SYSTEM DESIGN

Implement the following agents:

1. Clarification Agent

* Takes user topic
* Asks 5–10 critical questions:

  * scope
  * domain
  * research objective
  * hypothesis direction
  * constraints
* Output: structured research brief

---

2. Planning Agent

* Converts brief into:

  * research plan
  * sections
  * key questions to answer
* Shows plan to user for approval/edit

---

3. Retrieval Agent

* Fetches:

  * academic papers (arXiv)
  * real-time web data (Tavily)
* Returns:

  * summaries
  * key findings
  * contradictions
  * gaps

---

4. Synthesis Agent

* Combines retrieved data into:

  * themes
  * patterns
  * disagreements
  * research gaps
* Output must be structured (NOT paragraph dump)

---

5. Writing Agent

* Generates:

  * IEEE-style structured paper
  * sections:
    Abstract
    Introduction
    Literature Review
    Methodology
    Results (hypothetical if needed)
    Discussion
    Conclusion
* Must include inline citations

---

6. Critic Agent (VERY IMPORTANT)

* Reviews the paper
* Identifies:

  * weak arguments
  * missing citations
  * logical gaps
  * vague claims
* Outputs actionable feedback

---

7. Refinement Agent

* Improves writing:

  * clarity
  * academic tone
  * coherence
* Must NOT hallucinate new facts

---

## 🔁 CORE WORKFLOW

Step 1: User enters topic
Step 2: Clarification agent asks questions
Step 3: User answers
Step 4: Planning agent creates research plan
Step 5: User approves/edits plan
Step 6: Retrieval + synthesis
Step 7: Writing agent drafts paper
Step 8: Critic agent reviews
Step 9: Refinement agent improves
Step 10: Final output + export

---

## 🧠 UX REQUIREMENTS

DO NOT build chat UI.

Build structured interface:

* Left panel: user inputs + answers
* Center: research plan + generated sections
* Right panel: agent logs / progress

Include:

* step-by-step progress tracking
* editable sections
* regeneration per section

---

## ⚠️ CRITICAL RULES

* NEVER output fake citations
* ALWAYS separate:

  * facts
  * assumptions
  * generated content
* Avoid hallucinations
* If unsure → say "insufficient evidence"

---

## 💡 DIFFERENTIATION (IMPORTANT)

This system must feel like:

* a research workflow engine
  NOT
* a chatbot

It must:

* guide thinking
* structure output
* improve reasoning

---

## 📦 OUTPUT REQUIREMENTS

Generate:

1. Full backend code (FastAPI + LangGraph)
2. Agent prompts (modular and reusable)
3. Frontend UI structure (Next.js)
4. API routes
5. State management flow
6. Example test input/output

---

## 🚀 FINAL GOAL

Build a system that a professor or researcher would actually use to:

* save time
* improve research quality
* produce publishable work faster

Think like a startup founder, not a demo builder.
