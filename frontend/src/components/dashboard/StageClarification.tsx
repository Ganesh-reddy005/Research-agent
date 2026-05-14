"use client";

import React from 'react';
import { motion } from 'framer-motion';
import { Send, Loader2 } from 'lucide-react';

interface StageClarificationProps {
  questions: any[];
  answers: Record<string, string>;
  setAnswers: (answers: Record<string, string>) => void;
  onSubmit: () => void;
  isProcessing: boolean;
}

export default function StageClarification({ questions, answers, setAnswers, onSubmit, isProcessing }: StageClarificationProps) {
  return (
    <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} className="space-y-16 py-12 max-w-2xl mx-auto px-6">
      <div className="space-y-6 text-center">
        <h2 className="text-5xl font-serif text-mistral-black leading-tight tracking-tight font-bold">Scope <span className="text-mistral-orange italic">Alignment</span></h2>
        <p className="text-mistral-black/30 font-mono text-[10px] uppercase tracking-[0.3em] italic font-bold">Refining domain parameters for maximum relevance</p>
      </div>

      <div className="space-y-12">
        {questions.map((q, i) => (
          <div key={q.id} className="space-y-6">
            <label className="text-sm font-bold font-sans text-mistral-black/60 flex items-center gap-4">
              <span className="w-10 h-10 bg-mistral-orange/5 text-mistral-orange flex items-center justify-center text-[12px] rounded-xl font-mono font-bold border border-mistral-orange/10 italic">0{i+1}</span>
              {q.question}
            </label>
            <input 
              type="text" 
              placeholder="Provide context..."
              className="w-full bg-white border border-mistral-border/50 px-8 py-6 rounded-2xl outline-none text-mistral-black text-xl font-sans font-medium transition-all placeholder:text-mistral-black/10 shadow-sm focus:border-mistral-orange/20 focus:ring-8 focus:ring-mistral-orange/5"
              onChange={e => setAnswers({ ...answers, [q.id]: e.target.value })}
            />
          </div>
        ))}
      </div>

      <div className="flex justify-center">
        <button 
          onClick={onSubmit}
          disabled={isProcessing}
          className="bg-mistral-black text-white px-12 py-5 rounded-full font-bold font-sans text-xs uppercase tracking-[0.2em] hover:bg-mistral-orange transition-all shadow-xl active:scale-95 hover:scale-105 flex items-center gap-3"
        >
          {isProcessing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
          Initialize Strategy
        </button>
      </div>
    </motion.div>
  );
}
