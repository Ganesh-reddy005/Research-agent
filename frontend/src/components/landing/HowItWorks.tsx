"use client";

import React from 'react';
import { MessagesSquare, ListChecks, Library, FlaskConical, PenLine } from 'lucide-react';
import Eyebrow from './Eyebrow';
import Reveal from './Reveal';

const STEPS = [
  {
    icon: MessagesSquare,
    title: 'Clarify',
    body: 'Lume asks the few questions that matter: scope, baselines, constraints, and what would count as a result.',
  },
  {
    icon: ListChecks,
    title: 'Plan',
    body: 'You get a research plan with hypotheses and metrics. Edit it, then approve it. Nothing runs before you do.',
    approval: true,
  },
  {
    icon: Library,
    title: 'Review the literature',
    body: 'Searches arXiv, OpenAlex, CORE, the web and your own PDFs, then maps the themes, disagreements and gaps.',
  },
  {
    icon: FlaskConical,
    title: 'Run the experiments',
    body: 'Writes the code, runs it in an isolated sandbox across several seeds, fixes what breaks, and generates the figures.',
    approval: true,
    earlyAccess: true,
  },
  {
    icon: PenLine,
    title: 'Write and verify',
    body: 'Drafts the paper section by section, has a critic agent review it, and checks each claim against its evidence.',
  },
];

export default function HowItWorks() {
  return (
    <section id="how-it-works" className="py-24 md:py-32 px-4 sm:px-6 scroll-mt-16">
      <div className="max-w-7xl mx-auto space-y-16">
        <Reveal className="max-w-3xl space-y-6">
          <Eyebrow>How it works</Eyebrow>
          <h2 className="text-4xl md:text-6xl font-serif text-mistral-black tracking-tight leading-[1.05]">
            Autonomous where it helps. <span className="italic">You decide where it counts.</span>
          </h2>
          <p className="text-lg text-mistral-black/60 leading-relaxed">
            A team of specialised agents does the legwork between your idea and the draft. You sign off on the
            plan and the experiments before anything runs.
          </p>
        </Reveal>

        <ol className="grid md:grid-cols-5 border-t border-mistral-black">
          {STEPS.map((s, i) => (
            <Reveal as="li" key={s.title} delay={i * 0.07} className="space-y-4 border-b md:border-b-0 md:border-r last:border-r-0 border-mistral-black/10 py-8 md:pr-6 md:[&:not(:first-child)]:pl-6">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-bold text-mistral-orange">{String(i + 1).padStart(2, '0')}</span>
                  <s.icon className="w-5 h-5 text-mistral-black/70" aria-hidden />
                </div>
                <h3 className="text-2xl font-serif text-mistral-black tracking-tight">{s.title}</h3>
                <p className="text-sm text-mistral-black/60 leading-relaxed">{s.body}</p>
                <div className="flex flex-wrap gap-2 font-mono text-[9px] font-bold uppercase tracking-widest">
                  {s.approval && <span className="bg-mistral-black text-white px-2 py-1">You approve</span>}
                  {s.earlyAccess && <span className="border border-mistral-orange text-mistral-orange px-2 py-1">Early access</span>}
                </div>
            </Reveal>
          ))}
        </ol>
      </div>
    </section>
  );
}
