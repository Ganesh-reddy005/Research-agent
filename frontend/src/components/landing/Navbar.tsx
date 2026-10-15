"use client";

import React from 'react';
import Link from 'next/link';
import type { User } from '@supabase/supabase-js';
import { supabase } from '@/lib/supabaseClient';
import { LogOut, LayoutDashboard } from 'lucide-react';

const LINKS = [
  { href: '#how-it-works', label: 'How it works' },
  { href: '#experiments', label: 'Experiments' },
  { href: '#verification', label: 'Verification' },
  { href: '#faq', label: 'FAQ' },
];

export default function Navbar({ user, onSignIn }: { user: User | null; onSignIn: () => void }) {
  return (
    <nav className="fixed top-0 w-full z-50 border-b border-mistral-black/10 bg-mistral-beige/85 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-1 text-mistral-black font-mono text-xl font-black uppercase tracking-tighter">
          <img src="/logo.png" alt="" className="w-16 h-16 sm:w-20 sm:h-20 object-contain" />
          <span>Lume AI</span>
        </Link>
        <div className="flex items-center gap-8 font-mono text-[10px] font-bold uppercase tracking-widest text-mistral-black/60">
          {LINKS.map(l => (
            <a key={l.href} href={l.href} className="hidden md:inline hover:text-mistral-orange transition-colors">
              {l.label}
            </a>
          ))}

          {user ? (
            <div className="flex items-center gap-2 sm:gap-4">
              <Link
                href="/dashboard"
                className="flex items-center gap-2 bg-mistral-black text-white py-2 px-4 sm:px-5 text-[9px] hover:bg-mistral-orange transition-colors font-bold uppercase tracking-widest"
              >
                <LayoutDashboard className="w-3 h-3" />
                Workspace
              </Link>
              <button
                onClick={() => supabase.auth.signOut()}
                title="Sign out"
                aria-label="Sign out"
                className="p-2 hover:text-mistral-orange transition-colors border border-mistral-black/10 bg-white"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <button
              onClick={onSignIn}
              className="bg-mistral-black text-white py-2 px-5 text-[9px] hover:bg-mistral-orange transition-colors font-bold uppercase tracking-widest"
            >
              Sign in
            </button>
          )}
        </div>
      </div>
    </nav>
  );
}
