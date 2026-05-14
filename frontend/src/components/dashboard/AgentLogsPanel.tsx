"use client";

import React, { useRef, useEffect } from 'react';
import { Activity, ChevronDown, ChevronUp, FileSearch, Layers, Search, Database, Cpu, Book, CheckCircle, Sparkles, ShieldCheck, Zap } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface AgentLogsPanelProps {
  logs: any[];
  activeThought: { agent: string; text: string } | null;
  isProcessing: boolean;
  expandedLog: number | null;
  setExpandedLog: (index: number | null) => void;
  onClose?: () => void;
}

const getAgentIcon = (name: string) => {
  switch (name.toLowerCase()) {
    case 'clarification': return <FileSearch className="w-4 h-4" />;
    case 'planning': return <Layers className="w-4 h-4" />;
    case 'retriever': return <Search className="w-4 h-4" />;
    case 'indexer': return <Database className="w-4 h-4" />;
    case 'synthesis': return <Cpu className="w-4 h-4" />;
    case 'writer': return <Book className="w-4 h-4" />;
    case 'critic': return <CheckCircle className="w-4 h-4" />;
    case 'refinement': return <Sparkles className="w-4 h-4" />;
    case 'auditor': return <ShieldCheck className="w-4 h-4" />;
    default: return <Activity className="w-4 h-4" />;
  }
};

export default function AgentLogsPanel({ logs, activeThought, isProcessing, expandedLog, setExpandedLog, onClose }: AgentLogsPanelProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs, activeThought]);

  return (
    <aside className="w-80 h-full border-l border-mistral-border/50 bg-[#F5F2ED] flex flex-col z-20 shadow-2xl">
      <div className="px-6 py-6 border-b border-mistral-border/50 flex items-center justify-between bg-white/80 backdrop-blur-xl">
        <div className="text-[10px] font-bold text-mistral-black uppercase tracking-[0.2em] font-mono flex items-center gap-2.5">
          <Activity className="w-3.5 h-3.5 text-mistral-orange" />
          Neural Activity
        </div>
        <div className="flex items-center gap-3">
          {isProcessing && (
            <div className="flex gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-mistral-orange animate-pulse" />
              <span className="w-1.5 h-1.5 rounded-full bg-mistral-orange animate-pulse [animation-delay:0.2s]" />
            </div>
          )}
          {onClose && (
            <button onClick={onClose} className="p-1 hover:bg-mistral-beige rounded-md transition-colors">
              <ChevronDown className="w-4 h-4 rotate-270 text-mistral-black/40" />
            </button>
          )}
        </div>
      </div>
      
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-6 space-y-4 custom-scrollbar bg-mistral-beige/10">
        {activeThought && (
          <motion.div 
            initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
            className="p-5 bg-white border border-mistral-orange/20 shadow-sm rounded-2xl relative overflow-hidden"
          >
            <div className="absolute top-0 left-0 w-1 h-full bg-mistral-orange" />
            <div className="flex items-center gap-2 mb-3">
              <div className="text-mistral-orange">{getAgentIcon(activeThought.agent)}</div>
              <div className="text-[9px] font-bold font-mono uppercase tracking-[0.2em] text-mistral-black/40">{activeThought.agent} working...</div>
            </div>
            <div className="text-[11px] font-mono leading-relaxed text-mistral-black/80 break-words">
              {activeThought.text}
              <span className="inline-block w-1 h-3 bg-mistral-orange ml-1 animate-pulse" />
            </div>
          </motion.div>
        )}

        {logs.map((log, i) => (
          <div key={i} className="space-y-0">
            <button 
              onClick={() => setExpandedLog(expandedLog === i ? null : i)}
              className={`w-full text-left p-4 bg-white border border-mistral-border/30 hover:border-mistral-orange/20 transition-all flex items-center justify-between group shadow-sm active:scale-[0.99] ${expandedLog === i ? 'rounded-t-xl border-b-0' : 'rounded-xl'}`}
            >
              <div className="flex items-center gap-3">
                <div className={`text-mistral-black/40 group-hover:text-mistral-orange transition-colors`}>
                  {getAgentIcon(log.step)}
                </div>
                <div>
                  <div className="text-[8px] font-bold font-mono text-mistral-black/30 uppercase tracking-widest mb-0.5">{log.timestamp}</div>
                  <div className="text-[10px] font-bold font-sans tracking-tight text-mistral-black/70">{log.step}</div>
                </div>
              </div>
              {expandedLog === i ? <ChevronUp className="w-3 h-3 text-mistral-black/20" /> : <ChevronDown className="w-3 h-3 text-mistral-black/20" />}
            </button>
            
            <AnimatePresence>
              {expandedLog === i && (
                <motion.div 
                  initial={{ height: 0 }} animate={{ height: 'auto' }} exit={{ height: 0 }}
                  className="overflow-hidden bg-white/50 border-x border-b border-mistral-border/30 rounded-b-xl"
                >
                  <pre className="p-4 text-[9px] text-mistral-black/60 overflow-y-auto whitespace-pre-wrap break-words font-mono leading-relaxed max-h-48 bg-[#F5F2ED]/30">
                    {JSON.stringify(log.data, null, 2)}
                  </pre>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        ))}

        {logs.length === 0 && !activeThought && (
          <div className="h-full flex flex-col items-center justify-center opacity-20 text-center space-y-4 mt-12">
            <Zap className="w-8 h-8 text-mistral-black" />
            <div className="text-[9px] uppercase font-bold font-sans tracking-[0.2em] text-mistral-black">Standby</div>
          </div>
        )}
      </div>
    </aside>
  );
}
