"use client";

import React from 'react';
import { Sparkles } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="py-16 border-t border-mistral-black/5 bg-mistral-beige px-6">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-8 font-sans text-[11px] text-mistral-black/40">
        <div className="flex items-center gap-1 text-mistral-black text-2xl font-black uppercase tracking-tighter">
          <img src="/logo.png" alt="Lume Logo" className="w-12 h-12 object-contain" />
          <span>Lume.ai</span>
        </div>
        <div className="flex gap-12 font-bold uppercase tracking-widest">
          <a href="#" className="hover:text-mistral-orange transition-colors">Privacy</a>
          <a href="#" className="hover:text-mistral-orange transition-colors">Terms</a>
          <a href="#" className="hover:text-mistral-orange transition-colors">Twitter / X</a>
        </div>
        <div className="uppercase tracking-[0.4em]">
          © 2026 LUME • ALL RIGHTS RESERVED
        </div>
      </div>
    </footer>
  );
}
