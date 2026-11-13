"use client";

import React, { useState } from 'react';
import { FlaskConical, PenLine } from 'lucide-react';
import type { ExperimentBrief } from '@/lib/types';
import { Button, SectionLabel, StageHeader, inputClass } from './ui';
import BriefListField from './BriefListField';

/** What still has to be filled in before the coding agent can start (mirrors the backend's check). */
function missingFields(b: ExperimentBrief): string[] {
  const missing = [['objective', b.objective], ['target', b.target], ['metric', b.metric.name]]
    .filter(([, value]) => !value.trim()).map(([label]) => label);
  return b.open_questions.length ? [...missing, 'answers to the open questions'] : missing;
}

/** Answered questions move into the notes the agent reads, as "question → answer". */
function applyAnswers(brief: ExperimentBrief, answers: Record<number, string>): ExperimentBrief {
  const answered = brief.open_questions.map((q, i) => [q, answers[i]?.trim()] as const);
  return {
    ...brief,
    open_questions: answered.filter(([, a]) => !a).map(([q]) => q),
    notes: [...brief.notes, ...answered.filter(([, a]) => a).map(([q, a]) => `${q} → ${a}`)].filter(n => n.trim()),
    must_hold: brief.must_hold.filter(t => t.trim()),
    off_limits: brief.off_limits.filter(t => t.trim()),
  };
}

export default function StageExperimentBrief({ brief: initial, onSave, onWritePaper, isProcessing }: {
  brief: ExperimentBrief;
  onSave: (brief: ExperimentBrief) => Promise<string[]>;
  onWritePaper: () => void;
  isProcessing: boolean;
}) {
  const [brief, setBrief] = useState<ExperimentBrief>(initial);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState<string | null>(null);

  const set = (patch: Partial<ExperimentBrief>) => { setBrief(prev => ({ ...prev, ...patch })); setStatus(null); };
  const setMetric = (patch: Partial<ExperimentBrief['metric']>) => set({ metric: { ...brief.metric, ...patch } });
  const missing = missingFields(applyAnswers(brief, answers));

  const save = async () => {
    setSaving(true);
    try {
      await onSave(applyAnswers(brief, answers));
      setBrief(prev => applyAnswers(prev, answers));
      setAnswers({});
      setStatus('Saved.');
    } catch (err) {
      setStatus(err instanceof Error ? err.message : 'Could not save the brief.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-10">
      <StageHeader
        title="Plan the experiments"
        description="The coding agent works from this brief. After every attempt it reports what changed and what it would try next, and you decide: continue, stop, or change the plan."
      />

      {brief.open_questions.length > 0 && (
        <section className="space-y-4 p-5 border border-mistral-orange/40 bg-mistral-orange/5">
          <SectionLabel>Lume needs your answers first</SectionLabel>
          {brief.open_questions.map((q, i) => (
            <label key={i} className="block space-y-2">
              <span className="text-base text-mistral-black">{q}</span>
              <input value={answers[i] ?? ''} onChange={e => setAnswers({ ...answers, [i]: e.target.value })}
                     placeholder="Your answer" className={`${inputClass} !py-2`} />
            </label>
          ))}
        </section>
      )}

      <section className="space-y-3">
        <SectionLabel>Objective</SectionLabel>
        <textarea value={brief.objective} onChange={e => set({ objective: e.target.value })} rows={2}
                  aria-label="Objective" placeholder="What should the experiments improve or test?"
                  className={`${inputClass} resize-y`} />
      </section>

      <section className="space-y-3">
        <SectionLabel>Target</SectionLabel>
        <input value={brief.target} onChange={e => set({ target: e.target.value })} aria-label="Target"
               placeholder="Repository URL, or the system to experiment on" className={inputClass} />
      </section>

      <section className="space-y-3">
        <SectionLabel>How success is measured</SectionLabel>
        <div className="grid sm:grid-cols-[1fr_auto] gap-2">
          <input value={brief.metric.name} onChange={e => setMetric({ name: e.target.value })} aria-label="Metric"
                 placeholder="The number that decides success" className={inputClass} />
          <select value={brief.metric.goal} onChange={e => setMetric({ goal: e.target.value as 'maximize' | 'minimize' })}
                  aria-label="Better when" className={`${inputClass} sm:w-48`}>
            <option value="maximize">Higher is better</option>
            <option value="minimize">Lower is better</option>
          </select>
        </div>
        <input value={brief.metric.measured_by} onChange={e => setMetric({ measured_by: e.target.value })}
               aria-label="Measured by" placeholder="Measured by: the tool, command or procedure" className={inputClass} />
        <input value={brief.baseline} onChange={e => set({ baseline: e.target.value })} aria-label="Baseline"
               placeholder="Compared with: the unmodified system, or a published result" className={inputClass} />
      </section>

      <BriefListField label="Must still pass" hint="Checks every attempt must pass, so a better number is a real improvement."
                      items={brief.must_hold} placeholder="e.g. the test suite passes" onChange={must_hold => set({ must_hold })} />
      <BriefListField label="Must not change" hint="Anything that would make the comparison unfair if changed."
                      items={brief.off_limits} placeholder="e.g. the evaluation data" onChange={off_limits => set({ off_limits })} />
      <BriefListField label="Notes for the agent" items={brief.notes}
                      placeholder="Anything else it should know" onChange={notes => set({ notes })} />

      <section className="space-y-2">
        <SectionLabel>Attempt limit</SectionLabel>
        <div className="flex items-center gap-3">
          <input type="number" min={1} max={20} value={brief.attempt_limit} aria-label="Attempt limit"
                 onChange={e => set({ attempt_limit: Math.min(20, Math.max(1, Number(e.target.value) || 1)) })}
                 className={`${inputClass} !w-24 !py-2`} />
          <p className="text-sm text-mistral-black/60">A safety limit. You still decide after every attempt.</p>
        </div>
      </section>

      <div className="space-y-4 pt-6 border-t border-mistral-black/10">
        {missing.length > 0 && <p className="text-sm text-mistral-black/70">Before launch, add: {missing.join(', ')}.</p>}
        {status && <p className="text-sm text-mistral-black/70" role="status">{status}</p>}
        <div className="flex flex-col sm:flex-row gap-3 sm:justify-end">
          <Button variant="ghost" onClick={onWritePaper} disabled={isProcessing}>
            <PenLine className="w-4 h-4" aria-hidden /> Write the draft instead
          </Button>
          <Button variant="secondary" onClick={save} loading={saving}>Save brief</Button>
          <Button disabled title="The coding agent arrives with the sandbox. Your saved brief will be ready for it."
                  className="!px-6">
            <FlaskConical className="w-4 h-4" aria-hidden /> Launch coding agent
          </Button>
        </div>
        <p className="text-sm text-mistral-black/60 sm:text-right">The coding agent arrives with the sandbox. Your saved brief will be ready for it.</p>
      </div>
    </div>
  );
}
