"use client";

import React, { useState } from 'react';
import { Plus, Trash2, ArrowRight } from 'lucide-react';
import type { PlanSection, ResearchPlan } from '@/lib/types';
import { Button, SectionLabel, StageHeader, inputClass } from './ui';

export default function StagePlanning({ brief, plan, onApprove, isProcessing }: {
  brief: string;
  plan: ResearchPlan;
  onApprove: (plan: ResearchPlan) => void;
  isProcessing: boolean;
}) {
  const [sections, setSections] = useState<PlanSection[]>(plan.sections);

  const update = (i: number, patch: Partial<PlanSection>) =>
    setSections(sections.map((s, j) => (j === i ? { ...s, ...patch } : s)));

  const valid = sections.length > 0 && sections.every(s => s.title.trim());

  return (
    <div className="space-y-10">
      <StageHeader
        title="Review the research plan"
        description="Edit anything that looks off, then approve. Lume won't start searching until you do."
      />

      {(brief || plan.objective) && (
        <section className="space-y-3">
          <SectionLabel>Goal</SectionLabel>
          {plan.objective && <p className="text-lg text-mistral-black leading-relaxed">{plan.objective}</p>}
          {brief && <p className="text-base text-mistral-black/70 leading-relaxed whitespace-pre-line">{brief}</p>}
        </section>
      )}

      <section className="space-y-4">
        <SectionLabel>Sections of the paper</SectionLabel>
        <ol className="space-y-4">
          {sections.map((s, i) => (
            <li key={i} className="border border-mistral-black/10 p-4 sm:p-5 space-y-3 bg-white">
              <div className="flex items-center gap-3">
                <span className="text-sm font-semibold text-mistral-orange w-6 shrink-0">{i + 1}.</span>
                <input
                  value={s.title}
                  onChange={e => update(i, { title: e.target.value })}
                  aria-label={`Section ${i + 1} title`}
                  placeholder="Section title"
                  className={`${inputClass} !py-2 font-semibold`}
                />
                <button
                  onClick={() => setSections(sections.filter((_, j) => j !== i))}
                  disabled={sections.length === 1}
                  aria-label={`Remove section ${i + 1}`}
                  className="p-2 text-mistral-black/50 hover:text-red-600 disabled:opacity-30 disabled:hover:text-mistral-black/50 transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
              <textarea
                value={s.description}
                onChange={e => update(i, { description: e.target.value })}
                aria-label={`Section ${i + 1} description`}
                placeholder="What should this section cover?"
                rows={2}
                className={`${inputClass} !text-sm resize-y sm:ml-9 sm:w-[calc(100%-2.25rem)]`}
              />
            </li>
          ))}
        </ol>
        <Button
          variant="secondary"
          onClick={() => setSections([...sections, { title: '', description: '', questions: [] }])}
        >
          <Plus className="w-4 h-4" aria-hidden /> Add a section
        </Button>
      </section>

      <div className="flex flex-col sm:flex-row sm:items-center gap-3 sm:justify-end pt-2 border-t border-mistral-black/10">
        {!valid && <span className="text-sm text-mistral-black/60">Every section needs a title.</span>}
        <Button
          onClick={() => onApprove({ ...plan, sections })}
          disabled={!valid}
          loading={isProcessing}
          className="!px-6 !py-3 mt-6"
        >
          Approve plan and start research <ArrowRight className="w-4 h-4" aria-hidden />
        </Button>
      </div>
    </div>
  );
}
