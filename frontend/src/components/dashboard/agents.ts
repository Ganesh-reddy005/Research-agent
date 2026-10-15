import type { ResearchState } from '@/lib/types';

/** The five steps a research project moves through, shown in the progress bar. */
export const STEPS = ['Questions', 'Plan', 'Sources', 'Review', 'Paper'] as const;

const AGENTS: Record<string, { label: string; step: number }> = {
  clarification: { label: 'Preparing questions', step: 0 },
  planning: { label: 'Drafting the research plan', step: 1 },
  retriever: { label: 'Searching for sources', step: 2 },
  indexer: { label: 'Reading and indexing sources', step: 2 },
  assistance: { label: 'Summarising what was found', step: 2 },
  synthesis: { label: 'Connecting the findings', step: 4 },
  writer: { label: 'Writing the paper', step: 4 },
  critic: { label: 'Reviewing the draft', step: 4 },
  refinement: { label: 'Editing the final version', step: 4 },
  auditor: { label: 'Checking citations', step: 4 },
};

export const agentLabel = (agent: string) => AGENTS[agent.toLowerCase()]?.label ?? 'Working';

// Shown in rotation while an agent works without visible output
const HINTS: Record<string, string[]> = {
  clarification: ['Reading your topic…', 'Working out what is ambiguous…', 'Drafting clarifying questions…'],
  planning: ['Turning your answers into a brief…', 'Outlining the sections of the paper…', 'Choosing the questions each section must answer…'],
  retriever: ['Writing search queries…', 'Searching arXiv, OpenAlex, CORE and the web…', 'Collecting and de-duplicating results…'],
  indexer: ['Downloading the full text of the top sources…', 'Splitting papers into passages…', 'Indexing passages so they can be cited…'],
  assistance: ['Summarising what was found…'],
  synthesis: ['Finding themes across the sources…', 'Looking for disagreements and open gaps…'],
  writer: ['Writing the paper section by section…', 'Matching claims to their sources…'],
  critic: ['Reviewing the draft like a peer reviewer…', 'Looking for weak arguments and missing evidence…'],
  refinement: ['Editing the final version…', 'Tightening the wording…', 'Formatting the paper…'],
  auditor: ['Checking every citation against the sources…'],
};

export const agentHints = (agent: string) => HINTS[agent.toLowerCase()] ?? ['Working…'];

export const agentStep = (agent: string): number | undefined => AGENTS[agent.toLowerCase()]?.step;

/** One-line, human-readable result of a finished step. */
export function describeStep(step: string, data: ResearchState & { indexed_count?: number }): string {
  switch (step) {
    case 'clarification':
      return `${data.clarification_questions?.length ?? 0} questions ready`;
    case 'planning':
      return `Plan with ${data.research_plan?.sections.length ?? 0} sections`;
    case 'retriever':
      return `Found ${data.raw_sources?.length ?? 0} sources`;
    case 'indexer':
      return data.indexed_count ? `Indexed ${data.indexed_count} passages` : 'Indexing finished';
    case 'assistance':
      return 'Summary ready';
    case 'auditor': {
      const audit = data.citation_audit_log;
      return audit ? `Checked ${audit.total_citations_found} citations` : 'Citations checked';
    }
    default:
      return 'Done';
  }
}
