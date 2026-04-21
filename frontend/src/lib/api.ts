export type EventCallbacks = {
  onStep: (step: string, state: any, threadId: string) => void;
  onThought: (agent: string, token: string) => void;
  onInterrupt: (threadId: string, next: string[]) => void;
  onDone: (threadId: string) => void;
  onError: (error: string) => void;
};

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
  mode: 'light' | 'deep' = 'deep'
) {
  try {
    const response = await fetch('http://127.0.0.1:8000/api/research/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ topic, mode })
    });
    await handleSSEResponse(response, callbacks);
  } catch (error: any) {
    callbacks.onError(error.message);
  }
}

export async function resumeResearch(
  threadId: string,
  action: 'answer' | 'approve',
  data: any,
  callbacks: EventCallbacks
) {
  try {
    const response = await fetch('http://127.0.0.1:8000/api/research/resume', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ thread_id: threadId, action, data })
    });
    await handleSSEResponse(response, callbacks);
  } catch (error: any) {
    callbacks.onError(error.message);
  }
}
