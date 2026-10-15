"use client";

import React, { useState } from 'react';
import { ArrowRight } from 'lucide-react';
import type { ResearchDepth } from '@/lib/types';
import { Button, inputClass } from './ui';

type Mode = 'research' | 'brainstorm';

const EXAMPLES = [
  'Does retrieval-augmented generation reduce hallucinations in code-generation models?',
  'How do learned index structures compare with B-trees on real-world workloads?',
  'What are the trade-offs between sparse and dense attention for long-context transformers?',
  'How effective are LLM-based fuzzers at finding memory-safety bugs compared with AFL++?',
];

const DEPTHS: { id: ResearchDepth; label: string; description: string }[] = [
  { id: 'light', label: 'Quick', description: '15+ sources. Faster, good for a first look.' },
  { id: 'deep', label: 'Deep research', description: '50+ sources. More thorough, takes longer.' },
];

const NEXT_STEPS = [
  'Lume asks a few questions to pin down the scope.',
  'You review and edit the research plan before anything is searched.',
  'Lume searches arXiv, OpenAlex, CORE, the web and your library, then writes the paper.',
];

export default function StageIdle({ onStartResearch, onStartBrainstorm }: {
  onStartResearch: (topic: string, depth: ResearchDepth) => void;
  onStartBrainstorm: (idea: string) => void;
}) {
  const [mode, setMode] = useState<Mode>('research');
  // Separate draft per tab, so switching tabs neither carries text over nor loses it
  const [drafts, setDrafts] = useState<Record<Mode, string>>({ research: '', brainstorm: '' });
  const text = drafts[mode];
  const setText = (value: string) => setDrafts(prev => ({ ...prev, [mode]: value }));
  const [depth, setDepth] = useState<ResearchDepth>('light');

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    const value = text.trim();
    if (!value) return;
    if (mode === 'research') onStartResearch(value, depth);
    else onStartBrainstorm(value);
  };

  return (
    <div className="space-y-10 py-4 sm:py-10">
      <div className="space-y-3">
        <h1 className="font-serif text-4xl sm:text-5xl text-mistral-black tracking-tight leading-tight">
          {mode === 'research' ? 'What do you want to research?' : 'What idea are you exploring?'}
        </h1>
        <p className="text-base text-mistral-black/65 leading-relaxed">
          {mode === 'research'
            ? 'Describe your research question in a sentence or two. You can refine it in the next steps.'
            : 'Talk an idea through before committing to a research project.'}
        </p>
      </div>

      <div role="tablist" aria-label="Mode" className="inline-flex border border-mistral-black/15 p-1 bg-mistral-beige/60">
        {(['research', 'brainstorm'] as Mode[]).map(m => (
          <button
            key={m}
            role="tab"
            aria-selected={mode === m}
            onClick={() => setMode(m)}
            className={`px-4 py-2 text-sm font-medium transition-colors ${mode === m ? 'bg-white text-mistral-black shadow-sm' : 'text-mistral-black/60 hover:text-mistral-black'}`}
          >
            {m === 'research' ? 'Research project' : 'Brainstorm'}
          </button>
        ))}
      </div>

      <form onSubmit={submit} className="space-y-6">
        <label className="block space-y-2">
          <span className="sr-only">{mode === 'research' ? 'Research question' : 'Your idea'}</span>
          <textarea
            value={text}
            onChange={e => setText(e.target.value)}
            onKeyDown={e => {
              // Enter starts; Shift + Enter adds a line (ignored while an IME is composing)
              if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
                e.preventDefault();
                submit(e);
              }
            }}
            rows={4}
            placeholder={mode === 'research'
              ? 'e.g. How do learned index structures compare with B-trees on real-world workloads?'
              : 'e.g. I want to study whether small models can verify the reasoning of larger ones…'}
            className={`${inputClass} resize-none text-lg leading-relaxed`}
          />
        </label>

        {mode === 'research' && (
          <fieldset className="space-y-3">
            <legend className="text-sm font-semibold text-mistral-black/70 mb-3">How deep should Lume go?</legend>
            <div className="grid sm:grid-cols-2 gap-3">
              {DEPTHS.map(d => (
                <label
                  key={d.id}
                  className={`flex gap-3 p-4 border cursor-pointer transition-colors ${depth === d.id ? 'border-mistral-black bg-mistral-beige/50' : 'border-mistral-black/15 hover:border-mistral-black/40'}`}
                >
                  <input
                    type="radio"
                    name="depth"
                    value={d.id}
                    checked={depth === d.id}
                    onChange={() => setDepth(d.id)}
                    className="mt-1 accent-mistral-orange"
                  />
                  <span className="space-y-0.5">
                    <span className="block text-base font-semibold text-mistral-black">{d.label}</span>
                    <span className="block text-sm text-mistral-black/65">{d.description}</span>
                  </span>
                </label>
              ))}
            </div>
          </fieldset>
        )}

        <div className="flex flex-col sm:flex-row sm:items-center gap-3 sm:justify-between">
          <span className="text-sm text-mistral-black/60">Press Enter to start · Shift + Enter for a new line</span>
          <Button type="submit" disabled={!text.trim()} className="!px-6 !py-3">
            {mode === 'research' ? 'Start research' : 'Start brainstorming'}
            <ArrowRight className="w-4 h-4" aria-hidden />
          </Button>
        </div>
      </form>

      {mode === 'research' && (
        <div className="grid gap-10 sm:grid-cols-2 pt-8 border-t border-mistral-black/10">
          <section className="space-y-3">
            <h2 className="text-sm font-semibold text-mistral-black/70">Try an example</h2>
            <ul className="space-y-2">
              {EXAMPLES.map(example => (
                <li key={example}>
                  <button
                    onClick={() => setText(example)}
                    className="text-left text-sm text-mistral-black/75 hover:text-mistral-orange leading-relaxed transition-colors"
                  >
                    {example}
                  </button>
                </li>
              ))}
            </ul>
          </section>
          <section className="space-y-3">
            <h2 className="text-sm font-semibold text-mistral-black/70">What happens next</h2>
            <ol className="space-y-2">
              {NEXT_STEPS.map((step, i) => (
                <li key={step} className="flex gap-3 text-sm text-mistral-black/75 leading-relaxed">
                  <span className="font-semibold text-mistral-orange">{i + 1}.</span>
                  {step}
                </li>
              ))}
            </ol>
          </section>
        </div>
      )}
    </div>
  );
}
