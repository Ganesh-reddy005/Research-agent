"use client";

import React from 'react';
import { Fingerprint } from 'lucide-react';

export default function Features() {
  return (
    <section id="features" className="py-32 px-6 bg-mistral-black text-white relative overflow-hidden">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center gap-24">
        <div className="flex-1 space-y-12">
          <div className="space-y-6">
            <h2 className="text-5xl md:text-6xl font-serif leading-[1.1] tracking-tight">
              Research takes <br /> 
              <span className="italic font-light text-mistral-orange">many forms.</span>
            </h2>
            <p className="text-lg text-white/50 leading-relaxed font-sans max-w-md">
              Whether you need a quick answer or a comprehensive paper draft, Lume supports you from start to finish.
            </p>
          </div>

          <div className="grid grid-cols-1 gap-8 pt-4">
            {[
              { label: "Talk to your sources", desc: "Query the data Lume has extracted from your paper clusters in plain English." },
              { label: "Final Manuscript Drafts", desc: "Export complete, structured drafts in IEEE, APA, or custom scholarly formats." },
              { label: "Continuous Updates", desc: "Lume monitors your research topics and alerts you when new relevant data drops." }
            ].map((item, i) => (
              <div key={i} className="group border-l border-white/20 hover:border-mistral-orange pl-8 transition-colors">
                <div className="text-xl font-serif text-white tracking-tight mb-2 italic">{item.label}</div>
                <p className="text-sm font-sans text-white/40">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Dashboard Preview UI (Subtle/Modern) */}
        <div className="flex-1 w-full p-1 bg-white/10 rounded-[3rem] border border-white/10">
           <div className="bg-white rounded-[2.5rem] p-10 flex flex-col font-sans text-mistral-black shadow-2xl overflow-hidden aspect-square">
              <div className="flex justify-between items-center border-b border-mistral-black/5 pb-4 mb-8">
                <div className="flex gap-2">
                   <div className="w-2.5 h-2.5 rounded-full bg-red-400" />
                   <div className="w-2.5 h-2.5 rounded-full bg-amber-400" />
                   <div className="w-2.5 h-2.5 rounded-full bg-green-400" />
                </div>
                <span className="text-[10px] font-bold text-mistral-black/20 uppercase tracking-widest">Active Analysis: Quantum-v2</span>
              </div>
              <div className="space-y-6 flex-1">
                <div className="h-4 w-1/3 bg-mistral-black/5 rounded-full" />
                <div className="space-y-3">
                  <div className="h-2 w-full bg-mistral-black/5 rounded-full" />
                  <div className="h-2 w-5/6 bg-mistral-black/5 rounded-full" />
                  <div className="h-2 w-4/6 bg-mistral-orange/20 rounded-full" />
                </div>
                <div className="p-6 bg-mistral-beige/50 rounded-2xl border border-mistral-black/5 space-y-4">
                   <div className="flex items-center gap-3">
                      <Fingerprint className="w-4 h-4 text-mistral-orange" />
                      <span className="text-[10px] font-bold uppercase tracking-wider">Source Integrity Verified</span>
                   </div>
                   <div className="h-2 w-1/2 bg-mistral-orange/10 rounded-full" />
                </div>
              </div>
              <div className="mt-auto pt-6 flex justify-between items-center border-t border-mistral-black/5">
                <div className="flex gap-4">
                   <div className="h-8 w-8 bg-mistral-beige rounded-lg" />
                   <div className="h-8 w-8 bg-mistral-beige rounded-lg" />
                </div>
                <div className="h-10 w-28 bg-mistral-black rounded-lg" />
              </div>
           </div>
        </div>
      </div>
    </section>
  );
}
