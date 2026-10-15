"use client";

import React, { useEffect, useRef, useState } from 'react';
import { X, ChevronDown } from 'lucide-react';
import type { ActivityLog } from '@/lib/types';
import AgentIcon from './AgentIcon';
import { agentLabel, describeStep } from './agents';

export default function AgentLogsPanel({ logs, activeThought, isProcessing, onClose }: {
  logs: ActivityLog[];
  activeThought: { agent: string; text: string } | null;
  isProcessing: boolean;
  onClose: () => void;
}) {
  const [expanded, setExpanded] = useState<number | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [logs, activeThought]);

  return (
    <aside className="h-full bg-white border-l border-mistral-black/10 flex flex-col" aria-label="Activity">
      <div className="h-14 px-5 flex items-center justify-between border-b border-mistral-black/10 shrink-0">
        <div>
          <h2 className="text-base font-semibold text-mistral-black">Activity</h2>
          <p className="text-xs text-mistral-black/60">{isProcessing ? 'Lume is working…' : 'Every step the agents have taken'}</p>
        </div>
        <button onClick={onClose} className="p-2 text-mistral-black/60 hover:text-mistral-black" aria-label="Close activity">
          <X className="w-4 h-4" />
        </button>
      </div>

      <div ref={scrollRef} className="flex-1 overflow-y-auto custom-scrollbar p-4 space-y-2">
        {logs.length === 0 && !activeThought && (
          <p className="text-sm text-mistral-black/60 leading-relaxed p-2">
            Nothing yet. Steps appear here as soon as a research project starts.
          </p>
        )}

        {logs.map((log, i) => (
          <div key={i} className="border border-mistral-black/10">
            <button
              onClick={() => setExpanded(expanded === i ? null : i)}
              aria-expanded={expanded === i}
              className="w-full text-left p-3 flex items-start gap-3 hover:bg-mistral-beige/40 transition-colors"
            >
              <AgentIcon name={log.step} className="w-4 h-4 mt-0.5 text-mistral-black/60 shrink-0" />
              <span className="flex-1 min-w-0">
                <span className="block text-sm font-medium text-mistral-black">{agentLabel(log.step)}</span>
                <span className="block text-sm text-mistral-black/65">{describeStep(log.step, log.data)}</span>
              </span>
              <span className="text-xs text-mistral-black/55 tabular-nums shrink-0">{log.time}</span>
              <ChevronDown className={`w-4 h-4 text-mistral-black/50 shrink-0 transition-transform ${expanded === i ? 'rotate-180' : ''}`} aria-hidden />
            </button>
            {expanded === i && (
              <pre className="px-3 pb-3 text-xs text-mistral-black/70 whitespace-pre-wrap break-words font-mono leading-relaxed max-h-64 overflow-y-auto">
                {JSON.stringify(log.data, null, 2)}
              </pre>
            )}
          </div>
        ))}

        {activeThought && (
          <div className="border border-mistral-orange/40 bg-mistral-beige/30 p-3 space-y-2">
            <div className="flex items-center gap-2 text-sm font-medium text-mistral-black">
              <AgentIcon name={activeThought.agent} className="w-4 h-4 text-mistral-orange" />
              {agentLabel(activeThought.agent)}…
            </div>
            <p className="text-sm text-mistral-black/70 leading-relaxed break-words whitespace-pre-wrap">
              {activeThought.text.slice(-500)}
            </p>
          </div>
        )}
      </div>
    </aside>
  );
}
