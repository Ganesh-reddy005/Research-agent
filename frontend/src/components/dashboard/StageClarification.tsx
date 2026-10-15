"use client";

import React, { useState } from 'react';
import { ArrowRight } from 'lucide-react';
import type { ClarificationQuestion } from '@/lib/types';
import { Button, StageHeader, inputClass } from './ui';

export default function StageClarification({ questions, initialAnswers, onSubmit, isProcessing }: {
  questions: ClarificationQuestion[];
  initialAnswers: Record<string, string>;
  onSubmit: (answers: Record<string, string>) => void;
  isProcessing: boolean;
}) {
  const [answers, setAnswers] = useState<Record<string, string>>(initialAnswers);

  return (
    <div className="space-y-10">
      <StageHeader
        title="A few questions first"
        description="Your answers help Lume focus the search. Skip any you're unsure about."
      />

      <ol className="space-y-8">
        {questions.map((q, i) => (
          <li key={q.id}>
            <label className="block space-y-3">
              <span className="flex gap-3 text-base font-medium text-mistral-black leading-relaxed">
                <span className="text-mistral-orange font-semibold">{i + 1}.</span>
                {q.question}
              </span>
              <textarea
                rows={2}
                value={answers[q.id] ?? ''}
                onChange={e => setAnswers({ ...answers, [q.id]: e.target.value })}
                placeholder="Your answer (optional)"
                className={`${inputClass} resize-y`}
              />
            </label>
          </li>
        ))}
      </ol>

      <div className="flex justify-end pt-2">
        <Button onClick={() => onSubmit(answers)} loading={isProcessing} className="!px-6 !py-3">
          Continue to the plan <ArrowRight className="w-4 h-4" aria-hidden />
        </Button>
      </div>
    </div>
  );
}
