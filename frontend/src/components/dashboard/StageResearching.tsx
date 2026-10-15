"use client";

import React, { useEffect, useState } from 'react';
import { Check, Loader2, Square } from 'lucide-react';
import type { ActivityLog, LiveActivity } from '@/lib/types';
import { Button, StageHeader } from './ui';
import { agentLabel, agentHints, describeStep } from './agents';

const STEP_TITLES = [
  { title: 'Preparing your questions', description: 'Lume is working out what it needs to know about your topic.' },
  { title: 'Drafting a research plan', description: 'Turning your answers into a plan you can review and edit.' },
  { title: 'Gathering sources', description: 'Searching arXiv, OpenAlex, CORE, the web and your library, then reading what it finds.' },
  { title: 'Gathering sources', description: 'Searching arXiv, OpenAlex, CORE, the web and your library, then reading what it finds.' },
  { title: 'Writing your paper', description: 'Writing each section, reviewing the draft and checking the citations. This takes a few minutes.' },
];

function formatElapsed(ms: number) {
  const s = Math.max(0, Math.floor(ms / 1000));
  return s < 60 ? `${s}s` : `${Math.floor(s / 60)}m ${String(s % 60).padStart(2, '0')}s`;
}

/** Re-renders every second while mounted. */
function useNow() {
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);
  return now;
}

export default function StageResearching({ step, live, logs, onStop }: {
  step: number;
  live: LiveActivity | null;
  logs: ActivityLog[];
  onStop: () => void;
}) {
  const now = useNow();
  const { title, description } = STEP_TITLES[step] ?? STEP_TITLES[0];

  // While an agent is busy without output, cycle through what it is doing
  const hints = live ? agentHints(live.agent) : ['Connecting to the research agents…'];
  const hint = hints[Math.floor((now - (live?.startedAt ?? now)) / 4000) % hints.length];
  const stream = live?.text.slice(-700) ?? '';

  return (
    <div className="space-y-8">
      <StageHeader title={title} description={description} />

      <section aria-live="polite" className="border border-mistral-black/10 bg-mistral-beige/40 p-5 sm:p-6 space-y-3">
        <div className="flex items-center gap-2.5">
          <Loader2 className="w-4 h-4 text-mistral-orange animate-spin shrink-0" aria-hidden />
          <span className="text-sm font-semibold text-mistral-black">{live ? agentLabel(live.agent) : 'Starting up'}</span>
          {live && <span className="text-xs text-mistral-black/60 tabular-nums">{formatElapsed(now - live.startedAt)}</span>}
          <Button variant="secondary" onClick={onStop} className="!px-3 !py-1.5 ml-auto">
            <Square className="w-3 h-3 fill-current" aria-hidden /> Stop
          </Button>
        </div>
        <p className="text-sm text-mistral-black/75">{live?.message || hint}</p>
        {stream && (
          <p className="text-sm text-mistral-black/70 leading-relaxed whitespace-pre-wrap break-words max-h-64 overflow-hidden border-t border-mistral-black/10 pt-3">
            {stream.length < (live?.text.length ?? 0) && '…'}
            {stream}
          </p>
        )}
      </section>

      {logs.length > 0 && (
        <section className="space-y-3">
          <h2 className="text-sm font-semibold text-mistral-black/70">Completed so far</h2>
          <ul className="divide-y divide-mistral-black/10 border-y border-mistral-black/10">
            {logs.map((log, i) => (
              <li key={i} className="flex items-center gap-3 py-3 text-sm">
                <Check className="w-4 h-4 text-mistral-orange shrink-0" aria-hidden />
                <span className="font-medium text-mistral-black">{agentLabel(log.step)}</span>
                <span className="text-mistral-black/60">· {describeStep(log.step, log.data)}</span>
                <span className="ml-auto text-xs text-mistral-black/55 tabular-nums">{log.time}</span>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
