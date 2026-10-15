import React from 'react';
import { Check } from 'lucide-react';
import { STEPS } from './agents';

/** Where the project is in Questions → Plan → Sources → Review → Paper. */
export default function ProgressSteps({ current, done = false }: { current: number; done?: boolean }) {
  return (
    <ol className="flex items-center gap-2 overflow-x-auto pb-1" aria-label="Research progress">
      {STEPS.map((label, i) => {
        const complete = done || i < current;
        const active = !done && i === current;
        return (
          <li key={label} className="flex items-center gap-2 shrink-0" aria-current={active ? 'step' : undefined}>
            <span className={`flex items-center gap-2 text-sm ${active ? 'text-mistral-black font-semibold' : complete ? 'text-mistral-black/70' : 'text-mistral-black/45'}`}>
              <span className={`w-6 h-6 flex items-center justify-center text-xs font-semibold border ${
                complete ? 'bg-mistral-black border-mistral-black text-white'
                  : active ? 'border-mistral-orange text-mistral-orange'
                  : 'border-mistral-black/20 text-mistral-black/50'
              }`}>
                {complete ? <Check className="w-3.5 h-3.5" aria-hidden /> : i + 1}
              </span>
              {label}
            </span>
            {i < STEPS.length - 1 && <span className={`w-6 sm:w-10 h-px ${complete ? 'bg-mistral-black' : 'bg-mistral-black/15'}`} aria-hidden />}
          </li>
        );
      })}
    </ol>
  );
}
