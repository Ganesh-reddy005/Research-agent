"use client";

import React, { useState } from 'react';
import { FileSearch, SquareTerminal, ShieldCheck } from 'lucide-react';
import Eyebrow from './Eyebrow';
import Reveal from './Reveal';

type Ref = 'R3' | 'S12';

const PROMISES = [
  { icon: FileSearch, text: 'Citations open the exact passage they rely on.' },
  { icon: SquareTerminal, text: 'Numbers and figures open the run that produced them.' },
  { icon: ShieldCheck, text: 'Claims without support are flagged before you read the draft.' },
];

function Chip({ id, active, onSelect }: { id: Ref; active: Ref | null; onSelect: (r: Ref | null) => void }) {
  const on = active === id;
  return (
    <button
      type="button"
      onMouseEnter={() => onSelect(id)}
      onFocus={() => onSelect(id)}
      onClick={() => onSelect(on ? null : id)}
      aria-pressed={on}
      className={`mx-0.5 px-1.5 py-0.5 font-mono text-[0.7em] font-bold align-[0.15em] border transition-colors ${
        on ? 'bg-mistral-orange border-mistral-orange text-white' : 'border-mistral-orange/50 text-mistral-orange hover:bg-mistral-orange/10'
      }`}
    >
      {id}
    </button>
  );
}

function EvidenceCard({ id, active, label, children }: { id: Ref; active: Ref | null; label: string; children: React.ReactNode }) {
  const dim = active !== null && active !== id;
  return (
    <div className={`bg-white border p-5 space-y-3 transition-all duration-300 ${
      active === id ? 'border-mistral-orange shadow-[4px_4px_0_0_#ff511c]' : 'border-mistral-black/10'
    } ${dim ? 'opacity-40' : ''}`}>
      <div className="flex items-center justify-between font-mono text-[10px] font-bold uppercase tracking-widest">
        <span className="text-mistral-orange">{id}</span>
        <span className="text-mistral-black/40">{label}</span>
      </div>
      {children}
    </div>
  );
}

export default function Verification() {
  const [active, setActive] = useState<Ref | null>(null);

  return (
    <section id="verification" className="py-24 md:py-32 px-4 sm:px-6 scroll-mt-16">
      <div className="max-w-7xl mx-auto grid lg:grid-cols-[1fr_1.25fr] gap-16 lg:gap-20 items-start">
        <Reveal className="space-y-8 lg:sticky lg:top-28">
          <div className="space-y-6">
            <Eyebrow earlyAccess>Verification</Eyebrow>
            <h2 className="text-4xl md:text-6xl font-serif text-mistral-black tracking-tight leading-[1.05]">
              Every claim comes with a <span className="italic">receipt.</span>
            </h2>
            <p className="text-lg text-mistral-black/60 leading-relaxed max-w-md">
              A Lume paper cites two kinds of evidence: the passage a statement comes from, and the run a result
              comes from. Both are one click away.
            </p>
          </div>
          <ul className="space-y-4">
            {PROMISES.map(p => (
              <li key={p.text} className="flex gap-3 text-sm text-mistral-black/75">
                <p.icon className="w-4 h-4 text-mistral-orange shrink-0 mt-0.5" aria-hidden />
                {p.text}
              </li>
            ))}
          </ul>
        </Reveal>

        <Reveal delay={0.1} className="space-y-4" >
          <div onMouseLeave={() => setActive(null)} className="space-y-4">
            <article className="bg-white border border-mistral-black/10 p-6 sm:p-8 space-y-4">
              <div className="font-mono text-[10px] font-bold uppercase tracking-widest text-mistral-black/40">
                §5 Results · draft
              </div>
              <p className="font-serif text-xl sm:text-2xl leading-relaxed text-mistral-black">
                Restricting each token to a local window plus a few global tokens reduced peak training memory by
                38.1%<Chip id="R3" active={active} onSelect={setActive} /> while staying within 0.4 points of the
                dense baseline&apos;s accuracy<Chip id="R3" active={active} onSelect={setActive} />. This matches
                earlier reports that long-context models rarely need full attention
                <Chip id="S12" active={active} onSelect={setActive} />.
              </p>
              <p className="font-mono text-[10px] uppercase tracking-widest text-mistral-black/35">
                Hover or tap a citation · example output
              </p>
            </article>

            <div className="grid sm:grid-cols-2 gap-4">
              <EvidenceCard id="R3" active={active} label="Experiment run">
                <div className="font-mono text-xs text-mistral-black/70 space-y-1">
                  <div>exp-03 · sparse_attn.py</div>
                  <div className="text-mistral-black/45">seeds 0, 1, 2 · env.lock</div>
                </div>
                <dl className="grid grid-cols-2 gap-y-1 font-mono text-xs border-t border-mistral-black/10 pt-3">
                  <dt className="text-mistral-black/45">peak mem</dt><dd className="text-right">9.10 / 14.71 GB</dd>
                  <dt className="text-mistral-black/45">accuracy</dt><dd className="text-right">0.871 / 0.875</dd>
                  <dt className="text-mistral-black/45">change</dt><dd className="text-right text-mistral-orange">−38.1% · −0.4 pts</dd>
                </dl>
              </EvidenceCard>

              <EvidenceCard id="S12" active={active} label="Source passage">
                <div className="text-sm font-serif text-mistral-black leading-snug">
                  Efficient Attention for Long Sequences <span className="text-mistral-black/40">(example)</span>
                </div>
                <div className="font-mono text-[10px] uppercase tracking-widest text-mistral-black/40">arXiv · §4.2 · p. 6</div>
                <blockquote className="border-l-2 border-mistral-orange pl-3 text-xs text-mistral-black/65 leading-relaxed italic">
                  “…most attention mass concentrates within a local window, with a small set of global tokens
                  accounting for nearly all of the remainder.”
                </blockquote>
                <div className="flex items-center gap-1.5 font-mono text-[10px] font-bold uppercase tracking-widest text-mistral-black/60">
                  <ShieldCheck className="w-3 h-3 text-mistral-orange" aria-hidden /> supports the claim
                </div>
              </EvidenceCard>
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
