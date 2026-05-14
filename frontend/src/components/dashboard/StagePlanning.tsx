"use client";

import React from 'react';
import { motion } from 'framer-motion';
import { Loader2 } from 'lucide-react';

interface StagePlanningProps {
  brief: string;
  plan: any;
  onApprove: () => void;
  isProcessing: boolean;
}

export default function StagePlanning({ brief, plan, onApprove, isProcessing }: StagePlanningProps) {
  return (
    <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} className="space-y-16 py-12 max-w-4xl mx-auto px-6">
      <div className="space-y-6 text-center">
        <h2 className="text-5xl font-serif text-mistral-black leading-tight tracking-tight font-bold">Technical <span className="text-mistral-orange italic">Blueprint</span></h2>
        <p className="text-mistral-black/30 font-mono text-[10px] uppercase tracking-[0.3em] italic font-bold">Architected strategic research path for autonomous execution</p>
      </div>

      <div className="bg-white border border-mistral-border/50 shadow-2xl rounded-[3rem] overflow-hidden">
        <div className="px-12 py-16 border-b border-mistral-border/30 bg-[#F5F2ED]/30">
          <div className="flex items-center gap-4 mb-8">
            <div className="w-8 h-px bg-mistral-orange/30" />
            <h3 className="text-[10px] font-bold font-mono text-mistral-orange uppercase tracking-[0.2em]">Strategic Intent</h3>
          </div>
          <p className="text-mistral-black leading-tight font-serif text-4xl tracking-tight font-bold italic">"{brief}"</p>
        </div>
        
        <div className="p-12 md:p-16 space-y-12">
          <div className="flex items-center gap-4">
            <div className="w-8 h-px bg-mistral-black/10" />
            <h3 className="text-[10px] font-bold font-mono text-mistral-black/30 uppercase tracking-[0.2em]">Planned Architecture</h3>
          </div>
          <div className="grid md:grid-cols-2 gap-8">
            {plan?.sections?.map((s: any, i: number) => (
              <div key={i} className="flex gap-8 p-8 border border-mistral-border/30 bg-white hover:border-mistral-orange/20 transition-all shadow-sm rounded-3xl group active:scale-[0.99] hover:shadow-lg">
                <div className="text-4xl font-serif font-bold text-mistral-orange/10 group-hover:text-mistral-orange transition-colors italic">0{i+1}</div>
                <div className="space-y-3">
                  <div className="font-bold font-sans text-mistral-black text-lg tracking-tight leading-tight">{s.title}</div>
                  <div className="text-xs text-mistral-black/40 font-sans leading-relaxed line-clamp-3 italic">{s.description}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="flex flex-col sm:flex-row items-center justify-center gap-8 pt-6">
        <button 
          onClick={onApprove}
          disabled={isProcessing}
          className="bg-mistral-black text-white px-16 py-6 rounded-full font-bold font-sans text-xs uppercase tracking-[0.2em] hover:bg-mistral-orange transition-all shadow-2xl active:scale-95 hover:scale-105"
        >
          {isProcessing && <Loader2 className="w-4 h-4 animate-spin inline-block mr-2" />}
          Execute Investigation
        </button>
        <button className="text-[10px] font-bold font-mono text-mistral-black/40 uppercase tracking-[0.2em] hover:text-mistral-orange transition-colors border-b border-transparent hover:border-mistral-orange">
          Refine Brief
        </button>
      </div>
    </motion.div>
  );
}
