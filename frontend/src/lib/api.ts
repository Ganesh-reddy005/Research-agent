import { supabase } from './supabaseClient';
import type {
  ChatMessage, LibraryDocument, ResearchDepth, ResearchPlan, ResearchState, SessionSnapshot, SessionSummary,
} from './types';

export type EventCallbacks = {
  onStep: (step: string, state: ResearchState, threadId: string) => void;
  onThought: (agent: string, token: string) => void;
  onInterrupt: (threadId: string, next: string[]) => void;
  onDone: (threadId: string) => void;
  onError: (error: string) => void;
};

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

const message = (error: unknown) => (error instanceof Error ? error.message : String(error));

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
            callbacks.onInterrupt(data.thread_id, data.next);
          } else if (currentEvent === 'step') {
            callbacks.onStep(data.step, data.state, data.thread_id);
          } else if (currentEvent === 'thought') {
            callbacks.onThought(data.agent, data.token);
          }
        } catch (e) {
          console.error('Failed to parse SSE data', e);
        }
      }
    }
  }
}

export async function startResearch(
  topic: string,
  callbacks: EventCallbacks,
  mode: ResearchDepth = 'deep'
) {
  try {
    const headers = await getAuthHeaders();
    const response = await fetch(`${BASE_URL}/api/research/start`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ topic, mode })
    });
    if (!response.ok) throw new Error(await errorDetail(response, "Failed to start research"));
    await handleSSEResponse(response, callbacks);
  } catch (error) {
    callbacks.onError(message(error));
  }
}

export type ResumeData =
  | { answers: Record<string, string> }
  | { mode: ResearchDepth; plan: ResearchPlan }
  | Record<string, never>;

export async function resumeResearch(
  threadId: string,
  action: 'answer' | 'approve' | 'continue',
  data: ResumeData,
  callbacks: EventCallbacks
) {
  try {
    const headers = await getAuthHeaders();
    const response = await fetch(`${BASE_URL}/api/research/resume`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ thread_id: threadId, action, data })
    });
    if (!response.ok) throw new Error(await errorDetail(response, "Failed to resume research"));
    await handleSSEResponse(response, callbacks);
  } catch (error) {
    callbacks.onError(message(error));
  }
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

export async function chatWithData(
  threadId: string,
  query: string
): Promise<{ answer: string; sources: string[] }> {
  const headers = await getAuthHeaders();
  const response = await fetch(`${BASE_URL}/api/research/chat`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ thread_id: threadId, query })
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

/** Send one message; the server keeps the conversation. Omit chatId to start a new one. */
export async function brainstormResearch(
  text: string,
  chatId: string | null,
  callbacks: EventCallbacks
) {
  try {
    const headers = await getAuthHeaders();
    const response = await fetch(`${BASE_URL}/api/research/brainstorm`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ message: text, chat_id: chatId })
    });
    if (!response.ok) throw new Error(await errorDetail(response, 'Brainstorming failed'));
    await handleSSEResponse(response, callbacks);
  } catch (error) {
    callbacks.onError(message(error));
  }
}
