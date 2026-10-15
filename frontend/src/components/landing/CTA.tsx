"use client";

import React from 'react';
import { ArrowRight } from 'lucide-react';
import Reveal from './Reveal';

export default function CTA({ signedIn, onStart }: { signedIn: boolean; onStart: () => void }) {
  return (
    <section className="py-32 md:py-44 px-4 sm:px-6 text-center relative overflow-hidden">
      <div aria-hidden className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[34rem] h-[34rem] max-w-[90vw] max-h-[90vw] rounded-full bg-mistral-orange/10" />
      <Reveal className="max-w-4xl mx-auto space-y-10 relative">
        <h2 className="text-5xl md:text-7xl font-serif text-mistral-black tracking-tight leading-[1.02]">
          Spend your time <br className="hidden sm:block" />
          <span className="italic text-mistral-orange">on the ideas.</span>
        </h2>
        <p className="text-lg text-mistral-black/60 max-w-xl mx-auto leading-relaxed">
          Lume handles the searching, the glue code and the first draft. You make the calls.
        </p>
        <div className="flex flex-col items-center gap-4">
          <button
            onClick={onStart}
            className="group bg-mistral-black text-white text-lg py-5 px-10 sm:px-14 hover:bg-mistral-orange transition-colors font-bold flex items-center gap-3 shadow-[6px_6px_0_0_#ff511c]"
          >
            {signedIn ? 'Open your workspace' : 'Start a research project'}
            <ArrowRight className="w-5 h-5 transition-transform group-hover:translate-x-1" />
          </button>
          <p className="font-mono text-[10px] uppercase tracking-widest text-mistral-black/45">
            Nothing runs without your approval
          </p>
        </div>
      </Reveal>
    </section>
  );
}
