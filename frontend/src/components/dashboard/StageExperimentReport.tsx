"use client";

import React, { useState } from 'react';
import { ArrowRight, PenLine, RotateCcw } from 'lucide-react';
import type { Attempt, ExperimentBrief, ExperimentDecision, Lab } from '@/lib/types';
import { Button, SectionLabel, StageHeader, inputClass } from './ui';
import AttemptsTable from './AttemptsTable';

const TITLES: Record<Attempt['verdict'], string> = {
  baseline: 'Baseline measured', improved: 'It got better', 'no gain': 'No real change', worse: 'It got worse',
  'failed checks': 'A check failed', crashed: 'It didn’t run',
};

/** After every attempt: what happened, every result so far, and the user's decision. */
export default function StageExperimentReport({ brief, lab, notebook, onDecide, isProcessing }: {
  brief: ExperimentBrief;
  lab: Lab;
  notebook: Attempt[];
  onDecide: (decision: ExperimentDecision, direction?: string) => void;
  isProcessing: boolean;
}) {
  const [direction, setDirection] = useState('');
  const [revising, setRevising] = useState(!lab.ready);
  const report = lab.report;
  const latest = notebook[notebook.length - 1];
  const left = report?.attempts_left ?? 0;
  const title = !lab.ready ? 'The setup needs fixing' : latest ? `Attempt ${latest.n}: ${TITLES[latest.verdict]}` : 'Report';

  return (
    <div className="space-y-10">
      <StageHeader title={title} description={report?.findings}>
        <p className="text-sm text-mistral-black/60">
          {left} attempt{left === 1 ? '' : 's'} left · spent so far ${(lab.cost_usd ?? 0).toFixed(3)} ({(lab.tokens ?? 0).toLocaleString()} tokens)
        </p>
      </StageHeader>

      {notebook.length > 0 && (
        <section className="space-y-3">
          <SectionLabel>Every attempt so far</SectionLabel>
          <AttemptsTable attempts={notebook} metric={brief.metric.name} goal={brief.metric.goal} />
        </section>
      )}

      {latest?.error && (
        <section className="space-y-2">
          <SectionLabel>What went wrong</SectionLabel>
          <p className="text-sm text-mistral-black/85">{latest.error}</p>
          {latest.log && <pre className="text-xs bg-mistral-black text-white/90 p-3 overflow-x-auto max-h-56 whitespace-pre-wrap">{latest.log}</pre>}
        </section>
      )}

      {report?.next && (
        <section className="space-y-2">
          <SectionLabel>Suggested next</SectionLabel>
          <p className="text-base text-mistral-black/85">{report.next}</p>
          {report.pending.length > 0 && <p className="text-sm text-mistral-black/60">Still planned: {report.pending.join('; ')}</p>}
        </section>
      )}

      {revising && (
        <section className="space-y-2">
          <SectionLabel>How should the plan change?</SectionLabel>
          <textarea value={direction} onChange={e => setDirection(e.target.value)} rows={3} aria-label="Direction for the new plan"
                    placeholder={lab.ready ? 'e.g. Focus on memory layout instead of threading' : 'e.g. The tests need pytest installed first'}
                    className={`${inputClass} resize-y`} />
        </section>
      )}

      <div className="flex flex-col sm:flex-row gap-3 sm:justify-end pt-6 border-t border-mistral-black/10">
        <Button variant="ghost" onClick={() => onDecide('stop')} disabled={isProcessing}>
          <PenLine className="w-4 h-4" aria-hidden /> Stop and write the paper
        </Button>
        {revising ? (
          <Button onClick={() => onDecide('change plan', direction.trim())} disabled={!direction.trim()} loading={isProcessing}>
            <RotateCcw className="w-4 h-4" aria-hidden /> Make a new plan
          </Button>
        ) : (
          <>
            <Button variant="secondary" onClick={() => setRevising(true)} disabled={isProcessing}>Change the plan</Button>
            <Button onClick={() => onDecide('continue')} disabled={left === 0} loading={isProcessing} className="!px-6">
              Continue <ArrowRight className="w-4 h-4" aria-hidden />
            </Button>
          </>
        )}
      </div>
    </div>
  );
}
