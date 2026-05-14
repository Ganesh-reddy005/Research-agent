# Graph Report - Research Agent  (2026-05-11)

## Corpus Check
- 58 files · ~178,776 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 264 nodes · 293 edges · 26 communities (20 shown, 6 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 29 edges (avg confidence: 0.76)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `58c9b679`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]

## God Nodes (most connected - your core abstractions)
1. `OpenRouterEmbeddings` - 17 edges
2. `ainvoke_llm()` - 12 edges
3. `Lume.ai - Post-v1 Strategic Roadmap` - 8 edges
4. `Multi-Agent Research Paper Assistant — Implementation Plan` - 8 edges
5. `Backend Architecture` - 8 edges
6. `supabase` - 7 edges
7. `Research Agent v2.0 - Multi-Agent Discovery System` - 7 edges
8. `Lume.ai Design System` - 7 edges
9. `getAuthHeaders()` - 6 edges
10. `get_supabase_client()` - 5 edges

## Surprising Connections (you probably didn't know these)
- `search_private_library()` --calls--> `OpenRouterEmbeddings`  [INFERRED]
  backend/agents/retriever.py → backend/utils/llm.py
- `retriever_node()` --calls--> `ainvoke_llm()`  [INFERRED]
  backend/agents/retriever.py → backend/utils/llm.py
- `assistance_node()` --calls--> `ainvoke_llm()`  [INFERRED]
  backend/agents/assistance.py → backend/utils/llm.py
- `refinement_node()` --calls--> `ainvoke_llm()`  [INFERRED]
  backend/agents/refinement.py → backend/utils/llm.py
- `clarification_node()` --calls--> `ainvoke_llm()`  [INFERRED]
  backend/agents/clarification.py → backend/utils/llm.py

## Communities (26 total, 6 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.09
Nodes (18): Dashboard(), getAgentIcon(), ResearchMode, Stage, LibraryPanelProps, StageClarificationProps, StageCompletedProps, StagePlanningProps (+10 more)

### Community 1 - "Community 1"
Cohesion: 0.07
Nodes (17): assistance_node(), brainstorm_chat(), Handles a brainstorming chat session.     Expects messages in format: [{"role":, clarification_node(), critic_node(), planner_node(), planning_node(), refinement_node() (+9 more)

### Community 2 - "Community 2"
Cohesion: 0.11
Nodes (20): BrainstormRequest, chat_with_data(), ChatRequest, list_library(), ResearchResumeRequest, ResearchStartRequest, resume_research(), start_research() (+12 more)

### Community 3 - "Community 3"
Cohesion: 0.11
Nodes (3): SidebarProps, AuthModalProps, supabase

### Community 4 - "Community 4"
Cohesion: 0.09
Nodes (22): `agents/critic.py` — Critic Agent, `agents/planner.py` — Planner Agent, `agents/retriever.py` — Retriever Agent, `agents/writer.py` — Writer Agent, API Keys Required, `api/main.py` — FastAPI with SSE, Automated, Backend Architecture (+14 more)

### Community 5 - "Community 5"
Cohesion: 0.1
Nodes (19): 1. Prerequisites, 2. Backend Initialization, 3. Frontend Initialization, Agent Workflow Diagram, 📂 Architecture, code:text (├── backend/), code:mermaid (graph TD), code:bash (cd backend) (+11 more)

### Community 6 - "Community 6"
Cohesion: 0.14
Nodes (13): 1. Planner Agent, 2. Retriever Agent, 3. Writer Agent, 4. Critic Agent, 🤖 Agents Definition, ⚙️ API Handling, 🚀 Bonus (optional if time permits), ⚡ Constraints (+5 more)

### Community 7 - "Community 7"
Cohesion: 0.22
Nodes (3): AgentLogsViewerProps, ReportViewerProps, SourceCardProps

### Community 8 - "Community 8"
Cohesion: 0.22
Nodes (8): Competitor Analysis & The "Missing Link", Lume.ai - Post-v1 Strategic Roadmap, Phase 1: Deepening the Data Moat (The "Private Corpus" Feature), Phase 2: Solving Architectural Bottlenecks (Graphify Insights), Phase 3: The UX "Aha!" Moment (Visual Knowledge Graphs), Phase 4: Professional Output Portability, Summary GTM (Go-to-Market) Strategy, The Current State

### Community 9 - "Community 9"
Cohesion: 0.25
Nodes (7): 1. Think Before Coding, 2. Simplicity First, 3. Surgical Changes, 4. Goal-Driven Execution, code:block1 (1. [Step] → verify: [check]), Gemini.md, graphify

### Community 10 - "Community 10"
Cohesion: 0.25
Nodes (7): 1. Vision, 2. Color Palette, 3. Typography, 4. UI Components (Modern Subtle), 4. UI Components (Sharp & Professional), 5. Dashboard Principles, Lume.ai Design System

### Community 11 - "Community 11"
Cohesion: 0.29
Nodes (5): ibmPlexMono, inter, metadata, playfair, spaceGrotesk

### Community 12 - "Community 12"
Cohesion: 0.33
Nodes (5): indexer_node(), fetch_full_text(), process_sources_with_full_text(), Takes an array of source dictionaries, grabs the top `max_sources`,      and app, Fetch the full markdown text of a URL using Jina Reader API.     Returns empty s

### Community 13 - "Community 13"
Cohesion: 0.29
Nodes (6): Backend (`.env`), ✅ Completed Tasks, 🔑 Environment Variables Required, Frontend (`.env.local`), 🚀 Immediate Next Steps (Pending), Lume.ai - Development Status & Next Steps

### Community 14 - "Community 14"
Cohesion: 0.4
Nodes (4): lifespan(), AgentState, build_graph(), TypedDict

### Community 15 - "Community 15"
Cohesion: 0.4
Nodes (4): code:bash (npm run dev), Deploy on Vercel, Getting Started, Learn More

### Community 18 - "Community 18"
Cohesion: 0.67
Nodes (3): getAgentIcon(), StageResearching(), StageResearchingProps

### Community 19 - "Community 19"
Cohesion: 0.67
Nodes (3): AgentLogsPanel(), AgentLogsPanelProps, getAgentIcon()

## Knowledge Gaps
- **100 isolated node(s):** `config`, `nextConfig`, `config`, `spaceGrotesk`, `ibmPlexMono` (+95 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `OpenRouterEmbeddings` connect `Community 2` to `Community 1`, `Community 12`?**
  _High betweenness centrality (0.036) - this node is a cross-community bridge._
- **Why does `ainvoke_llm()` connect `Community 1` to `Community 2`?**
  _High betweenness centrality (0.027) - this node is a cross-community bridge._
- **Why does `chat_with_data()` connect `Community 2` to `Community 1`?**
  _High betweenness centrality (0.014) - this node is a cross-community bridge._
- **Are the 10 inferred relationships involving `OpenRouterEmbeddings` (e.g. with `ResearchStartRequest` and `ResearchResumeRequest`) actually correct?**
  _`OpenRouterEmbeddings` has 10 INFERRED edges - model-reasoned connections that need verification._
- **Are the 10 inferred relationships involving `ainvoke_llm()` (e.g. with `brainstorm_chat()` and `retriever_node()`) actually correct?**
  _`ainvoke_llm()` has 10 INFERRED edges - model-reasoned connections that need verification._
- **What connects `config`, `nextConfig`, `config` to the rest of the system?**
  _100 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.09 - nodes in this community are weakly interconnected._