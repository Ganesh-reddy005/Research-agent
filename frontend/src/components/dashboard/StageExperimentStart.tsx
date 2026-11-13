"use client";

import React, { useState } from 'react';
import { ArrowRight } from 'lucide-react';
import type { StartingPoint } from '@/lib/types';
import { Button, SectionLabel, StageHeader, inputClass } from './ui';

const SCRATCH = 'scratch';

/** Before Lume reads any code: start from the repository it found, another one, or write it from scratch. */
export default function StageExperimentStart({ start, onChoose, isProcessing }: {
  start: StartingPoint;
  onChoose: (choice: { url: string } | { scratch: true }) => void;
  isProcessing: boolean;
}) {
  const options = [start.url, ...start.alternatives.map(a => a.url)].filter(Boolean);
  const [choice, setChoice] = useState(start.url || SCRATCH);
  const [custom, setCustom] = useState('');
  const why = (url: string) => (url === start.url ? start.why : start.alternatives.find(a => a.url === url)?.why);
  const url = choice === 'custom' ? custom.trim() : choice;

  const option = (value: string, label: React.ReactNode, detail?: string) => (
    <label key={value} className={`flex gap-3 p-4 border cursor-pointer ${choice === value ? 'border-mistral-orange bg-mistral-orange/5' : 'border-mistral-black/10 bg-white'}`}>
      <input type="radio" name="start" checked={choice === value} onChange={() => setChoice(value)} className="mt-1 accent-mistral-orange" />
      <span className="space-y-1">
        <span className="block text-base font-semibold text-mistral-black break-all">{label}</span>
        {detail && <span className="block text-sm text-mistral-black/70">{detail}</span>}
      </span>
    </label>
  );

  return (
    <div className="space-y-10">
      <StageHeader
        title={start.url ? 'Start from existing code?' : 'Nothing existing fits'}
        description={start.url
          ? 'Lume found open-source code that already does much of this. Starting from it is cheaper and stronger than writing everything again. Nothing is read until you choose.'
          : start.if_none || 'Lume found no open-source code that fits, so it can write the code from scratch.'}
      />
      <section className="space-y-3">
        <SectionLabel>Starting point</SectionLabel>
        {options.map(u => option(u, u, why(u)))}
        {option('custom', 'Another repository', 'Paste its URL below')}
        {choice === 'custom' && (
          <input value={custom} onChange={e => setCustom(e.target.value)} placeholder="https://github.com/owner/repo"
                 aria-label="Repository URL" className={inputClass} />
        )}
        {option(SCRATCH, 'Write it from scratch',
                'Lume writes the evaluation first (you review it, then it is frozen), then builds and compares each variant. No baseline: you get a results table.')}
      </section>
      {start.known.length > 0 && (
        <p className="text-sm text-mistral-black/60">Repositories in your research sources: {start.known.join(', ')}</p>
      )}
      <div className="flex justify-end pt-6 border-t border-mistral-black/10">
        <Button onClick={() => onChoose(choice === SCRATCH ? { scratch: true } : { url })}
                disabled={choice === 'custom' && !custom.trim()} loading={isProcessing} className="!px-6 !py-3">
          {choice === SCRATCH ? 'Design it from scratch' : 'Read this code and plan'} <ArrowRight className="w-4 h-4" aria-hidden />
        </Button>
      </div>
    </div>
  );
}
