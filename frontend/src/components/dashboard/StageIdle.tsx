"use client";

import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, ChevronDown, BookOpen, MessageSquare, Zap, Globe, Sparkles } from 'lucide-react';

interface StageIdleProps {
  topic: string;
  setTopic: (val: string) => void;
  researchMode: 'light' | 'deep' | 'optimise' | 'papers' | 'chat';
  setResearchMode: (mode: any) => void;
  onSubmit: (e: React.FormEvent) => void;
  onBrainstorm: (e: React.FormEvent) => void;
}

type Tab = 'research' | 'papers' | 'chat';

export default function StageIdle({ topic, setTopic, researchMode, setResearchMode, onSubmit, onBrainstorm }: StageIdleProps) {
  const [activeTab, setActiveTab] = useState<Tab>('chat');
  const [placeholder, setPlaceholder] = useState('');
  const [isModeOpen, setIsModeOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  
  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsModeOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const examples = {
    research: [
      "What are the long-term effects of microplastics on marine ecosystems?",
      "Analyze the efficacy of CRISPR in treating sickle cell anemia.",
      "Synthesize recent breakthroughs in solid-state battery technology.",
    ],
    papers: [
      "Deep Learning for protein folding",
      "Quantum computing error correction 2025",
      "Impact of LLMs on cognitive psychology",
    ],
    chat: [
      "Explain the latest findings in room-temperature superconductors",
      "Compare various carbon capture technologies",
      "Summarize the debate on AGI safety timelines",
    ]
  };

  const [exampleIndex, setExampleIndex] = useState(0);
  const [charIndex, setCharIndex] = useState(0);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    const currentExample = examples[activeTab][exampleIndex % examples[activeTab].length];
    const typeSpeed = isDeleting ? 30 : 60;
    
    const timer = setTimeout(() => {
      if (!isDeleting && charIndex < currentExample.length) {
        setPlaceholder(currentExample.substring(0, charIndex + 1));
        setCharIndex(charIndex + 1);
      } else if (isDeleting && charIndex > 0) {
        setPlaceholder(currentExample.substring(0, charIndex - 1));
        setCharIndex(charIndex - 1);
      } else if (!isDeleting && charIndex === currentExample.length) {
        setTimeout(() => setIsDeleting(true), 2000);
      } else if (isDeleting && charIndex === 0) {
        setIsDeleting(false);
        setExampleIndex((exampleIndex + 1));
      }
    }, typeSpeed);

    return () => clearTimeout(timer);
  }, [charIndex, isDeleting, exampleIndex, activeTab]);

  const modes = [
    { id: 'chat', label: 'General Chat', desc: 'Interactive brainstorming assistant' },
    { id: 'light', label: 'Light Research', desc: '15+ Sources. Rapid discovery' },
    { id: 'deep', label: 'Deep Probe (50+ Sources)', desc: 'Exhaustive multi-agent research' },
    { id: 'papers', label: 'Find Papers', desc: 'Direct academic search (V2)' }
  ];

  const currentModeLabel = modes.find(m => m.id === researchMode)?.label || 'Select Mode';

  return (
    <div className="min-h-[70vh] flex flex-col items-center justify-center py-10">
      <div className="w-full max-w-2xl space-y-8">
        {/* Logo & Headline */}
        <div className="text-center space-y-4 mb-4">
           <div className="flex justify-center mb-2">
             <div className="w-12 h-12 bg-mistral-black rounded-xl flex items-center justify-center shadow-lg shadow-black/5">
                <Globe className="w-6 h-6 text-mistral-orange" />
             </div>
           </div>
           <h1 className="text-4xl font-serif text-mistral-black tracking-tight leading-tight">
             How can I help with your <br />
             <span className="italic font-light text-mistral-orange">discovery today?</span>
           </h1>
        </div>

        {/* Action Tabs */}
        <div className="flex items-center justify-center gap-2 p-1 bg-[#F5F2ED] rounded-xl w-fit mx-auto border border-mistral-black/5">
          {[
            { id: 'chat', label: 'General Chat', icon: <MessageSquare className="w-3.5 h-3.5" /> },
            { id: 'research', label: 'Scientific Research', icon: <Zap className="w-3.5 h-3.5" /> },
            { id: 'papers', label: 'Find Papers', icon: <BookOpen className="w-3.5 h-3.5" /> },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => {
                setActiveTab(tab.id as Tab);
                setCharIndex(0);
                setIsDeleting(false);
                // Sync mode with tab
                if (tab.id === 'papers') setResearchMode('papers');
                else if (tab.id === 'chat') setResearchMode('chat');
                else if (researchMode === 'papers' || researchMode === 'chat') setResearchMode('deep');
              }}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-[10px] font-bold uppercase tracking-widest transition-all ${
                activeTab === tab.id 
                  ? 'bg-white text-mistral-black shadow-sm' 
                  : 'text-mistral-black/40 hover:text-mistral-black'
              }`}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </div>

        {/* Search Bar */}
        <div className="relative group">
          <form 
            onSubmit={(e) => {
              if (activeTab === 'research') onSubmit(e);
              else if (activeTab === 'chat') onBrainstorm(e);
            }} 
            className="relative z-10"
          >
            <div className="flex flex-col border border-mistral-black/10 bg-white shadow-xl shadow-black/[0.02] rounded-2xl focus-within:border-mistral-orange/30 transition-all duration-300">
              <div className="flex items-start px-6 py-8 min-h-[160px]">
                <Search className="w-5 h-5 text-mistral-black/20 mr-4 mt-1" />
                <div className="flex-1 relative">
                  <input 
                    type="text" 
                    value={topic}
                    onChange={e => setTopic(e.target.value)}
                    placeholder={topic ? "" : placeholder}
                    disabled={activeTab === 'papers'}
                    className="w-full bg-transparent focus:outline-none text-lg font-sans text-mistral-black placeholder:text-mistral-black/20"
                  />
                  {!topic && activeTab !== 'papers' && (
                    <span className="absolute left-0 top-1.5 w-0.5 h-6 bg-mistral-orange/40 animate-pulse pointer-events-none" />
                  )}
                  {activeTab === 'papers' && (
                    <div className="absolute inset-0 flex items-start pt-1">
                      <span className="text-xs font-bold uppercase tracking-widest text-mistral-orange/60 bg-mistral-orange/5 px-3 py-1 rounded-full">Coming Soon in V2</span>
                    </div>
                  )}
                </div>
              </div>
              
              <div className="flex items-center justify-between px-4 py-3 bg-[#F9F8F6] border-t border-mistral-black/[0.03] rounded-b-2xl">
                <div className="flex items-center gap-2">
                  <div className="relative" ref={dropdownRef}>
                    <button
                      type="button"
                      onClick={() => setIsModeOpen(!isModeOpen)}
                      className="flex items-center gap-3 bg-white border-2 border-mistral-black rounded-lg pl-3 pr-8 py-1.5 text-[10px] font-bold uppercase tracking-widest text-mistral-black hover:border-mistral-orange transition-all cursor-pointer shadow-sm min-w-[200px] text-left"
                    >
                      {currentModeLabel}
                      <ChevronDown className={`absolute right-2 top-1/2 -translate-y-1/2 w-3 h-3 text-mistral-black transition-transform ${isModeOpen ? 'rotate-180' : ''}`} />
                    </button>

                    <AnimatePresence>
                      {isModeOpen && (
                        <motion.div
                          initial={{ opacity: 0, y: 10, scale: 0.95 }}
                          animate={{ opacity: 1, y: 0, scale: 1 }}
                          exit={{ opacity: 0, y: 10, scale: 0.95 }}
                          className="absolute bottom-full mb-2 left-0 w-64 bg-white border border-mistral-black/10 shadow-2xl rounded-xl overflow-hidden z-50 p-1"
                        >
                          {modes.map((mode) => (
                            <button
                              key={mode.id}
                              type="button"
                              onClick={() => {
                                setResearchMode(mode.id as any);
                                setIsModeOpen(false);
                                // Sync tab if they select chat
                                if (mode.id === 'chat') setActiveTab('chat');
                                else setActiveTab('research');
                              }}
                              className={`w-full text-left p-3 rounded-lg transition-all ${
                                researchMode === mode.id 
                                  ? 'bg-mistral-orange/5 text-mistral-black' 
                                  : 'hover:bg-[#F9F8F6] text-mistral-black/50'
                              }`}
                            >
                              <div className="text-[10px] font-bold uppercase tracking-widest">{mode.label}</div>
                              <div className="text-[9px] mt-1 opacity-60 leading-tight">{mode.desc}</div>
                            </button>
                          ))}
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                  
                  <div className="flex items-center gap-1.5 px-3 py-1.5 bg-mistral-orange/5 rounded-lg border border-mistral-orange/10">
                    <div className="w-1.5 h-1.5 rounded-full bg-mistral-orange animate-pulse" />
                    <span className="text-[9px] font-bold text-mistral-orange uppercase tracking-widest">Autonomous Agent v1.0</span>
                  </div>
                </div>

                <button 
                  type="submit" 
                  disabled={activeTab === 'papers' || !topic.trim()}
                  className="bg-mistral-black text-white px-8 py-2 rounded-lg text-[10px] font-black uppercase tracking-widest hover:bg-mistral-orange active:scale-95 transition-all shadow-lg shadow-black/5 disabled:opacity-30 disabled:grayscale"
                >
                  {activeTab === 'chat' ? 'Start General' : 'Run Discovery'}
                </button>
              </div>
            </div>
          </form>
          {/* Shadow decoration */}
          <div className="absolute -inset-1 bg-gradient-to-r from-mistral-orange/10 to-transparent blur-2xl opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none -z-10" />
        </div>

        {/* Feature Hints */}
        <div className="grid grid-cols-3 gap-6 pt-4">
           <div className="space-y-2">
              <div className="text-[9px] font-black text-mistral-black/30 uppercase tracking-[0.2em]">Verified Sources</div>
              <p className="text-[10px] text-mistral-black/50 leading-relaxed">Direct integration with arXiv, OpenAlex, and CORE API stacks.</p>
           </div>
           <div className="space-y-2">
              <div className="text-[9px] font-black text-mistral-black/30 uppercase tracking-[0.2em]">Sovereign Memory</div>
              <p className="text-[10px] text-mistral-black/50 leading-relaxed">Synthesis includes your private PDF library automatically.</p>
           </div>
           <div className="space-y-2">
              <div className="text-[9px] font-black text-mistral-black/30 uppercase tracking-[0.2em]">IEEE Adherence</div>
              <p className="text-[10px] text-mistral-black/50 leading-relaxed">Outputs formatted manuscripts with full citation verification.</p>
           </div>
        </div>
      </div>
    </div>
  );
}
