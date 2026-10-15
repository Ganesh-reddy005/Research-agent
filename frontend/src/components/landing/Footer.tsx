"use client";

import React from 'react';

export default function Footer() {
  return (
    <footer className="py-14 border-t border-mistral-black/10 bg-mistral-beige px-4 sm:px-6">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-8 text-[11px] text-mistral-black/45">
        <div className="flex flex-col items-center md:items-start gap-1">
          <div className="flex items-center gap-1 text-mistral-black text-2xl font-black uppercase tracking-tighter">
            <img src="/logo.png" alt="" className="w-12 h-12 object-contain" />
            <span>Lume.ai</span>
          </div>
          <span className="font-mono uppercase tracking-widest text-[10px]">Autonomous research for computer science</span>
        </div>
        <div className="flex gap-10 font-mono font-bold uppercase tracking-widest">
          <a href="#" className="hover:text-mistral-orange transition-colors">Privacy</a>
          <a href="#" className="hover:text-mistral-orange transition-colors">Terms</a>
          <a href="#" className="hover:text-mistral-orange transition-colors">Twitter / X</a>
        </div>
        <div className="font-mono uppercase tracking-[0.3em]">© 2026 Lume</div>
      </div>
    </footer>
  );
}
