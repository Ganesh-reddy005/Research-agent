"use client";

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { Search, Database, MessageSquare, FileText, ArrowRight, LayoutDashboard } from 'lucide-react';
import { supabase } from '@/lib/supabaseClient';

export default function Hero() {
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? null);
    });
  }, []);

  return (
    <section className="relative h-screen min-h-[700px] flex items-center px-6 overflow-hidden">
      {/* Subtle Background Image with Professional Fade */}
      <div className="absolute inset-0 z-0">
        <img 
          src="/hero_img.png" 
          alt="Background" 
          className="w-full h-full object-cover grayscale-[0.5] opacity-70"
        />
        <div className="absolute inset-0 bg-gradient-to-r from-mistral-beige via-mistral-beige/95 to-transparent w-full md:w-3/4" />
      </div>

      <div className="max-w-7xl mx-auto w-full relative z-10">
        <div className="max-w-3xl space-y-10">
          <div className="space-y-4">
            <motion.h1 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8 }}
              className="text-5xl md:text-8xl font-serif text-mistral-black leading-[1.05] tracking-tight"
            >
              Autonomous <br />
              <span className="italic font-light text-mistral-orange">Scientific Research.</span>
            </motion.h1>
            
            <motion.p 
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="max-w-xl text-lg md:text-xl text-mistral-black/60 font-sans leading-relaxed"
            >
              Lume is a complete research agent that finds, reads, and synthesizes 100s of real papers into verified IEEE manuscripts.
            </motion.p>
          </div>
          
          <motion.div 
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="flex flex-col sm:flex-row items-center gap-6 pt-2"
          >
            <Link 
              href="/dashboard" 
              className="bg-mistral-black text-white text-base py-3.5 px-10 rounded-lg hover:bg-mistral-orange transition-all font-bold shadow-lg shadow-black/5 flex items-center gap-3"
            >
              {user ? (
                <>
                  <LayoutDashboard className="w-5 h-5" />
                  Resume Researching
                </>
              ) : (
                'Start Researching'
              )}
            </Link>
            <div className="flex items-center gap-3 font-mono text-[10px] text-mistral-black/40 uppercase tracking-widest font-bold">
              <div className="flex -space-x-2">
                {[1,2,3].map(i => <div key={i} className="w-6 h-6 rounded-full border-2 border-mistral-beige bg-mistral-black/10" />)}
              </div>
              <span>Trusted by 10k+ Researchers</span>
            </div>
          </motion.div>

          {/* Simplified Action Preview */}
          <motion.div 
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5, duration: 1 }}
            className="pt-12 grid grid-cols-1 md:grid-cols-4 gap-4 max-w-4xl"
          >
            {[
              { label: "Find Papers", icon: <Search className="w-3.5 h-3.5" /> },
              { label: "Extract Data", icon: <Database className="w-3.5 h-3.5" /> },
              { label: "Talk to Sources", icon: <MessageSquare className="w-3.5 h-3.5" /> },
              { label: "Draft IEEE Paper", icon: <FileText className="w-3.5 h-3.5" /> }
            ].map((item, i) => (
              <div key={i} className="flex items-center gap-3 p-3 bg-white/50 backdrop-blur-sm border border-mistral-black/5 rounded-xl text-[11px] font-bold text-mistral-black/70">
                <div className="w-6 h-6 rounded-full bg-mistral-orange text-white flex items-center justify-center">
                  {item.icon}
                </div>
                {item.label}
              </div>
            ))}
          </motion.div>
        </div>
      </div>
    </section>
  );
}
