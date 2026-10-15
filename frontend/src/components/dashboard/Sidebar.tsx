"use client";

import React from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import type { User } from '@supabase/supabase-js';
import { Plus, Library, LogOut, X } from 'lucide-react';
import { supabase } from '@/lib/supabaseClient';
import type { SessionSummary } from '@/lib/types';

function formatDate(iso: string) {
  const date = new Date(iso);
  const days = Math.floor((Date.now() - date.getTime()) / 86_400_000);
  if (days < 1 && new Date().getDate() === date.getDate()) return 'Today';
  if (days < 2) return 'Yesterday';
  return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

export default function Sidebar({
  user, sessions, activeThreadId, onSelectSession, onNewResearch, onOpenLibrary, isLibraryOpen, isOpen, onClose,
}: {
  user: User;
  sessions: SessionSummary[];
  activeThreadId: string | null;
  onSelectSession: (session: SessionSummary) => void;
  onNewResearch: () => void;
  onOpenLibrary: () => void;
  isLibraryOpen: boolean;
  isOpen: boolean;
  onClose: () => void;
}) {
  const router = useRouter();

  const signOut = async () => {
    await supabase.auth.signOut();
    router.push('/');
  };

  return (
    <>
      {isOpen && <div className="fixed inset-0 bg-black/30 z-40 md:hidden" onClick={onClose} aria-hidden />}
      <aside
        className={`fixed md:static inset-y-0 left-0 z-50 w-72 md:w-64 shrink-0 bg-mistral-beige border-r border-mistral-black/10 flex flex-col transition-transform md:translate-x-0 ${isOpen ? 'translate-x-0' : '-translate-x-full'}`}
        aria-label="Workspace navigation"
      >
        <div className="h-14 px-4 flex items-center justify-between border-b border-mistral-black/10">
          <Link href="/" className="flex items-center gap-1 text-mistral-black font-mono text-base font-black uppercase tracking-tighter">
            <img src="/logo.png" alt="" className="w-10 h-10 object-contain" />
            Lume
          </Link>
          <button onClick={onClose} className="md:hidden p-2 text-mistral-black/70" aria-label="Close menu">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-4 space-y-1">
          <button
            onClick={onNewResearch}
            className="w-full flex items-center justify-center gap-2 bg-mistral-black text-white py-2.5 text-sm font-semibold hover:bg-mistral-orange transition-colors"
          >
            <Plus className="w-4 h-4" aria-hidden /> New research
          </button>
          <button
            onClick={onOpenLibrary}
            aria-pressed={isLibraryOpen}
            className={`w-full flex items-center gap-2.5 px-3 py-2.5 text-sm font-medium transition-colors ${
              isLibraryOpen ? 'bg-white text-mistral-orange' : 'text-mistral-black/80 hover:bg-white/70'
            }`}
          >
            <Library className="w-4 h-4" aria-hidden /> My library
          </button>
        </div>

        <nav className="flex-1 overflow-y-auto custom-scrollbar px-4 pb-4" aria-label="Research history">
          <h2 className="px-3 pt-2 pb-2 text-xs font-semibold text-mistral-black/60">History</h2>
          {sessions.length === 0 ? (
            <p className="px-3 py-2 text-sm text-mistral-black/60 leading-relaxed">
              Your research projects will appear here.
            </p>
          ) : (
            <ul className="space-y-0.5">
              {sessions.map(s => {
                const active = s.thread_id === activeThreadId;
                return (
                  <li key={s.thread_id}>
                    <button
                      onClick={() => onSelectSession(s)}
                      aria-current={active ? 'page' : undefined}
                      className={`w-full text-left px-3 py-2.5 transition-colors ${active ? 'bg-white' : 'hover:bg-white/70'}`}
                    >
                      <span className={`block text-sm leading-snug line-clamp-2 ${active ? 'text-mistral-black font-medium' : 'text-mistral-black/80'}`}>
                        {s.topic}
                      </span>
                      <span className="mt-1 flex items-center gap-1.5 text-xs text-mistral-black/60">
                        <span className={`w-1.5 h-1.5 ${s.research_mode === 'brainstorm' ? 'border border-mistral-black/50' : s.status === 'completed' ? 'bg-mistral-black/50' : 'bg-mistral-orange'}`} aria-hidden />
                        {s.research_mode === 'brainstorm' ? 'Brainstorm' : s.status === 'completed' ? 'Completed' : 'In progress'} · {formatDate(s.created_at)}
                      </span>
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </nav>

        <div className="p-4 border-t border-mistral-black/10 flex items-center gap-3">
          <div className="w-9 h-9 bg-mistral-black text-white flex items-center justify-center text-xs font-semibold uppercase shrink-0" aria-hidden>
            {user.email?.slice(0, 2) ?? '?'}
          </div>
          <span className="flex-1 min-w-0 text-sm text-mistral-black truncate" title={user.email}>{user.email}</span>
          <button onClick={signOut} className="p-2 text-mistral-black/60 hover:text-mistral-orange transition-colors" aria-label="Sign out" title="Sign out">
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </aside>
    </>
  );
}
