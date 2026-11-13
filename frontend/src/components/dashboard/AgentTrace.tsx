import React from 'react';
import type { TraceStep } from '@/lib/types';

/** A phase's tool calls, collapsed: what the agent looked at and what each call returned. */
export default function AgentTrace({ title, trace }: { title: string; trace?: TraceStep[] }) {
  if (!trace?.length) return null;
  return (
    <details className="border border-mistral-black/10 bg-white">
      <summary className="px-4 py-3 cursor-pointer text-sm font-semibold text-mistral-black/80">
        {title} ({trace.length} tool call{trace.length === 1 ? '' : 's'})
      </summary>
      <ol className="px-4 pb-4 space-y-2 text-xs font-mono text-mistral-black/80 max-h-80 overflow-y-auto">
        {trace.map((step, i) => (
          <li key={i} className="break-words">
            <span className="text-mistral-orange">{i + 1}. {step.tool}</span>({step.args})
            {step.result && <span className="block text-mistral-black/60">→ {step.result}</span>}
          </li>
        ))}
      </ol>
    </details>
  );
}
