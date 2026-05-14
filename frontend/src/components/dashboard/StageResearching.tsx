"use client";

import React from 'react';
import { motion } from 'framer-motion';
import { Loader2, CheckCircle, Activity, Zap } from 'lucide-react';

interface StageResearchingProps {
  activeThought: { agent: string; text: string } | null;
}

export default function StageResearching({ activeThought }: StageResearchingProps) {
  const steps = [
    { label: 'Discover', agents: ['clarification', 'planning'] },
    { label: 'Collect', agents: ['retriever', 'indexer'] },
    { label: 'Analyze', agents: ['synthesis', 'critic', 'refinement'] },
    { label: 'Draft', agents: ['writer', 'auditor'] }
  ];

  const currentStepIndex = steps.findIndex(s => s.agents.includes(activeThought?.agent.toLowerCase() || '')) || 0;

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-12 py-8 max-w-3xl mx-auto px-4">
      {/* Professional Linear Stepper (Sharp) */}
      <div className="flex justify-between items-center w-full px-2 border-b border-mistral-black/5 pb-10">
        {steps.map((step, i) => {
          const isActive = i === currentStepIndex;
          const isCompleted = i < currentStepIndex;
          return (
            <div key={step.label} className="flex items-center gap-3">
              <div className={`text-[10px] font-bold uppercase tracking-widest font-mono ${isActive ? 'text-mistral-orange' : isCompleted ? 'text-mistral-black' : 'text-mistral-black/20'}`}>
                {String(i + 1).padStart(2, '0')}. {step.label}
              </div>
              {i < steps.length - 1 && <div className="w-8 h-px bg-mistral-black/5" />}
            </div>
          );
        })}
      </div>

      <div className="space-y-8">
        <div className="flex items-center gap-5 p-6 bg-white border border-mistral-black/5 shadow-sm">
          <div className="w-1.5 h-8 bg-mistral-orange" />
          <div className="flex-1">
            <div className="text-[9px] font-bold font-mono text-mistral-black/30 uppercase tracking-widest mb-0.5">Active Protocol</div>
            <div className="text-xl font-sans text-mistral-black tracking-tight font-medium uppercase">{activeThought?.agent || 'System'} Execution</div>
          </div>
          <Loader2 className="w-5 h-5 text-mistral-orange animate-spin" />
        </div>

        <div className="p-10 min-h-[35vh] bg-[#F5F2ED]/30 border border-mistral-black/5 relative overflow-hidden group">
          <div className="font-sans">
            <div className="text-[9px] font-bold font-mono text-mistral-black/10 uppercase tracking-[0.3em] mb-12 flex items-center gap-3">
              <Activity className="w-3.5 h-3.5" />
              Intelligence Stream
            </div>
            
            {activeThought ? (
              <div className="text-mistral-black leading-relaxed text-lg font-serif italic max-w-2xl">
                "{activeThought.text}"
                <span className="inline-block w-1.5 h-5 bg-mistral-orange/30 ml-2 animate-pulse align-middle" />
              </div>
            ) : (
              <div className="h-full flex flex-col items-center justify-center py-20 opacity-10 font-bold font-sans text-sm space-y-4">
                <Zap className="w-6 h-6" />
                <span className="tracking-widest uppercase">Initializing neural nodes...</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  );
}
