// Shapes of the research state streamed from / returned by the backend.

export type ClarificationQuestion = { id: string; question: string };

export type PlanSection = { title: string; description: string; questions?: string[] };

export type ResearchPlan = {
  objective?: string;
  sections: PlanSection[];
  expected_outcome?: string;
};

export type Source = { title: string; url: string; summary?: string; source: string };

export type CitationAudit = {
  total_citations_found: number;
  unique_sources_cited: number;
  invalid_citations: number[];
};

export type ResearchState = {
  topic?: string;
  research_mode?: ResearchDepth;
  clarification_questions?: ClarificationQuestion[];
  user_answers?: Record<string, string>;
  research_brief?: string;
  research_plan?: ResearchPlan;
  raw_sources?: Source[];
  assistance_summary?: string;
  draft_report?: string;
  final_report?: string;
  citation_audit_log?: CitationAudit;
  current_step?: string;
};

export type ResearchDepth = 'light' | 'deep';

export type SessionSnapshot = { thread_id: string; next: string[]; state: ResearchState };

export type SessionSummary = {
  thread_id: string;
  topic: string;
  status: string;
  research_mode: string; // 'light' | 'deep' | 'brainstorm'
  created_at: string;
};

export type LibraryDocument = { id: string; filename: string; uploaded_at: string };

export type ChatMessage = { role: 'user' | 'assistant'; content: string };

export type ActivityLog = { step: string; time: string; data: ResearchState };
