"use client";

import React, { useState } from 'react';
import { ArrowRight, Send } from 'lucide-react';
import type { ChatMessage, Source } from '@/lib/types';
import { Button, SectionLabel, StageHeader, inputClass } from './ui';

function countBySource(sources: Source[]) {
  const counts = new Map<string, number>();
  sources.forEach(s => counts.set(s.source, (counts.get(s.source) ?? 0) + 1));
  return Array.from(counts.entries()).sort((a, b) => b[1] - a[1]);
}

export default function StageReview({ summary, sources, chat, onAsk, onWritePaper, isProcessing }: {
  summary: string;
  sources: Source[];
  chat: ChatMessage[];
  onAsk: (question: string) => void;
  onWritePaper: () => void;
  isProcessing: boolean;
}) {
  const [question, setQuestion] = useState('');

  const ask = (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || isProcessing) return;
    onAsk(question.trim());
    setQuestion('');
  };

  return (
    <div className="space-y-10">
      <StageHeader
        title="Here's what Lume found"
        description="Read the summary and ask questions about the sources. When you're ready, Lume writes the paper."
      />

      <section className="space-y-4">
        <SectionLabel>{sources.length} sources collected</SectionLabel>
        <ul className="flex flex-wrap gap-2">
          {countBySource(sources).map(([name, n]) => (
            <li key={name} className="px-3 py-1.5 border border-mistral-black/15 text-sm text-mistral-black/80">
              {name} <span className="font-semibold text-mistral-black">{n}</span>
            </li>
          ))}
        </ul>
      </section>

      {summary && (
        <section className="space-y-3">
          <SectionLabel>Summary</SectionLabel>
          <p className="text-base text-mistral-black/85 leading-relaxed whitespace-pre-line">{summary}</p>
        </section>
      )}

      <section className="space-y-4">
        <SectionLabel>Ask about the sources</SectionLabel>
        {chat.length > 0 && (
          <ul className="space-y-4 max-h-[28rem] overflow-y-auto custom-scrollbar pr-1" aria-live="polite">
            {chat.map((m, i) => (
              <li key={i} className={m.role === 'user' ? 'flex justify-end' : ''}>
                <div className={`max-w-[85%] px-4 py-3 text-[15px] leading-relaxed whitespace-pre-line ${
                  m.role === 'user' ? 'bg-mistral-black text-white' : 'bg-mistral-beige/60 text-mistral-black border border-mistral-black/10'
                }`}>
                  {m.content}
                </div>
              </li>
            ))}
          </ul>
        )}
        <form onSubmit={ask} className="flex gap-2">
          <input
            value={question}
            onChange={e => setQuestion(e.target.value)}
            placeholder="e.g. Which sources disagree with each other?"
            aria-label="Ask a question about the sources"
            className={inputClass}
          />
          <Button type="submit" variant="secondary" disabled={!question.trim()} loading={isProcessing} aria-label="Ask">
            <Send className="w-4 h-4" aria-hidden />
          </Button>
        </form>
      </section>

      <div className="flex justify-end pt-6 border-t border-mistral-black/10">
        <Button onClick={onWritePaper} disabled={isProcessing} className="!px-6 !py-3">
          Write the paper <ArrowRight className="w-4 h-4" aria-hidden />
        </Button>
      </div>
    </div>
  );
}
