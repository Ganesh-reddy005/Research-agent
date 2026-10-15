"use client";

import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { ArrowRight, Search, Send } from 'lucide-react';
import type { ChatMessage, Source } from '@/lib/types';
import { Button, SectionLabel, StageHeader, inputClass } from './ui';
import { SourceLink } from './SearchActivity';

/** A source-chat answer: the query searched, the answer with linked [n] citations, and its sources. */
function Answer({ message }: { message: ChatMessage }) {
  const urls = new Map((message.sources ?? []).map(s => [s.n, s.url]));
  const linked = message.content.replace(/\[(\d+)\](?!\()/g, (match, n) =>
    urls.has(Number(n)) ? `[[${n}]](${urls.get(Number(n))})` : match);
  return (
    <div className="space-y-3">
      {message.searchQuery && (
        <p className="flex items-center gap-2 text-xs text-mistral-black/60">
          <Search className="w-3.5 h-3.5 shrink-0" aria-hidden /> Searched for “{message.searchQuery}”
        </p>
      )}
      <div className="prose prose-sm max-w-none prose-p:leading-relaxed prose-p:text-mistral-black/85 prose-a:text-mistral-orange prose-a:no-underline hover:prose-a:underline">
        <ReactMarkdown components={{ a: ({ href, children }) => <a href={href} target="_blank" rel="noopener noreferrer">{children}</a> }}>
          {linked}
        </ReactMarkdown>
      </div>
      {message.sources && message.sources.length > 0 && (
        <ul className="space-y-2 pt-3 border-t border-mistral-black/10">
          {message.sources.map(s => <li key={s.n}><SourceLink s={s} /></li>)}
        </ul>
      )}
    </div>
  );
}

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
                {m.role === 'user' ? (
                  <div className="max-w-[85%] px-4 py-3 text-[15px] leading-relaxed whitespace-pre-line bg-mistral-black text-white">
                    {m.content}
                  </div>
                ) : (
                  <div className="px-4 py-4 bg-mistral-beige/60 border border-mistral-black/10">
                    <Answer message={m} />
                  </div>
                )}
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
