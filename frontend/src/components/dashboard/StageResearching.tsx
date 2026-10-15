"use client";

import React from 'react';
import { Check, Loader2 } from 'lucide-react';
import type { ActivityLog } from '@/lib/types';
import { StageHeader } from './ui';
import { agentLabel, describeStep } from './agents';

const STEP_TITLES = [
  { title: 'Preparing your questions', description: 'Lume is working out what it needs to know about your topic.' },
  { title: 'Drafting a research plan', description: 'Turning your answers into a plan you can review and edit.' },
  { title: 'Gathering sources', description: 'Searching arXiv, OpenAlex, CORE, the web and your library, then reading what it finds.' },
  { title: 'Gathering sources', description: 'Searching arXiv, OpenAlex, CORE, the web and your library, then reading what it finds.' },
  { title: 'Writing your paper', description: 'Writing each section, reviewing the draft and checking the citations. This takes a few minutes.' },
];

export default function StageResearching({ step, activeThought, logs }: {
  step: number;
  activeThought: { agent: string; text: string } | null;
  logs: ActivityLog[];
}) {
  const { title, description } = STEP_TITLES[step] ?? STEP_TITLES[0];
  // Long streams are noisy; show the most recent part
  const stream = activeThought?.text.slice(-700) ?? '';

  return (
    <div className="space-y-8">
      <StageHeader title={title} description={description} />

      <section aria-live="polite" className="border border-mistral-black/10 bg-mistral-beige/40 p-5 sm:p-6 space-y-3">
        <div className="flex items-center gap-2.5 text-sm font-semibold text-mistral-black">
          <Loader2 className="w-4 h-4 text-mistral-orange animate-spin" aria-hidden />
          {activeThought ? agentLabel(activeThought.agent) : 'Starting up'}
        </div>
        {stream && (
          <p className="text-sm text-mistral-black/70 leading-relaxed whitespace-pre-wrap break-words max-h-64 overflow-hidden">
            {stream.length < (activeThought?.text.length ?? 0) && '…'}
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
