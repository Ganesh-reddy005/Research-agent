# Lume.ai - Autonomous Research Production System

**Lume.ai** is a professional-grade, multi-agent AI research platform designed for high-fidelity scholarly discovery. Built with **LangGraph**, **FastAPI**, and **Next.js**, it transforms complex research inquiries into structured, academic-quality manuscripts through a coordinated swarm of specialized agents.

![Lume.ai Banner](https://images.unsplash.com/photo-1507413245164-6160d8298b31?q=80&w=2070&auto=format&fit=crop)

## ✨ The Vision
To provide a distraction-free scholarly workbench that combines the aggressive technical edge of modern AI with the clarity and precision of traditional academic research. Lume.ai follows the **Mistral-inspired "Sharp & Professional"** design language.

## 🚀 Key Features

- **Multi-Agent Orchestration**: A persistent state-machine powered by LangGraph that manages a workflow of Planner, Retriever, Indexer, Synthesis, Writer, and Critic agents.
- **Deep Research Mode**: Exhaustive investigation across 50+ sources including **ArXiv**, **OpenAlex**, and the web (via Tavily).
- **Private Library (Sovereign Data)**: Upload PDFs to your personal library. Lume.ai indexes them into a private Qdrant collection for semantic Q&A and research context.
- **"Live Lab" Experience**: Real-time Server-Sent Events (SSE) stream "thinking" tokens and drafted sections as they are generated.
- **Persistent Memory**: Full session persistence using Postgres checkpointing, allowing you to resume research threads at any time.
- **Academic Precision**: Specialized agents for writing and refining manuscripts with strict adherence to academic standards and citation styles.

## 🎨 Lume.ai Design System

Lume.ai features a unique visual identity:
- **Palette**: Mistral Beige (`#F5F2ED`), Midnight Black (`#000000`), and Mistral Orange (`#FF511C`).
- **Typography**: Authority meets clarity with `EB Garamond` (Serif) for headlines and `Inter` (Sans) for interface.
- **Aesthetics**: Sharp boundaries, zero-radius corners, and high-density layouts for a "scholarly workbench" feel.

## 🛠️ Tech Stack

### Backend (Intelligence)
- **Framework**: FastAPI (Async)
- **Orchestration**: LangGraph (Stateful Multi-Agent Workflows)
- **Persistence**: Postgres (Checkpointing) & Supabase (Auth/Session management)
- **Vector DB**: Qdrant (Semantic Search & Library Indexing)
- **Providers**: OpenRouter (Gemini 2.0 Pro / Llama 3), Groq (High-speed inference)

### Frontend (Interface)
- **Framework**: Next.js 14 (App Router, TypeScript)
- **State Management**: React Hooks + SSE
- **Styling**: Tailwind CSS (Lume Design Tokens)
- **Animations**: Framer Motion

## 📂 Architecture

```text
├── backend/
│   ├── agents/          # Planner, Retriever, Indexer, Synthesis, Writer, Critic, etc.
│   ├── api/             # FastAPI Endpoints & SSE Event Generators
│   ├── graph/           # LangGraph State Workflow Definitions
│   ├── utils/           # LLM Providers, Auth, and Ingestion Logic
│   └── requirements.txt
├── frontend/
│   ├── src/app/         # Dashboard & Landing Page
│   ├── src/components/  # Modular UI (AgentLogs, ReportViewer, Library)
│   ├── src/lib/         # Supabase Client & API Service
│   └── tailwind.config.ts
```

### Agent Workflow
```mermaid
graph TD
    START((START)) --> Clarification[Clarification Node]
    Clarification --> Planning[Planning Node]
    Planning --> Retriever[Retriever Node]
    Retriever --> Indexer[Indexer Node]
    Indexer --> Assistance[Assistance Node]
    Assistance --> Synthesis[Synthesis Node]
    Synthesis --> Writer[Writer Node]
    Writer --> Critic[Critic Node]
    Critic --> Refinement[Refinement Node]
    Refinement --> END((END))
```

## ⚙️ Setup & Installation

### 1. Prerequisites
- Python 3.10+ & Node.js 18+
- [Supabase Project](https://supabase.com/) (Auth & Postgres)
- [Qdrant Instance](https://qdrant.tech/) (Local or Cloud)
- API Keys: OpenRouter, Tavily, OpenAlex

### 2. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` in `backend/`:
```env
# API Keys
OPENROUTER_API_KEY=your_key
TAVILY_API_KEY=your_key
OPENALEX_API_KEY=your_key

# Database & Auth
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres
SUPABASE_URL=https://[PROJECT].supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_key

# Vector DB
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your_optional_key
```

### 3. Frontend Setup
```bash
cd frontend
npm install
```

Create a `.env.local` in `frontend/`:
```env
NEXT_PUBLIC_SUPABASE_URL=https://[PROJECT].supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_key
```

Run the development server:
```bash
npm run dev
```

## 📜 License
MIT License. Developed for high-impact autonomous research.
