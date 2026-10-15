"use client";

import React, { useEffect, useRef, useState } from 'react';
import { X, ChevronDown } from 'lucide-react';
import type { ActivityLog, LiveActivity, ResearchState } from '@/lib/types';
import AgentIcon from './AgentIcon';
import { agentLabel, describeStep } from './agents';

const words = (text?: string) => (text ? text.trim().split(/\s+/).length : 0);

function Text({ children }: { children?: string }) {
  return <p className="text-sm text-mistral-black/75 leading-relaxed whitespace-pre-line">{children}</p>;
}

/** Human-readable details of what a finished step produced. */
function StepDetails({ step, data }: { step: string; data: ResearchState }) {
  switch (step) {
    case 'clarification':
      return (
        <ol className="space-y-2 list-decimal pl-5 text-sm text-mistral-black/75 leading-relaxed">
          {data.clarification_questions?.map(q => <li key={q.id}>{q.question}</li>)}
        </ol>
      );
    case 'planning':
      return (
        <div className="space-y-2">
          {data.research_plan?.objective && <Text>{data.research_plan.objective}</Text>}
          <ol className="space-y-1 list-decimal pl-5 text-sm text-mistral-black/75">
            {data.research_plan?.sections.map((s, i) => <li key={i}>{s.title}</li>)}
          </ol>
        </div>
      );
    case 'retriever':
      return (
        <ul className="space-y-1.5 text-sm">
          {data.raw_sources?.slice(0, 12).map((s, i) => (
            <li key={i} className="text-mistral-black/75 leading-snug">
              {s.title} <span className="text-mistral-black/55">· {s.source}{s.year ? `, ${s.year}` : ''}</span>
            </li>
          ))}
          {(data.raw_sources?.length ?? 0) > 12 && (
            <li className="text-mistral-black/55">and {data.raw_sources!.length - 12} more</li>
          )}
        </ul>
      );
    case 'assistance':
      return <Text>{data.assistance_summary}</Text>;
    case 'synthesis':
      return <Text>{data.synthesis_report}</Text>;
    case 'writer':
      return <Text>{`First draft written: ${words(data.draft_report)} words.`}</Text>;
    case 'critic':
      return <Text>{data.critic_feedback}</Text>;
    case 'refinement':
      return <Text>{`Final version: ${words(data.final_report)} words.`}</Text>;
    case 'auditor': {
      const a = data.citation_audit_log;
      if (!a) return null;
      return (
        <Text>
          {`${a.total_citations_found} citations to ${a.unique_sources_cited} sources.` +
            (a.invalid_citations?.length ? ` Not matching any source: ${a.invalid_citations.map(n => `[${n}]`).join(', ')}.` : ' All match retrieved sources.')}
        </Text>
      );
    }
    default:
      return null;
  }
}

const HAS_DETAILS = new Set(['clarification', 'planning', 'retriever', 'assistance', 'synthesis', 'writer', 'critic', 'refinement', 'auditor']);

export default function AgentLogsPanel({ logs, live, isProcessing, onClose }: {
  logs: ActivityLog[];
  live: LiveActivity | null;
  isProcessing: boolean;
  onClose: () => void;
}) {
  const [expanded, setExpanded] = useState<number | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [logs, live]);

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
        {logs.length === 0 && !live && (
          <p className="text-sm text-mistral-black/60 leading-relaxed p-2">
            Nothing yet. Steps appear here as soon as a research project starts.
          </p>
        )}

        {logs.map((log, i) => {
          const expandable = HAS_DETAILS.has(log.step);
          return (
            <div key={i} className="border border-mistral-black/10">
              <button
                onClick={() => setExpanded(expanded === i ? null : i)}
                disabled={!expandable}
                aria-expanded={expanded === i}
                className="w-full text-left p-3 flex items-start gap-3 enabled:hover:bg-mistral-beige/40 transition-colors"
              >
                <AgentIcon name={log.step} className="w-4 h-4 mt-0.5 text-mistral-black/60 shrink-0" />
                <span className="flex-1 min-w-0">
                  <span className="block text-sm font-medium text-mistral-black">{agentLabel(log.step)}</span>
                  <span className="block text-sm text-mistral-black/65">{describeStep(log.step, log.data)}</span>
                </span>
                <span className="text-xs text-mistral-black/55 tabular-nums shrink-0">{log.time}</span>
                {expandable && (
                  <ChevronDown className={`w-4 h-4 text-mistral-black/50 shrink-0 transition-transform ${expanded === i ? 'rotate-180' : ''}`} aria-hidden />
                )}
              </button>
              {expanded === i && (
                <div className="px-3 pb-3 pl-10 max-h-72 overflow-y-auto custom-scrollbar">
                  <StepDetails step={log.step} data={log.data} />
                </div>
              )}
            </div>
          );
        })}

        {live && (
          <div className="border border-mistral-orange/40 bg-mistral-beige/30 p-3 space-y-2">
            <div className="flex items-center gap-2 text-sm font-medium text-mistral-black">
              <AgentIcon name={live.agent} className="w-4 h-4 text-mistral-orange" />
              {agentLabel(live.agent)}…
            </div>
            {live.message && <p className="text-sm text-mistral-black/75">{live.message}</p>}
            {live.text && (
              <p className="text-sm text-mistral-black/70 leading-relaxed break-words whitespace-pre-wrap">
                {live.text.slice(-500)}
              </p>
            )}
          </div>
        )}
      </div>
    </aside>
  );
}
