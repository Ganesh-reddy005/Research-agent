export type AgentStateInfo = {
  step: 'planner' | 'retriever' | 'writer' | 'critic';
  state: any;
};

export async function submitResearchQuery(
  query: string, 
  onEvent: (event: string, data: any) => void,
  onDone: () => void,
  onError: (error: string) => void
) {
  try {
    const response = await fetch('http://127.0.0.1:8000/api/research', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query })
    });
    
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
              onDone();
            } else if (currentEvent === 'error') {
              onError(data.error);
            } else {
              onEvent(currentEvent, data);
            }
          } catch (e) {
            console.error('Failed to parse SSE data', e);
          }
        }
      }
    }
  } catch (error: any) {
    onError(error.message);
  }
}
