"use client";

import React from 'react';
import { motion } from 'framer-motion';
import { Database, Loader2, ArrowRight, BookOpen } from 'lucide-react';

interface StageReviewProps {
  summary: string;
  chatHistory: { role: 'user' | 'assistant'; text: string }[];
  chatQuery: string;
  setChatQuery: (val: string) => void;
  onChatSubmit: () => void;
  onGeneratePaper: () => void;
  isProcessing: boolean;
}

export default function StageReview({ summary, chatHistory, chatQuery, setChatQuery, onChatSubmit, onGeneratePaper, isProcessing }: StageReviewProps) {
  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-12 py-8 max-w-4xl mx-auto px-4">
      <div className="space-y-4 border-b border-mistral-black/5 pb-10">
        <h2 className="text-3xl font-serif text-mistral-black tracking-tight font-medium uppercase tracking-widest">Synthesis <span className="text-mistral-orange italic font-light">Analysis</span></h2>
        <p className="text-mistral-black/30 font-mono text-[9px] uppercase tracking-[0.4em]">Corpus extraction complete / interactive interrogation active</p>
      </div>

      <div className="grid md:grid-cols-1 gap-10">
        <div className="bg-white border border-mistral-black/5 p-10 space-y-8">
          <div className="flex items-center gap-3">
            <div className="w-1.5 h-6 bg-mistral-orange" />
            <h3 className="text-[10px] font-bold font-mono text-mistral-black uppercase tracking-widest">Executive Abstract</h3>
          </div>
          <p className="text-mistral-black/80 leading-relaxed font-serif text-lg italic">{summary}</p>
        </div>
        
        <div className="bg-white border border-mistral-black/5 p-10 space-y-8">
          <div className="flex items-center justify-between border-b border-mistral-black/5 pb-6">
            <h3 className="text-[10px] font-bold font-mono text-mistral-black uppercase tracking-widest flex items-center gap-2">
              <Database className="w-3.5 h-3.5 text-mistral-orange" />
              Source Interrogation
            </h3>
          </div>

          <div className="h-[25rem] overflow-y-auto pr-4 space-y-8 custom-scrollbar">
            {chatHistory.length === 0 && (
              <div className="h-full flex flex-col items-center justify-center text-mistral-black/10 font-bold font-sans text-xs space-y-4 opacity-40 uppercase tracking-[0.2em]">
                 <BookOpen className="w-12 h-12 opacity-20" />
                 <span>Waiting for inquiry...</span>
              </div>
            )}
            {chatHistory.map((msg, i) => (
              <div key={i} className={`flex flex-col gap-2 ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                <div className={`p-5 max-w-[90%] text-base font-sans leading-relaxed ${msg.role === 'user' ? 'bg-mistral-black text-white' : 'bg-[#F5F2ED] text-mistral-black border border-mistral-black/5'}`}>
                  {msg.text}
                </div>
                <div className="px-2 text-[8px] font-bold font-mono text-mistral-black/20 uppercase tracking-widest">
                  {msg.role === 'user' ? 'Investigator' : 'Lume Assistant'}
                </div>
              </div>
            ))}
          </div>
          
          <div className="relative">
            <input 
              type="text" 
              disabled={isProcessing}
              value={chatQuery}
              onChange={(e) => setChatQuery(e.target.value)}
              onKeyDown={async (e) => {
                if (e.key === 'Enter') onChatSubmit();
              }}
              className="w-full pl-6 pr-20 py-4 border border-mistral-black/10 focus:border-mistral-orange/30 focus:outline-none bg-white font-sans text-base text-mistral-black placeholder:text-mistral-black/20"
              placeholder="Query the research corpus..."
            />
            <button onClick={onChatSubmit} disabled={isProcessing || !chatQuery.trim()} className="absolute right-2 top-1/2 -translate-y-1/2 bg-mistral-black text-white p-2.5 hover:bg-mistral-orange transition-all">
              {isProcessing ? <Loader2 className="w-4 h-4 animate-spin"/> : <ArrowRight className="w-4 h-4"/>}
            </button>
          </div>
        </div>
      </div>

      <div className="flex justify-center pt-8">
        <button 
          onClick={onGeneratePaper}
          disabled={isProcessing}
          className="bg-mistral-black text-white px-10 py-4 font-bold font-sans text-xs uppercase tracking-[0.2em] hover:bg-mistral-orange transition-all shadow-sm"
        >
          Draft Technical Manuscript
        </button>
      </div>
    </motion.div>
  );
}
