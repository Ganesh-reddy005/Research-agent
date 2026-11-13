import { supabase } from './supabaseClient';
import type {
  BenchmarkSpec, ChatMessage, ExperimentBrief, ExperimentDecision, Hypothesis, LibraryDocument, ResearchDepth, ResearchPlan, ResearchState, SearchSource, SessionSnapshot, SessionSummary,
  StartResearchRequest,
} from './types';

export type EventCallbacks = {
  onStep: (step: string, state: ResearchState, threadId: string) => void;
  onThought: (agent: string, token: string) => void;
  onInterrupt: (threadId: string, next: string[], step?: string, question?: string) => void;  // step: the agent that paused
  onDone: (threadId: string) => void;
  onError: (error: string) => void;
  onAgentStart?: (agent: string, threadId: string) => void;
  onProgress?: (agent: string, message: string) => void;
  onSearchStart?: (search: { id: string; tool: string; query: string }) => void;
  onSearchEnd?: (search: { id: string; tool: string; query: string; sources: SearchSource[] }) => void;
};

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

const message = (error: unknown) => (error instanceof Error ? error.message : String(error));

// The user pressed Stop: not an error worth showing
const isAbort = (error: unknown) => error instanceof DOMException && error.name === 'AbortError';

async function getAuthHeaders() {
  const { data: { session } } = await supabase.auth.getSession();
  return {
    'Authorization': `Bearer ${session?.access_token}`,
    'Content-Type': 'application/json'
  };
}

async function errorDetail(response: Response, fallback: string) {
  const body = await response.json().catch(() => ({}));
  return body.detail || fallback;
}

async function handleSSEResponse(
  response: Response,
  callbacks: EventCallbacks
) {
  if (!response.body) throw new Error("No body in response");

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let currentEvent = 'message';

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (line.trim() === '') continue;
      if (line.startsWith('event:')) {
        currentEvent = line.slice(6).trim();
      } else if (line.startsWith('data:')) {
        const dataStr = line.slice(5).trim();
        try {
          const data = JSON.parse(dataStr);
          if (currentEvent === 'done') {
            callbacks.onDone(data.thread_id);
          } else if (currentEvent === 'error') {
            callbacks.onError(data.error);
          } else if (currentEvent === 'interrupt') {
            callbacks.onInterrupt(data.thread_id, data.next, data.step, data.question);
          } else if (currentEvent === 'step') {
            callbacks.onStep(data.step, data.state, data.thread_id);
          } else if (currentEvent === 'thought') {
            callbacks.onThought(data.agent, data.token);
          } else if (currentEvent === 'agent_start') {
            callbacks.onAgentStart?.(data.agent, data.thread_id);
          } else if (currentEvent === 'progress') {
            callbacks.onProgress?.(data.agent, data.message);
          } else if (currentEvent === 'search_start') {
            callbacks.onSearchStart?.(data);
          } else if (currentEvent === 'search_end') {
            callbacks.onSearchEnd?.(data);
          }
        } catch (e) {
          console.error('Failed to parse SSE data', e);
        }
      }
    }
  }
}

export async function startResearch(
  request: StartResearchRequest,
  callbacks: EventCallbacks,
  signal?: AbortSignal
) {
  try {
    const headers = await getAuthHeaders();
    const response = await fetch(`${BASE_URL}/api/research/start`, {
      method: 'POST',
      headers,
      body: JSON.stringify(request),
      signal
    });
    if (!response.ok) throw new Error(await errorDetail(response, "Failed to start research"));
    await handleSSEResponse(response, callbacks);
  } catch (error) {
    if (!isAbort(error)) callbacks.onError(message(error));
  }
}

export type ResumeData =
  | { answers: Record<string, string> }
  | { mode: ResearchDepth; plan: ResearchPlan }
  | { hypotheses: Hypothesis[]; setup?: string[]; spec?: BenchmarkSpec }
  | { decision: ExperimentDecision; direction?: string }
  | { url: string } | { scratch: true }
  | { answer: string }
  | Record<string, never>;

export async function resumeResearch(
  threadId: string,
  action: 'answer' | 'approve' | 'continue' | 'plan_experiments'
    | 'launch_experiments' | 'choose_start' | 'approve_experiment_plan' | 'experiment_decision' | 'retry_plan' | 'answer_question',
  data: ResumeData,
  callbacks: EventCallbacks,
  signal?: AbortSignal
) {
  try {
    const headers = await getAuthHeaders();
    const response = await fetch(`${BASE_URL}/api/research/resume`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ thread_id: threadId, action, data }),
      signal
    });
    if (!response.ok) throw new Error(await errorDetail(response, "Failed to resume research"));
    await handleSSEResponse(response, callbacks);
  } catch (error) {
    if (!isAbort(error)) callbacks.onError(message(error));
  }
}

/** Save edits to the experiment brief; returns it as stored and what is still missing before launch. */
export async function saveExperimentBrief(
  threadId: string,
  brief: ExperimentBrief
): Promise<{ brief: ExperimentBrief; missing: string[] }> {
  const headers = await getAuthHeaders();
  const response = await fetch(`${BASE_URL}/api/research/${threadId}/brief`, {
    method: 'PUT', headers, body: JSON.stringify({ brief }),
  });
  if (!response.ok) throw new Error(await errorDetail(response, 'Could not save the experiment brief'));
  return response.json();
}

/** Download the experiment's code (zip with LUME_RUN.md) as a file. */
export async function downloadExperimentCode(threadId: string) {
  const headers = await getAuthHeaders();
  const response = await fetch(`${BASE_URL}/api/research/${threadId}/code`, { headers });
  if (!response.ok) throw new Error(await errorDetail(response, 'Could not download the code'));
  const name = /filename="([^"]+)"/.exec(response.headers.get('Content-Disposition') ?? '')?.[1] ?? 'experiment.zip';
  const link = document.createElement('a');
  link.href = URL.createObjectURL(await response.blob());
  link.download = name;
  link.click();
  URL.revokeObjectURL(link.href);
}

export async function getResearchSession(threadId: string): Promise<SessionSnapshot> {
  const headers = await getAuthHeaders();
  const response = await fetch(`${BASE_URL}/api/research/${threadId}`, { headers });
  if (!response.ok) throw new Error(await errorDetail(response, 'Could not load this research session'));
  return response.json();
}

export async function getBrainstorm(chatId: string): Promise<{ chat_id: string; messages: ChatMessage[] }> {
  const headers = await getAuthHeaders();
  const response = await fetch(`${BASE_URL}/api/research/brainstorm/${chatId}`, { headers });
  if (!response.ok) throw new Error(await errorDetail(response, 'Could not load this conversation'));
  return response.json();
}

/** Ask about a session's sources. `history` is the earlier conversation, oldest first. */
export async function chatWithData(
  threadId: string,
  query: string,
  history: { role: string; content: string }[] = []
): Promise<{ answer: string; sources: SearchSource[]; search_query: string }> {
  const headers = await getAuthHeaders();
  const response = await fetch(`${BASE_URL}/api/research/chat`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ thread_id: threadId, query, history })
  });
  if (!response.ok) throw new Error(await errorDetail(response, 'Failed to fetch chat response'));
  return response.json();
}

export async function uploadDocument(file: File) {
  const { data: { session } } = await supabase.auth.getSession();
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${BASE_URL}/api/library/upload`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${session?.access_token}`,
    },
    body: formData
  });

  if (!response.ok) throw new Error(await errorDetail(response, 'Upload failed'));
  return response.json();
}

export async function getLibrary(): Promise<LibraryDocument[]> {
  const headers = await getAuthHeaders();
  const response = await fetch(`${BASE_URL}/api/library`, { headers });
  if (!response.ok) throw new Error('Failed to fetch library');
  return response.json();
}

export async function getSessions(): Promise<SessionSummary[]> {
  const headers = await getAuthHeaders();
  const response = await fetch(`${BASE_URL}/api/sessions`, { headers });
  if (!response.ok) throw new Error('Failed to fetch sessions');
  return response.json();
}

/** Delete a research project or brainstorm and everything stored for it. */
export async function deleteSession(threadId: string) {
  const headers = await getAuthHeaders();
  const response = await fetch(`${BASE_URL}/api/sessions/${threadId}`, { method: 'DELETE', headers });
  if (!response.ok) throw new Error(await errorDetail(response, 'Could not delete this item'));
}

/** Send one message; the server keeps the conversation. Omit chatId to start a new one. */
export async function brainstormResearch(
  text: string,
  chatId: string | null,
  callbacks: EventCallbacks,
  signal?: AbortSignal
) {
  try {
    const headers = await getAuthHeaders();
    const response = await fetch(`${BASE_URL}/api/research/brainstorm`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ message: text, chat_id: chatId }),
      signal
    });
    if (!response.ok) throw new Error(await errorDetail(response, 'Brainstorming failed'));
    await handleSSEResponse(response, callbacks);
  } catch (error) {
    if (!isAbort(error)) callbacks.onError(message(error));
  }
}
