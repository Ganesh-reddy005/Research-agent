"use client";

import React, { useState } from 'react';
import { ArrowRight, Plus, RotateCcw, Trash2 } from 'lucide-react';
import type { BenchmarkSpec, Hypothesis, Lab } from '@/lib/types';
import { Button, SectionLabel, StageHeader, inputClass } from './ui';
import BenchmarkFields from './BenchmarkFields';

export default function StageExperimentPlan({ lab, onApprove, onRetry, isProcessing }: {
  lab: Lab;
  onApprove: (data: { hypotheses: Hypothesis[]; setup?: string[]; spec?: BenchmarkSpec }) => void;
  onRetry: () => void;  // planning failed: run the failed step again
  isProcessing: boolean;
}) {
  const done = lab.hypotheses.filter(h => h.status === 'done');
  const [ideas, setIdeas] = useState<Hypothesis[]>(lab.hypotheses.filter(h => h.status !== 'done'));
  const [setup, setSetup] = useState(lab.setup);
  const [spec, setSpec] = useState(lab.spec);
  const update = (i: number, patch: Partial<Hypothesis>) => setIdeas(ideas.map((h, j) => (j === i ? { ...h, ...patch } : h)));
  const valid = ideas.some(h => h.idea.trim()) && (lab.ready || spec.measure.trim());

  const approve = () => onApprove({
    hypotheses: [...done, ...ideas.filter(h => h.idea.trim())],
    ...(lab.ready ? {} : { setup: setup.filter(c => c.trim()), spec: { ...spec, protected: spec.protected.filter(g => g.trim()) } }),
  });

  return (
    <div className="space-y-10">
      <StageHeader
        title={lab.ready ? 'Review the revised plan' : lab.mode === 'build' ? 'Review the plan to build from scratch' : 'Review the experiment plan'}
        description="Nothing runs until you approve. Edit the ideas, and before the first run, how attempts are set up and graded."
      />

      {lab.env?.summary && (
        <section className="space-y-2">
          <SectionLabel>{lab.mode === 'build' ? 'What Lume will build' : 'What Lume found in the code'}</SectionLabel>
          <p className="text-base text-mistral-black/85 leading-relaxed">{lab.env.summary}</p>
          {lab.env.risks && lab.env.risks.length > 0 && (
            <p className="text-sm text-mistral-black/70">Watch out for: {lab.env.risks.join('; ')}</p>
          )}
        </section>
      )}
      {(lab.error || (lab.env?.questions?.length ?? 0) > 0) && (
        <section className="p-4 border border-mistral-orange/40 bg-mistral-orange/5 text-sm text-mistral-black/85 space-y-1">
          {lab.error && <p>{lab.error}</p>}
          {lab.env?.questions?.map(q => <p key={q}>Open question: {q}</p>)}
        </section>
      )}

      <section className="space-y-4">
        <SectionLabel>{lab.mode === 'build' ? 'Steps to build, in order (step 1 writes the evaluation)' : 'Ideas to try, in order'}</SectionLabel>
        {done.length > 0 && <p className="text-sm text-mistral-black/60">Already tried: {done.map(h => h.idea).join('; ')}</p>}
        <ol className="space-y-3">
          {ideas.map((h, i) => (
            <li key={i} className="border border-mistral-black/10 p-4 bg-white space-y-2">
              <div className="flex items-center gap-3">
                <span className="text-sm font-semibold text-mistral-orange w-6 shrink-0">{i + 1}.</span>
                <input value={h.idea} onChange={e => update(i, { idea: e.target.value })} aria-label={`Idea ${i + 1}`}
                       placeholder="One concrete change" className={`${inputClass} !py-2 font-semibold`} />
                <button onClick={() => setIdeas(ideas.filter((_, j) => j !== i))} aria-label={`Remove idea ${i + 1}`}
                        className="p-2 text-mistral-black/50 hover:text-red-600 transition-colors"><Trash2 className="w-4 h-4" /></button>
              </div>
              {(h.why || h.expected_gain) && (
                <p className="text-sm text-mistral-black/65 sm:ml-9">{h.why}{h.expected_gain ? ` Expected: ${h.expected_gain}.` : ''}</p>
              )}
            </li>
          ))}
        </ol>
        <Button variant="secondary" onClick={() => setIdeas([...ideas, { id: 0, idea: '', status: 'pending' }])}>
          <Plus className="w-4 h-4" aria-hidden /> Add an idea
        </Button>
      </section>

      <BenchmarkFields setup={setup} spec={spec} locked={lab.ready} onChange={(s, b) => { setSetup(s); setSpec(b); }} />

      <div className="flex flex-col sm:flex-row sm:items-center gap-3 sm:justify-end pt-6 border-t border-mistral-black/10">
        {!valid && <span className="text-sm text-mistral-black/60">Add at least one idea{lab.ready ? '' : ' and a measure command'}, or try again.</span>}
        {lab.error && (
          <Button variant="secondary" onClick={onRetry} disabled={isProcessing} className="!px-6 !py-3 mt-6">
            <RotateCcw className="w-4 h-4" aria-hidden /> Try again
          </Button>
        )}
        <Button onClick={approve} disabled={!valid} loading={isProcessing} className="!px-6 !py-3">
          {lab.ready ? 'Approve and run the next attempt'
            : lab.mode === 'build' ? 'Approve, set up and write the evaluation' : 'Approve, set up and measure the baseline'} <ArrowRight className="w-4 h-4" aria-hidden />
        </Button>
      </div>
    </div>
  );
}
