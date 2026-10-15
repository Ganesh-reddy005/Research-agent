"use client";

import React from 'react';
import { motion } from 'framer-motion';
import { ArrowRight, ArrowDown } from 'lucide-react';
import Eyebrow from './Eyebrow';

const SOURCES = ['arXiv', 'OpenAlex', 'CORE', 'The open web', 'Your own PDFs'];
const PIPELINE = ['Clarify', 'Plan', 'Literature', 'Experiments', 'Paper'];

const rise = (delay: number) => ({
  initial: { opacity: 0, y: 18 },
  animate: { opacity: 1, y: 0 },
  transition: { delay, duration: 0.7, ease: [0.22, 1, 0.36, 1] as const },
});

export default function Hero({ signedIn, onStart }: { signedIn: boolean; onStart: () => void }) {
  return (
    <section className="relative min-h-screen flex items-center px-4 sm:px-6 pt-28 pb-16 overflow-hidden">
      <div className="absolute inset-0 z-0">
        <img
          src="/hero_img.png"
          alt=""
          className="w-full h-full object-cover object-[70%_center] opacity-80"
        />
        <div className="absolute inset-0 bg-gradient-to-r from-mistral-beige via-mistral-beige/95 to-mistral-beige/10 md:to-transparent md:w-3/4" />
        <div className="absolute inset-x-0 bottom-0 h-32 bg-gradient-to-t from-mistral-beige to-transparent" />
      </div>

      <div className="max-w-7xl mx-auto w-full relative z-10">
        <div className="max-w-3xl space-y-9">
          <motion.div {...rise(0)}>
            <Eyebrow>Autonomous research agent · for computer science</Eyebrow>
          </motion.div>

          <motion.h1
            {...rise(0.08)}
            className="text-[2.75rem] leading-[1.02] sm:text-6xl md:text-[5.5rem] font-serif text-mistral-black tracking-tight"
          >
            From idea to paper,
            <br />
            <span className="italic text-mistral-orange">with experiments that actually ran.</span>
          </motion.h1>

          <motion.p {...rise(0.18)} className="max-w-xl text-lg md:text-xl text-mistral-black/65 leading-relaxed">
            Lume scopes your question, reviews the literature, writes and runs your experiments in an
            isolated sandbox, then drafts the paper. Every citation points to a real passage. Every
            number points to a real run.
          </motion.p>

          <motion.div {...rise(0.28)} className="flex flex-col sm:flex-row sm:items-center gap-4 sm:gap-6">
            <button
              onClick={onStart}
              className="group bg-mistral-black text-white text-base py-4 px-8 hover:bg-mistral-orange transition-colors font-bold flex items-center justify-center gap-3 shadow-[4px_4px_0_0_#ff511c]"
            >
              {signedIn ? 'Open your workspace' : 'Start a research project'}
              <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
            </button>
            <a
              href="#how-it-works"
              className="flex items-center justify-center gap-2 font-mono text-[11px] font-bold uppercase tracking-widest text-mistral-black/60 hover:text-mistral-orange transition-colors py-3"
            >
              See how it works <ArrowDown className="w-3.5 h-3.5" />
            </a>
          </motion.div>

          <motion.div {...rise(0.4)} className="pt-6 space-y-5">
            <ol className="flex flex-wrap items-center gap-y-2 font-mono text-[10px] font-bold uppercase tracking-widest" aria-label="Lume pipeline">
              {PIPELINE.map((step, i) => (
                <li key={step} className="flex items-center">
                  <span className={`px-2.5 py-1.5 border ${step === 'Experiments' ? 'border-mistral-orange bg-mistral-orange text-white' : 'border-mistral-black/15 bg-white/60 text-mistral-black/70'}`}>
                    {String(i + 1).padStart(2, '0')} {step}
                  </span>
                  {i < PIPELINE.length - 1 && <span className="w-4 h-px bg-mistral-black/25" aria-hidden />}
                </li>
              ))}
            </ol>
            <p className="font-mono text-[10px] uppercase tracking-widest text-mistral-black/45">
              Searches <span className="text-mistral-black/70">{SOURCES.join(' · ')}</span>
            </p>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
