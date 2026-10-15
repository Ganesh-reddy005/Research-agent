"use client";

import React, { useEffect, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { ArrowLeft, ArrowUp } from 'lucide-react';
import type { ChatMessage } from '@/lib/types';
import { Button, inputClass } from './ui';

export default function StageBrainstorm({ messages, onSend, onBack, isProcessing }: {
  messages: ChatMessage[];
  onSend: (text: string) => void;
  onBack: () => void;
  isProcessing: boolean;
}) {
  const [text, setText] = useState('');
  const endRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ block: 'end' });
  }, [messages]);

  useEffect(() => {
    if (!isProcessing) inputRef.current?.focus();
  }, [isProcessing]);

  const send = () => {
    if (!text.trim() || isProcessing) return;
    onSend(text.trim());
    setText('');
  };

  return (
    <div className="flex flex-col min-h-[calc(100vh-10rem)]">
      <div className="flex items-center justify-between gap-4 pb-6 mb-6 border-b border-mistral-black/10">
        <Button variant="ghost" onClick={onBack} className="!px-2 -ml-2">
          <ArrowLeft className="w-4 h-4" aria-hidden /> Back
        </Button>
        <span className="text-sm text-mistral-black/60">Saved to your history</span>
      </div>

      <div className="flex-1 space-y-6 pb-8" aria-live="polite">
        {messages.map((m, i) => (
          <div key={i} className={m.role === 'user' ? 'flex justify-end' : ''}>
            {m.role === 'user' ? (
              <div className="max-w-[85%] bg-mistral-black text-white px-4 py-3 text-[15px] leading-relaxed whitespace-pre-line">
                {m.content}
              </div>
            ) : (
              <div className="prose prose-base max-w-none prose-p:leading-relaxed prose-p:text-mistral-black/85">
                {m.content
                  ? <ReactMarkdown>{m.content}</ReactMarkdown>
                  : <span className="text-sm text-mistral-black/60">Thinking…</span>}
              </div>
            )}
          </div>
        ))}
        <div ref={endRef} />
      </div>

      <div className="sticky bottom-0 bg-white pt-3 pb-1 border-t border-mistral-black/10">
        <div className="flex gap-2 items-end">
          <textarea
            ref={inputRef}
            rows={2}
            value={text}
            disabled={isProcessing}
            onChange={e => setText(e.target.value)}
            onKeyDown={e => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                send();
              }
            }}
            placeholder="Reply… (Shift + Enter for a new line)"
            aria-label="Message"
            className={`${inputClass} resize-none`}
          />
          <Button onClick={send} disabled={!text.trim()} loading={isProcessing} aria-label="Send" className="!px-3.5 !py-3.5">
            {!isProcessing && <ArrowUp className="w-4 h-4" aria-hidden />}
          </Button>
        </div>
      </div>
    </div>
  );
}
