"use client";

import React, { useState } from 'react';
import { ArrowRight } from 'lucide-react';
import type { ResearchDepth, StartResearchRequest } from '@/lib/types';
import { Button, inputClass } from './ui';
import PageCountField from './PageCountField';

type Mode = 'research' | 'repo' | 'brainstorm';

const EXAMPLES = [
  'Can I build a text-to-speech model that fits under 1 GB and still sounds natural?',
  'How small can an image classifier get on CIFAR-10 before accuracy drops? Compare pruning and quantisation.',
  'Can a fine-tuned 1B-parameter model fix Python bugs as well as much larger models?',
  'Can a compact model detect pneumonia from chest X-rays, trained on a public dataset?',
  'Which efficient attention method works best for long documents on a single GPU?',
  'How much energy does fine-tuning a small LLM use, and which techniques reduce it the most?',
];

const DEPTHS: { id: ResearchDepth; label: string; description: string }[] = [
  { id: 'light', label: 'Quick', description: '15+ sources. Faster, good for a first look.' },
  { id: 'deep', label: 'Deep research', description: '50+ sources. More thorough, takes longer.' },
];

const MODES: Record<Mode, { tab: string; title: string; description: string; placeholder: string; submit: string; steps?: string[] }> = {
  research: {
    tab: 'Research project',
    title: 'What do you want to research?',
    description: 'Describe your research question in a sentence or two. You can refine it in the next steps.',
    placeholder: 'e.g. How do learned index structures compare with B-trees on real-world workloads?',
    submit: 'Start research',
    steps: [
      'Lume asks a few questions to pin down the scope.',
      'You review and edit the research plan before anything is searched.',
      'Lume searches Semantic Scholar, arXiv, OpenAlex, CORE, the web and your library, then writes the paper.',
    ],
  },
  repo: {
    tab: 'From GitHub',
    title: 'Which project should Lume write up?',
    description: 'Paste a public GitHub repository. Lume reads the code, finds related work and writes a paper about your project.',
    placeholder: 'Optional: anything Lume should know, e.g. "Final-year project for my Operating Systems course. We measured a 2x speed-up on…"',
    submit: 'Read repository',
    steps: [
      'Lume reads your repository and summarises what the project does.',
      'You answer a few questions only you can answer, then review the plan.',
      'Lume finds related work and writes the paper, citing your code and the literature.',
    ],
  },
  brainstorm: {
    tab: 'Brainstorm',
    title: 'What idea are you exploring?',
    description: 'Talk an idea through before committing to a research project.',
    placeholder: 'e.g. I want to study whether small models can verify the reasoning of larger ones…',
    submit: 'Start brainstorming',
  },
};

export default function StageIdle({ onStartResearch, onStartBrainstorm }: {
  onStartResearch: (request: StartResearchRequest) => void;
  onStartBrainstorm: (idea: string) => void;
}) {
  const [mode, setMode] = useState<Mode>('research');
  // Separate draft per tab, so switching tabs neither carries text over nor loses it
  const [drafts, setDrafts] = useState<Record<Mode, string>>({ research: '', repo: '', brainstorm: '' });
  const text = drafts[mode];
  const setText = (value: string) => setDrafts(prev => ({ ...prev, [mode]: value }));
  const [repoUrl, setRepoUrl] = useState('');
  const [depth, setDepth] = useState<ResearchDepth>('light');
  const [pages, setPages] = useState<number | null>(null);
  const copy = MODES[mode];
  const canSubmit = mode === 'repo' ? !!repoUrl.trim() : !!text.trim();

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSubmit) return;
    const value = text.trim();
    if (mode === 'brainstorm') return onStartBrainstorm(value);
    const request: StartResearchRequest = { topic: value, mode: depth, ...(pages ? { pages } : {}) };
    onStartResearch(mode === 'repo' ? { ...request, repo_url: repoUrl.trim() } : request);
  };

  return (
    <div className="space-y-10 py-4 sm:py-10">
      <div className="space-y-3">
        <h1 className="font-serif text-4xl sm:text-5xl text-mistral-black tracking-tight leading-tight">{copy.title}</h1>
        <p className="text-base text-mistral-black/65 leading-relaxed">{copy.description}</p>
      </div>

      <div role="tablist" aria-label="Mode" className="inline-flex flex-wrap border border-mistral-black/15 p-1 bg-mistral-beige/60">
        {(Object.keys(MODES) as Mode[]).map(m => (
          <button
            key={m}
            role="tab"
            aria-selected={mode === m}
            onClick={() => setMode(m)}
            className={`px-4 py-2 text-sm font-medium transition-colors ${mode === m ? 'bg-white text-mistral-black shadow-sm' : 'text-mistral-black/60 hover:text-mistral-black'}`}
          >
            {MODES[m].tab}
          </button>
        ))}
      </div>

      <form onSubmit={submit} className="space-y-6">
        {mode === 'repo' && (
          <label className="block space-y-2">
            <span className="block text-sm font-semibold text-mistral-black/70">GitHub repository</span>
            <input
              type="url"
              inputMode="url"
              value={repoUrl}
              onChange={e => setRepoUrl(e.target.value)}
              placeholder="https://github.com/owner/repository"
              className={`${inputClass} text-lg`}
            />
          </label>
        )}

        <label className="block space-y-2">
          <span className={mode === 'repo' ? 'block text-sm font-semibold text-mistral-black/70' : 'sr-only'}>
            {mode === 'repo' ? 'Notes about the project' : mode === 'research' ? 'Research question' : 'Your idea'}
          </span>
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
            rows={mode === 'repo' ? 3 : 4}
            placeholder={copy.placeholder}
            className={`${inputClass} resize-none ${mode === 'repo' ? 'text-base' : 'text-lg'} leading-relaxed`}
          />
        </label>

        {mode !== 'brainstorm' && <PageCountField value={pages} onChange={setPages} />}

        {mode !== 'brainstorm' && (
          <fieldset className="space-y-3">
            <legend className="text-sm font-semibold text-mistral-black/70 mb-3">How deep should Lume go?</legend>
            <div className="grid sm:grid-cols-2 gap-3">
              {DEPTHS.map(d => (
                <label
                  key={d.id}
                  className={`flex gap-3 p-4 border cursor-pointer transition-colors ${depth === d.id ? 'border-mistral-black bg-mistral-beige/50' : 'border-mistral-black/15 hover:border-mistral-black/40'}`}
                >
                  <input type="radio" name="depth" value={d.id} checked={depth === d.id} onChange={() => setDepth(d.id)} className="mt-1 accent-mistral-orange" />
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
          <Button type="submit" disabled={!canSubmit} className="!px-6 !py-3">
            {copy.submit}
            <ArrowRight className="w-4 h-4" aria-hidden />
          </Button>
        </div>
      </form>

      {copy.steps && (
        <div className="grid gap-10 sm:grid-cols-2 pt-8 border-t border-mistral-black/10">
          {mode === 'research' && (
            <section className="space-y-3">
              <h2 className="text-sm font-semibold text-mistral-black/70">Try an example</h2>
              <ul className="space-y-2">
                {EXAMPLES.map(example => (
                  <li key={example}>
                    <button onClick={() => setText(example)} className="text-left text-sm text-mistral-black/75 hover:text-mistral-orange leading-relaxed transition-colors">
                      {example}
                    </button>
                  </li>
                ))}
              </ul>
            </section>
          )}
          <section className="space-y-3">
            <h2 className="text-sm font-semibold text-mistral-black/70">What happens next</h2>
            <ol className="space-y-2">
              {copy.steps.map((step, i) => (
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
