"use client";

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import AuthModal from './AuthModal';
import { supabase } from '@/lib/supabaseClient';
import { User, LogOut, LayoutDashboard } from 'lucide-react';

export default function Navbar() {
  const [isAuthOpen, setIsAuthOpen] = useState(false);
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? null);
    });

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null);
    });

    return () => subscription.unsubscribe();
  }, []);

  const handleSignOut = async () => {
    await supabase.auth.signOut();
  };

  return (
    <>
    <nav className="fixed top-0 w-full z-50 border-b border-mistral-black/10 bg-mistral-beige/80 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-1 text-mistral-black font-mono text-xl font-black uppercase tracking-tighter">
          <img src="/logo.png" alt="Lume Logo" className="w-20 h-20 object-contain" />
          <span>Lume.ai</span>
        </Link>
        <div className="hidden md:flex items-center gap-8 font-mono text-[10px] font-bold uppercase tracking-widest text-mistral-black/60">
          <a href="#how-it-works" className="hover:text-mistral-orange transition-colors">How it works</a>
          <a href="#features" className="hover:text-mistral-orange transition-colors">Capabilities</a>
          
          {user ? (
            <div className="flex items-center gap-4">
              <Link 
                href="/dashboard"
                className="flex items-center gap-2 bg-mistral-black text-white py-2 px-5 text-[9px] hover:bg-mistral-orange transition-all font-bold uppercase tracking-widest"
              >
                <LayoutDashboard className="w-3 h-3" />
                Go to Dashboard
              </Link>
              <button 
                onClick={handleSignOut}
                title="Sign Out"
                className="p-2 hover:text-mistral-orange transition-colors border border-mistral-black/5 bg-white"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <button 
              onClick={() => setIsAuthOpen(true)}
              className="bg-mistral-black text-white py-2 px-5 text-[9px] hover:bg-mistral-orange transition-all font-bold uppercase tracking-widest"
            >
              Sign in
            </button>
          )}
        </div>
      </div>
    </nav>
    <AuthModal isOpen={isAuthOpen} onClose={() => setIsAuthOpen(false)} />
    </>
  );
}
