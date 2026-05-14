"use client";

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { Sparkles, Zap, FileText, LogOut, User as UserIcon, Home, Clock, History, Plus } from 'lucide-react';
import { supabase } from '@/lib/supabaseClient';
import { useRouter } from 'next/navigation';
import { getSessions } from '@/lib/api';

interface SidebarProps {
  onNewResearch: () => void;
  onOpenLibrary: () => void;
  isLibraryOpen: boolean;
}

export default function Sidebar({ onNewResearch, onOpenLibrary, isLibraryOpen }: SidebarProps) {
  const [user, setUser] = useState<any>(null);
  const [sessions, setSessions] = useState<any[]>([]);
  const router = useRouter();

  useEffect(() => {
    supabase.auth.getUser().then(({ data: { user } }) => {
      setUser(user);
      if (user) fetchSessions();
    });
  }, []);

  const fetchSessions = async () => {
    try {
      const data = await getSessions();
      setSessions(data);
    } catch (err) {
      console.error("Failed to fetch sessions", err);
    }
  };

  const handleSignOut = async () => {
    await supabase.auth.signOut();
    router.push('/');
  };

  const getInitials = () => {
    if (!user?.email) return '??';
    const email = user.email;
    return email.substring(0, 2).toUpperCase();
  };

  return (
    <aside className="w-64 border-r border-mistral-black/5 bg-white flex flex-col z-20 overflow-hidden">
      <div className="p-6">
        <Link href="/" className="flex items-center gap-2 text-mistral-black font-mono text-lg font-black uppercase tracking-tighter">
          <img src="/logo.png" alt="Lume Logo" className="w-10 h-10 object-contain" />
          <span>Lume.ai</span>
        </Link>
      </div>

      <div className="px-4 mb-8">
        <button 
          onClick={onNewResearch}
          className="w-full flex items-center justify-center gap-2 bg-mistral-black text-white py-3 rounded-xl hover:bg-mistral-orange transition-all active:scale-[0.98] shadow-lg shadow-black/5 text-[11px] font-black uppercase tracking-widest"
        >
          <Plus className="w-4 h-4" />
          New Research
        </button>
      </div>

      <nav className="flex-1 overflow-y-auto custom-scrollbar px-4 space-y-8">
        <div className="space-y-1">
          <div className="px-3 text-[9px] font-black text-mistral-black/20 uppercase tracking-[0.2em] mb-2">Protocol</div>
          <button 
            onClick={onNewResearch}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-mistral-black/60 hover:bg-[#F5F2ED] hover:text-mistral-black transition-all text-[11px] font-bold"
          >
            <Home className="w-4 h-4" />
            Workbench
          </button>
          <button 
            onClick={onOpenLibrary}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all text-[11px] font-bold ${
              isLibraryOpen 
                ? 'bg-mistral-orange/5 text-mistral-orange' 
                : 'text-mistral-black/60 hover:bg-[#F5F2ED] hover:text-mistral-black'
            }`}
          >
            <FileText className="w-4 h-4" />
            Private Library
          </button>
        </div>

        <div className="space-y-1">
          <div className="px-3 text-[9px] font-black text-mistral-black/20 uppercase tracking-[0.2em] mb-2 flex items-center justify-between">
            History
            <History className="w-3 h-3" />
          </div>
          <div className="space-y-0.5">
            {sessions.length === 0 ? (
              <div className="px-3 py-4 text-[10px] text-mistral-black/30 italic">No recent sessions</div>
            ) : (
              sessions.slice(0, 8).map((session) => (
                <button 
                  key={session.thread_id}
                  className="w-full text-left px-3 py-2 rounded-lg text-mistral-black/50 hover:bg-[#F5F2ED] hover:text-mistral-black transition-all truncate text-[11px] font-medium"
                >
                  {session.topic}
                </button>
              ))
            )}
          </div>
        </div>
      </nav>

      <div className="p-4 mt-auto border-t border-mistral-black/5 bg-[#F9F8F6]">
        <div className="flex items-center gap-3">
          <div 
            title={user?.email}
            className="w-9 h-9 bg-mistral-black text-white rounded-lg flex items-center justify-center text-[10px] font-black uppercase tracking-widest shadow-sm"
          >
            {getInitials()}
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-[11px] font-black text-mistral-black truncate">{user?.email?.split('@')[0]}</div>
            <div className="text-[9px] text-mistral-black/40 font-bold uppercase tracking-tighter">Pro Researcher</div>
          </div>
          <button 
            onClick={handleSignOut}
            className="p-2 text-mistral-black/20 hover:text-mistral-orange transition-colors"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </aside>
  );
}
