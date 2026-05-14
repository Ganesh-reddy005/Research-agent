"use client";

import React, { useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { MessageSquare, Loader2, ArrowRight, BrainCircuit, User } from 'lucide-react';

interface StageBrainstormProps {
  chatHistory: { role: 'user' | 'assistant'; content: string }[];
  chatQuery: string;
  setChatQuery: (val: string) => void;
  onChatSubmit: () => void;
  isProcessing: boolean;
}

export default function StageBrainstorm({ chatHistory, chatQuery, setChatQuery, onChatSubmit, isProcessing }: StageBrainstormProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [chatHistory]);

  useEffect(() => {
    if (!isProcessing && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isProcessing]);

  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }} 
      animate={{ opacity: 1, y: 0 }} 
      className="max-w-3xl mx-auto w-full flex flex-col h-[calc(100vh-120px)]"
    >
      {/* Minimal Header */}
      <div className="flex items-center justify-between py-6 border-b border-mistral-black/5">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-mistral-black rounded-lg flex items-center justify-center text-mistral-orange shadow-sm">
            <BrainCircuit className="w-5 h-5" />
          </div>
          <h2 className="text-sm font-bold uppercase tracking-widest text-mistral-black">General Assistant</h2>
        </div>
        <div className="text-[10px] font-bold text-mistral-black/30 uppercase tracking-widest">Streaming active</div>
      </div>

      {/* ChatGPT Style Chat Area */}
      <div 
        ref={scrollRef}
        className="flex-1 overflow-y-auto py-10 space-y-8 custom-scrollbar"
      >
        {chatHistory.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center text-center space-y-4 opacity-30 py-20">
             <div className="w-12 h-12 bg-[#F5F2ED] rounded-full flex items-center justify-center">
                <MessageSquare className="w-6 h-6" />
             </div>
             <p className="text-[11px] font-bold uppercase tracking-widest text-mistral-black">How can I help you today?</p>
          </div>
        )}

        {chatHistory.map((msg, i) => (
          <motion.div 
            key={i} 
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            className={`flex gap-6 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div className={`flex max-w-[85%] gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
              <div className={`w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center border ${
                msg.role === 'user' 
                  ? 'bg-white border-mistral-black/10 text-mistral-black/40' 
                  : 'bg-mistral-black border-mistral-black text-mistral-orange'
              }`}>
                {msg.role === 'user' ? <User className="w-4 h-4" /> : <BrainCircuit className="w-4 h-4" />}
              </div>
              <div className={`p-5 rounded-2xl text-[15px] font-sans leading-relaxed transition-all ${
                msg.role === 'user' 
                  ? 'bg-mistral-black text-white' 
                  : 'bg-[#F9F8F6] text-mistral-black border border-mistral-black/5'
              }`}>
                {msg.content || (isProcessing && i === chatHistory.length - 1 ? <span className="inline-block w-1.5 h-4 bg-mistral-orange/40 animate-pulse ml-1" /> : null)}
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Pinned Input Area */}
      <div className="py-6 border-t border-mistral-black/5">
        <div className="relative group max-w-2xl mx-auto">
          <input 
            ref={inputRef}
            type="text" 
            disabled={isProcessing}
            value={chatQuery}
            onChange={(e) => setChatQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                onChatSubmit();
              }
            }}
            className="w-full pl-6 pr-14 py-4 bg-white border border-mistral-black/10 rounded-2xl focus:border-mistral-orange/30 focus:outline-none font-sans text-[15px] text-mistral-black placeholder:text-mistral-black/20 transition-all shadow-sm"
            placeholder="Send a message..."
          />
          <button 
            onClick={onChatSubmit} 
            disabled={isProcessing || !chatQuery.trim()} 
            className="absolute right-2 top-1/2 -translate-y-1/2 bg-mistral-black text-white w-10 h-10 rounded-xl flex items-center justify-center hover:bg-mistral-orange active:scale-95 transition-all shadow-lg disabled:opacity-30"
          >
            {isProcessing ? <Loader2 className="w-4 h-4 animate-spin"/> : <ArrowRight className="w-4 h-4"/>}
          </button>
        </div>
        <p className="mt-3 text-center text-[9px] text-mistral-black/20 font-bold uppercase tracking-widest">
          Autonomous Brainstorming Protocol // v1.0
        </p>
      </div>
    </motion.div>
  );
}
