"use client";

import React, { useEffect, useRef, useState } from 'react';
import { Loader2, MoreHorizontal, Trash2 } from 'lucide-react';
import type { SessionSummary } from '@/lib/types';

function formatDate(iso: string) {
  const date = new Date(iso);
  const days = Math.floor((Date.now() - date.getTime()) / 86_400_000);
  if (days < 1 && new Date().getDate() === date.getDate()) return 'Today';
  if (days < 2) return 'Yesterday';
  return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

/** One History entry: opens the session; its ⋯ menu deletes it after a confirmation. */
export default function HistoryItem({ session, active, onSelect, onDelete }: {
  session: SessionSummary;
  active: boolean;
  onSelect: () => void;
  onDelete: () => Promise<void>;
}) {
  const [menuOpen, setMenuOpen] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const ref = useRef<HTMLLIElement>(null);
  const brainstorm = session.research_mode === 'brainstorm';

  // Close the menu or confirmation on Escape or a click elsewhere
  useEffect(() => {
    if (!menuOpen && !confirming) return;
    const close = (e: MouseEvent | KeyboardEvent) => {
      const outside = e instanceof KeyboardEvent ? e.key === 'Escape' : !ref.current?.contains(e.target as Node);
      if (outside && !deleting) {
        setMenuOpen(false);
        setConfirming(false);
      }
    };
    document.addEventListener('mousedown', close);
    document.addEventListener('keydown', close);
    return () => {
      document.removeEventListener('mousedown', close);
      document.removeEventListener('keydown', close);
    };
  }, [menuOpen, confirming, deleting]);

  const remove = async () => {
    setDeleting(true);
    try {
      await onDelete();
    } finally {
      setDeleting(false);
      setConfirming(false);
    }
  };

  return (
    <li ref={ref} className="relative group">
      <button
        onClick={onSelect}
        aria-current={active ? 'page' : undefined}
        className={`w-full text-left pl-3 pr-9 py-2.5 transition-colors ${active ? 'bg-white' : 'hover:bg-white/70'}`}
      >
        <span className={`block text-sm leading-snug line-clamp-2 ${active ? 'text-mistral-black font-medium' : 'text-mistral-black/80'}`}>
          {session.topic}
        </span>
        <span className="mt-1 flex items-center gap-1.5 text-xs text-mistral-black/60">
          <span className={`w-1.5 h-1.5 ${brainstorm ? 'border border-mistral-black/50' : session.status === 'completed' ? 'bg-mistral-black/50' : 'bg-mistral-orange'}`} aria-hidden />
          {brainstorm ? 'Brainstorm' : session.status === 'completed' ? 'Completed' : 'In progress'} · {formatDate(session.created_at)}
        </span>
      </button>

      <button
        onClick={() => { setMenuOpen(!menuOpen); setConfirming(false); }}
        aria-label={`Options for ${session.topic}`}
        aria-haspopup="menu"
        aria-expanded={menuOpen}
        className={`absolute right-1.5 top-2 p-1.5 text-mistral-black/60 hover:text-mistral-black hover:bg-mistral-black/5 transition-opacity focus-visible:opacity-100 ${
          menuOpen || active ? 'opacity-100' : 'md:opacity-0 md:group-hover:opacity-100'
        }`}
      >
        <MoreHorizontal className="w-4 h-4" aria-hidden />
      </button>

      {menuOpen && (
        <div role="menu" className="absolute right-1.5 top-9 z-20 w-36 bg-white border border-mistral-black/15 shadow-lg py-1">
          <button
            role="menuitem"
            onClick={() => { setMenuOpen(false); setConfirming(true); }}
            className="w-full flex items-center gap-2 px-3 py-2 text-sm text-red-700 hover:bg-red-50"
          >
            <Trash2 className="w-4 h-4" aria-hidden /> Delete
          </button>
        </div>
      )}

      {confirming && (
        <div role="alertdialog" aria-label="Confirm delete" className="mx-1 mb-2 p-3 bg-white border border-red-200 space-y-2.5">
          <p className="text-xs text-mistral-black/80 leading-relaxed">
            Delete this {brainstorm ? 'conversation' : 'project'}? Its {brainstorm ? 'messages' : 'paper, sources and progress'} will
            be removed for good.
          </p>
          <div className="flex gap-2">
            <button
              onClick={remove}
              disabled={deleting}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold bg-red-700 text-white hover:bg-red-800 disabled:opacity-50"
            >
              {deleting && <Loader2 className="w-3 h-3 animate-spin" aria-hidden />} Delete
            </button>
            <button
              onClick={() => setConfirming(false)}
              disabled={deleting}
              className="px-3 py-1.5 text-xs font-semibold text-mistral-black/70 hover:text-mistral-black"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </li>
  );
}
