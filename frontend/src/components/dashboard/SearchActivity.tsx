"use client";

import React, { useState } from 'react';
import { Check, ChevronDown, Loader2 } from 'lucide-react';
import type { SearchSource, SearchStep } from '@/lib/types';

const TOOL_LABEL: Record<string, string> = {
  web_search: 'the web',
  search_arxiv: 'arXiv',
  search_openalex: 'OpenAlex',
};

export function sourceSite(s: SearchSource) {
  try {
    return new URL(s.url).hostname.replace(/^www\./, '');
  } catch {
    return s.source;
  }
}

/** Every source found in a turn, once each, in citation order. */
export function uniqueSources(searches: SearchStep[] = []) {
  const byNumber = new Map<number, SearchSource>();
  searches.forEach(step => step.sources.forEach(s => byNumber.set(s.n, s)));
  return Array.from(byNumber.values()).sort((a, b) => a.n - b.n);
}

export function SourceLink({ s }: { s: SearchSource }) {
  return (
    <a
      href={s.url}
      target="_blank"
      rel="noopener noreferrer"
      className="flex gap-2.5 text-sm leading-snug hover:text-mistral-orange group"
    >
      <span className="font-semibold text-mistral-orange tabular-nums shrink-0">[{s.n}]</span>
      <span className="min-w-0">
        <span className="block text-mistral-black group-hover:text-mistral-orange">{s.title}</span>
        <span className="block text-xs text-mistral-black/60">
          {sourceSite(s)}{s.year ? ` · ${s.year}` : ''}
        </span>
      </span>
    </a>
  );
}

function SearchRow({ step }: { step: SearchStep }) {
  const [open, setOpen] = useState(false);
  const where = TOOL_LABEL[step.tool] ?? step.tool;
  const searching = step.status === 'searching';

  return (
    <li>
      <button
        onClick={() => setOpen(!open)}
        disabled={searching || step.sources.length === 0}
        aria-expanded={open}
        className="w-full flex items-center gap-2.5 text-left text-sm text-mistral-black/75 enabled:hover:text-mistral-black"
      >
        {searching
          ? <Loader2 className="w-4 h-4 text-mistral-orange animate-spin shrink-0" aria-hidden />
          : <Check className="w-4 h-4 text-mistral-orange shrink-0" aria-hidden />}
        <span className="min-w-0 truncate">
          {searching ? 'Searching' : 'Searched'} {where} for <span className="text-mistral-black">“{step.query}”</span>
          {searching ? '…' : ` · ${step.sources.length} result${step.sources.length === 1 ? '' : 's'}`}
        </span>
        {!searching && step.sources.length > 0 && (
          <ChevronDown className={`w-4 h-4 shrink-0 text-mistral-black/50 transition-transform ${open ? 'rotate-180' : ''}`} aria-hidden />
        )}
      </button>
      {open && (
        <ul className="mt-3 mb-1 ml-6 space-y-3">
          {step.sources.map(s => <li key={s.n}><SourceLink s={s} /></li>)}
        </ul>
      )}
    </li>
  );
}

/** Live search progress plus the sources an answer can cite. */
export default function SearchActivity({ searches }: { searches: SearchStep[] }) {
  const [showAll, setShowAll] = useState(false);
  const sources = uniqueSources(searches);
  const visible = showAll ? sources : sources.slice(0, 4);

  return (
    <div className="space-y-4 mb-5">
      <ul className="space-y-2" aria-live="polite">
        {searches.map(step => <SearchRow key={step.id} step={step} />)}
      </ul>

      {sources.length > 0 && (
        <section className="border border-mistral-black/10 bg-mistral-beige/40 p-4 space-y-3">
          <h3 className="text-xs font-semibold text-mistral-black/70">Sources</h3>
          <ul className="grid sm:grid-cols-2 gap-3">
            {visible.map(s => <li key={s.n}><SourceLink s={s} /></li>)}
          </ul>
          {sources.length > 4 && (
            <button onClick={() => setShowAll(!showAll)} className="text-sm font-medium text-mistral-black/70 hover:text-mistral-orange">
              {showAll ? 'Show fewer' : `Show all ${sources.length} sources`}
            </button>
          )}
        </section>
      )}
    </div>
  );
}
