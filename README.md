# Multi-Agent Research Paper Assistant

A production-ready Multi-Agent Research system built with **LangGraph**, **FastAPI**, and **Next.js**. It generates structured, IEEE-style research reports by leveraging real-time data from the web and academic sources.

## 🚀 Features

- **Multi-Agent Workflow**: Sequential pipeline using LangGraph (Planner → Retriever → Writer → Critic).
- **Dual Retrieval**: Combines real-time web search (Tavily) with academic paper fetching (arXiv).
- **Professional Reports**: Generates structured IEEE-style reports with inline citations.
- **Real-time Updates**: Live agent-level progress streaming via Server-Sent Events (SSE).
- **Resilient LLM Integration**: Primary support for OpenRouter with automatic fallback to Groq.
- **Exportable Results**: Download reports as PDFs directly from the browser.

## 🛠️ Tech Stack

### Backend
- **Framework**: LangGraph (LangChain ecosystem)
- **API**: FastAPI
- **LLMs**: OpenRouter (Primary), Groq (Fallback)
- **Retrieval**: Tavily API, arXiv API
- **Concurrency**: Parallel search query execution

### Frontend
- **Framework**: Next.js 14+ (TypeScript)
- **Styling**: Tailwind CSS
- **Animations**: Framer Motion
- **Icons**: Lucide React
- **Report Rendering**: React Markdown + HTML2PDF

## 📂 Project Structure

```text
├── backend/
│   ├── agents/          # Individual agent nodes (Planner, Retriever, Writer, Critic)
│   ├── api/             # FastAPI routes and SSE implementation
│   ├── graph/           # LangGraph workflow definition
│   ├── utils/           # LLM initialization and helper functions
│   └── .env             # Environment variables
├── frontend/
│   ├── src/app/         # Next.js app router pages
│   ├── src/components/  # UI components (Agent steps, Report viewer)
│   └── src/lib/         # API client and utilities
└── details.md           # Original project requirements
```

## ⚙️ Setup Instructions

### 1. Prerequisites
- Python 3.9+
- Node.js 18+
- [Tavily API Key](https://tavily.com/)
- [Groq API Key](https://wow.groq.com/)
- [OpenRouter API Key](https://openrouter.ai/) (Optional, but recommended)

### 2. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in the `backend/` directory:
```env
OPENROUTER_API_KEY=your_openrouter_key
GROQ_API_KEY=your_groq_key
TAVILY_API_KEY=your_tavily_key
```

Run the backend:
```bash
uvicorn api.main:app --reload
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:3000` in your browser.

## 🤖 How it Works

1. **Planner Agent**: Breaks down the research query into 10-15 targeted search terms.
2. **Retriever Agent**: Executes searches in parallel across Tavily and arXiv, collecting up to 15 unique sources.
3. **Writer Agent**: Processes the collected data to write an IEEE-style report with citations.
4. **Critic Agent**: Reviews the draft for coherence, structure, and academic tone to produce the final version.

## 📝 License

MIT
