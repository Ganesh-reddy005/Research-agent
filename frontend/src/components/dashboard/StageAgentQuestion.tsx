"use client";

import React, { useState } from 'react';
import { ArrowRight } from 'lucide-react';
import { Button, StageHeader, inputClass } from './ui';

/** An agent paused mid-step to ask something only the user can answer; it continues with the answer. */
export default function StageAgentQuestion({ question, onAnswer, isProcessing }: {
  question: string;
  onAnswer: (answer: string) => void;
  isProcessing: boolean;
}) {
  const [answer, setAnswer] = useState('');
  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    if (answer.trim()) onAnswer(answer.trim());
  };
  return (
    <form onSubmit={submit} className="space-y-8">
      <StageHeader title="Lume has a question" description="The agent paused to ask something only you can answer. It continues where it stopped once you reply." />
      <p className="text-xl text-mistral-black leading-relaxed">{question}</p>
      <textarea value={answer} onChange={e => setAnswer(e.target.value)} rows={3} aria-label="Your answer"
                placeholder="Your answer" className={`${inputClass} resize-y`} autoFocus />
      <div className="flex justify-end pt-2 border-t border-mistral-black/10">
        <Button type="submit" disabled={!answer.trim()} loading={isProcessing} className="!px-6 !py-3 mt-6">
          Answer and continue <ArrowRight className="w-4 h-4" aria-hidden />
        </Button>
      </div>
    </form>
  );
}
