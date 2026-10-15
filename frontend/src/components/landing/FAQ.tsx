"use client";

import React from 'react';
import { Plus } from 'lucide-react';
import Eyebrow from './Eyebrow';
import Reveal from './Reveal';

const FAQS = [
  {
    q: 'Is Lume writing my paper for me?',
    a: 'No. You stay the author. You shape the question, approve the plan and the experiments, and decide what goes into the final paper. Lume does the legwork and shows its evidence for every claim, so you can check all of it. Follow your venue’s policy on disclosing AI assistance.',
  },
  {
    q: 'What kinds of experiments can it run?',
    a: 'In early access: Python on CPU, minutes per run. That covers small machine-learning experiments, algorithm and systems benchmarks, and analysis of data you upload. GPU runs are on the roadmap.',
  },
  {
    q: 'Is it safe to run code an AI wrote?',
    a: 'Every run happens in a fresh, isolated sandbox. It has no access to your accounts or API keys, no network unless the approved plan needs it, and strict limits on time and memory. Nothing touches your machine.',
  },
  {
    q: 'What if the results don’t support my hypothesis?',
    a: 'Then the paper says so. Hypotheses and metrics are fixed in the plan before anything runs, so the agent cannot quietly change the target after seeing the numbers. Negative results are results.',
  },
  {
    q: 'Where do the sources come from?',
    a: 'arXiv, OpenAlex, CORE and web search, plus any PDFs you add to your private library. Each source links back to the original document.',
  },
  {
    q: 'Who can see my PDFs and data?',
    a: 'Your library is private to your account: other users can never search or see it. To read and index your documents, Lume sends their text to the AI model providers that power it.',
  },
];

export default function FAQ() {
  return (
    <section id="faq" className="py-24 md:py-32 px-4 sm:px-6 bg-white border-y border-mistral-black/10 scroll-mt-16">
      <div className="max-w-7xl mx-auto grid lg:grid-cols-[1fr_1.6fr] gap-12 lg:gap-24">
        <Reveal className="space-y-6">
          <Eyebrow>FAQ</Eyebrow>
          <h2 className="text-4xl md:text-6xl font-serif text-mistral-black tracking-tight leading-[1.05]">
            Fair <span className="italic">questions.</span>
          </h2>
        </Reveal>

        <Reveal delay={0.08} className="border-t border-mistral-black">
          {FAQS.map(f => (
            <details key={f.q} className="group border-b border-mistral-black/10">
              <summary className="flex cursor-pointer list-none items-center justify-between gap-6 py-6 text-left [&::-webkit-details-marker]:hidden">
                <span className="text-xl md:text-2xl font-serif text-mistral-black tracking-tight group-hover:text-mistral-orange transition-colors">
                  {f.q}
                </span>
                <Plus className="w-4 h-4 shrink-0 text-mistral-black/50 transition-transform duration-300 group-open:rotate-45" aria-hidden />
              </summary>
              <p className="pb-6 pr-10 text-base text-mistral-black/60 leading-relaxed max-w-2xl">{f.a}</p>
            </details>
          ))}
        </Reveal>
      </div>
    </section>
  );
}
