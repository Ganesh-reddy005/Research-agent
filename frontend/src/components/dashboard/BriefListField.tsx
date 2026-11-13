"use client";

import React from 'react';
import { Plus, X } from 'lucide-react';
import { SectionLabel, inputClass } from './ui';

/** An editable list of short lines, e.g. the checks every experiment must still pass. */
export default function BriefListField({ label, hint, items, placeholder, onChange }: {
  label: string;
  hint?: string;
  items: string[];
  placeholder: string;
  onChange: (items: string[]) => void;
}) {
  const update = (i: number, value: string) => onChange(items.map((item, j) => (j === i ? value : item)));

  return (
    <section className="space-y-3">
      <div className="space-y-1">
        <SectionLabel>{label}</SectionLabel>
        {hint && <p className="text-sm text-mistral-black/60">{hint}</p>}
      </div>
      <ul className="space-y-2">
        {items.map((item, i) => (
          <li key={i} className="flex items-center gap-2">
            <input
              value={item}
              onChange={e => update(i, e.target.value)}
              placeholder={placeholder}
              aria-label={`${label} ${i + 1}`}
              className={`${inputClass} !py-2 !text-sm`}
            />
            <button
              onClick={() => onChange(items.filter((_, j) => j !== i))}
              aria-label={`Remove ${label.toLowerCase()} ${i + 1}`}
              className="p-2 text-mistral-black/50 hover:text-red-600 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </li>
        ))}
      </ul>
      <button
        onClick={() => onChange([...items, ''])}
        className="inline-flex items-center gap-1.5 text-sm font-semibold text-mistral-black/70 hover:text-mistral-orange transition-colors"
      >
        <Plus className="w-4 h-4" aria-hidden /> Add
      </button>
    </section>
  );
}
