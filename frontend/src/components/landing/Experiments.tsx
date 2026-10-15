"use client";

import React from 'react';
import Eyebrow from './Eyebrow';
import Reveal from './Reveal';

const STEPS = [
  {
    title: 'You approve the experiment',
    body: 'Lume proposes what to test and how success will be measured. Nothing runs until you say yes.',
  },
  {
    title: 'Lume writes and runs the code',
    body: 'Inside a secure, isolated sandbox, completely separate from your computer and your accounts.',
  },
  {
    title: 'Results are checked, not cherry-picked',
    body: 'Every experiment runs several times, so the numbers reflect real variation, not one lucky run.',
  },
  {
    title: 'Real results go into your paper',
    body: 'Tables and charts come straight from the runs, with the code attached so anyone can reproduce them.',
  },
];

// Example run, kept consistent with the Verification section (R3).
const RESULTS = [
  { setup: 'Standard attention (baseline)', memory: '14.71 GB', accuracy: '87.5%' },
  { setup: 'Sparse attention (average of 3 runs)', memory: '9.10 GB', accuracy: '87.1%', highlight: true },
];

function ExampleCard() {
  return (
    <div className="bg-white text-mistral-black shadow-[8px_8px_0_0_#ff511c]">
      <div className="flex items-center justify-between border-b border-mistral-black/10 px-6 py-4 font-mono text-[10px] font-bold uppercase tracking-widest">
        <span className="text-mistral-black/50">Example experiment</span>
        <span className="text-mistral-orange">Cited as R3</span>
      </div>

      <div className="px-6 py-6 space-y-2 border-b border-mistral-black/10">
        <div className="font-mono text-[10px] font-bold uppercase tracking-widest text-mistral-black/40">Hypothesis</div>
        <p className="font-serif text-2xl leading-snug">
          Sparse attention cuts memory use without hurting accuracy.
        </p>
      </div>

      <div className="px-6 py-6 border-b border-mistral-black/10 overflow-x-auto">
        <table className="w-full text-sm">
          <caption className="text-left pb-3 font-mono text-[10px] font-bold uppercase tracking-widest text-mistral-black/40">
            Results
          </caption>
          <thead>
            <tr className="border-y border-mistral-black text-left font-mono text-[10px] uppercase tracking-widest">
              <th scope="col" className="py-2 pr-4 font-bold">Setup</th>
              <th scope="col" className="py-2 px-4 font-bold text-right">Memory</th>
              <th scope="col" className="py-2 pl-4 font-bold text-right">Accuracy</th>
            </tr>
          </thead>
          <tbody className="tabular-nums">
            {RESULTS.map(r => (
              <tr key={r.setup} className="border-b border-mistral-black/10 last:border-mistral-black">
                <th scope="row" className={`py-3 pr-4 text-left font-normal ${r.highlight ? 'text-mistral-black' : 'text-mistral-black/60'}`}>
                  {r.setup}
                </th>
                <td className={`py-3 px-4 text-right font-mono ${r.highlight ? 'font-bold' : 'text-mistral-black/60'}`}>{r.memory}</td>
                <td className={`py-3 pl-4 text-right font-mono ${r.highlight ? 'font-bold' : 'text-mistral-black/60'}`}>{r.accuracy}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="px-6 py-6 grid grid-cols-[auto_1fr] gap-x-5 gap-y-1 items-baseline border-b border-mistral-black/10">
        <span className="font-mono text-[10px] font-bold uppercase tracking-widest text-mistral-black/40 row-span-2">Verdict</span>
        <span className="font-serif text-2xl text-mistral-orange">Supported</span>
        <span className="text-sm text-mistral-black/60">38% less memory, with accuracy within 0.4 points of the baseline.</span>
      </div>

      <div className="px-6 py-4 font-mono text-[10px] uppercase tracking-widest text-mistral-black/45">
        Attached: code · environment · logs for all 3 runs
      </div>
    </div>
  );
}

export default function Experiments() {
  return (
    <section id="experiments" className="py-24 md:py-32 px-4 sm:px-6 bg-mistral-black text-white scroll-mt-16">
      <div className="max-w-7xl mx-auto grid lg:grid-cols-2 gap-16 lg:gap-20 items-center">
        <div className="space-y-12">
          <Reveal className="space-y-6">
            <Eyebrow dark earlyAccess>Experiments</Eyebrow>
            <h2 className="text-4xl md:text-6xl font-serif tracking-tight leading-[1.05]">
              Other tools write about results. <span className="italic text-mistral-orange">Lume runs the experiments.</span>
            </h2>
            <p className="text-lg text-white/60 leading-relaxed max-w-lg">
              Most AI research tools can only summarise what others have already published. Lume writes the code
              for your experiment, runs it, and puts the real numbers into your paper.
            </p>
          </Reveal>

          <ol className="border-t border-white/15">
            {STEPS.map((s, i) => (
              <Reveal as="li" key={s.title} delay={i * 0.06} className="grid grid-cols-[3.5rem_1fr] gap-4 py-6 border-b border-white/15">
                <span className="font-mono text-2xl font-bold text-mistral-orange tabular-nums leading-none pt-1">
                  {String(i + 1).padStart(2, '0')}
                </span>
                <div className="space-y-1.5">
                  <h3 className="text-xl font-serif tracking-tight">{s.title}</h3>
                  <p className="text-sm text-white/50 leading-relaxed">{s.body}</p>
                </div>
              </Reveal>
            ))}
          </ol>
        </div>

        <Reveal delay={0.1}>
          <ExampleCard />
        </Reveal>
      </div>
    </section>
  );
}
