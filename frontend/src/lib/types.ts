// Shapes of the research state streamed from / returned by the backend.

export type ClarificationQuestion = { id: string; question: string };

export type PlanSection = { title: string; description: string; questions?: string[] };

export type ResearchPlan = {
  objective?: string;
  sections: PlanSection[];
  expected_outcome?: string;
};

export type Source = {
  title: string;
  url: string;
  summary?: string;
  source: string;
  year?: number | null;
  authors?: string[];
};

/** What Lume understood about the repository a project paper is about. */
export type ProjectProfile = {
  name: string;           // owner/repo
  url: string;
  branch?: string;
  commit?: string;
  title?: string;
  summary?: string;
  problem?: string;
  approach?: string;
  architecture?: { component: string; role: string; files?: string[] }[];
  tech_stack?: string[];
  key_algorithms?: string[];
  data?: string[];
  evaluation?: string;
  limitations?: string[];
  stats?: { files: number; lines: number; languages: Record<string, number> };
};

/** A new research session: a topic, or a repository whose project the paper writes up. */
export type StartResearchRequest = {
  topic: string;          // the question, or notes about the project when repo_url is set
  mode: ResearchDepth;
  repo_url?: string;
  pages?: number;         // paper length in IEEE pages; omit to let Lume choose
};

/** One search the planner chose: what a section needs and where it was looked for. */
export type SearchNeed = {
  id: number;
  section: string;
  need: string;
  kind: 'papers' | 'web' | 'none';  // none: covered by the project or the paper's own argument
  query: string;
  retry_query?: string;             // rewritten once because the first query found too little
  sources: number;                  // relevant sources kept
};

/** What the coding agent is asked to do, drafted by Lume and approved by the user before anything runs. */
export type ExperimentBrief = {
  objective: string;
  target: string;               // the code or system to experiment on
  metric: { name: string; goal: 'maximize' | 'minimize'; measured_by: string };
  baseline: string;             // what results are compared with
  must_hold: string[];          // checks every attempt must still pass
  off_limits: string[];         // what the agent must not change
  open_questions: string[];     // for the user to answer before the agent starts
  notes: string[];              // the user's answers and anything else the agent should know
  attempt_limit: number;        // safety net; the user decides after every attempt
};

/** How every attempt is graded: fixed when the user approves the plan. */
export type BenchmarkSpec = {
  build: string;
  checks: Record<string, string>;  // name -> command that must exit 0
  measure: string;
  read: string;                    // "time", "json:<key>" or "regex:<pattern>"
  repeats: number;
  warmup: number;
  timeout: number;
  protected: string[];             // files no attempt may change
};

export type Hypothesis = {
  id: number;
  idea: string;
  why?: string;
  expected_gain?: string;
  cost?: string;
  files?: string[];
  status: 'pending' | 'done';
  attempt?: number;
};

/** One entry of the lab notebook. */
export type Attempt = {
  n: number;
  hypothesis: string;
  change?: string;
  checks: Record<string, boolean>;
  metric: number | null;
  spread: number;
  verdict: 'baseline' | 'improved' | 'no gain' | 'worse' | 'failed checks' | 'crashed';
  lesson?: string;
  cost_usd?: number;
  files?: string[];
  stage?: string;
  error?: string;
  log?: string;
};

export type ExperimentReport = {
  findings?: string;
  lesson?: string;
  next?: string;
  recommend?: string;
  attempt?: number;
  attempts_left: number;
  pending: string[];
};

/** The coding agent's working state. */
export type Lab = {
  ready: boolean;          // dependencies installed and the baseline measured
  env?: { summary?: string; build_system?: string; key_files?: string[]; risks?: string[]; questions?: string[] };
  setup: string[];
  spec: BenchmarkSpec;
  hypotheses: Hypothesis[];
  plan_notes?: string;
  error?: string;
  report?: ExperimentReport;
  cost_usd?: number;
  tokens?: number;
};

export type ExperimentDecision = 'continue' | 'change plan' | 'stop';

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
  synthesis_report?: string;
  draft_report?: string;
  critic_feedback?: string;
  final_report?: string;
  citation_audit_log?: CitationAudit;
  current_step?: string;
  indexed_count?: number;
  repo_url?: string;
  project_profile?: ProjectProfile;
  target_pages?: number;
  search_plan?: SearchNeed[];
  experiment_brief?: ExperimentBrief;
  lab?: Lab;
  notebook?: Attempt[];
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

export type SearchSource = { n: number; title: string; url: string; source: string; year?: number | null };

/** One live search the brainstorm agent ran: web_search, search_arxiv or search_openalex. */
export type SearchStep = {
  id: string;
  tool: string;
  query: string;
  status: 'searching' | 'done';
  sources: SearchSource[];
};

export type ChatMessage = {
  role: 'user' | 'assistant';
  content: string;
  searches?: SearchStep[];     // brainstorm: live web/arXiv/OpenAlex searches
  sources?: SearchSource[];    // source chat: passages the answer cites
  searchQuery?: string;        // source chat: the query actually searched
};

export type ActivityLog = { step: string; time: string; data: ResearchState };

/** What the running research agent is doing right now. */
export type LiveActivity = { agent: string; startedAt: number; message?: string; text: string };
