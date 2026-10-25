"use client";

import React, { useState } from 'react';
import { MAX_PAGES, WORDS_PER_PAGE } from '@/lib/ieee';

const PRESETS = [2, 4, 6, 8, 10, 15];

/** Paper length in IEEE pages; null lets Lume choose (a short paper of about 2 pages). */
export default function PageCountField({ value, onChange }: {
  value: number | null;
  onChange: (pages: number | null) => void;
}) {
  // What's typed in Other, kept separately so typing "15" isn't cleared when it passes "1"
  const [typed, setTyped] = useState('');
  const custom = typed !== '' && value === Number(typed);
  const option = (pages: number | null, label: string) => (
    <button
      key={label}
      type="button"
      role="radio"
      aria-checked={!custom && value === pages}
      onClick={() => { setTyped(''); onChange(pages); }}
      className={`min-w-[3rem] px-3 py-2 text-sm font-medium border transition-colors ${
        !custom && value === pages ? 'border-mistral-black bg-mistral-black text-white' : 'border-mistral-black/15 text-mistral-black/75 hover:border-mistral-black/40'
      }`}
    >
      {label}
    </button>
  );

  return (
    <fieldset className="space-y-3">
      <legend className="text-sm font-semibold text-mistral-black/70 mb-3">How many pages?</legend>
      <div role="radiogroup" aria-label="Paper length in pages" className="flex flex-wrap items-center gap-2">
        {option(null, 'Auto')}
        {PRESETS.map(pages => option(pages, String(pages)))}
        <label className="flex items-center gap-2 text-sm text-mistral-black/65">
          Other
          <input
            type="number"
            min={1}
            max={MAX_PAGES}
            value={typed}
            onChange={e => {
              setTyped(e.target.value);
              const pages = Number(e.target.value);
              onChange(Number.isInteger(pages) && pages >= 1 && pages <= MAX_PAGES ? pages : null);
            }}
            aria-label={`Custom number of pages, 1 to ${MAX_PAGES}`}
            className={`w-16 px-2 py-2 text-sm border bg-white focus:outline-none focus:border-mistral-orange ${custom ? 'border-mistral-black' : 'border-mistral-black/15'}`}
          />
        </label>
      </div>
      <p className="text-xs text-mistral-black/60">
        {value
          ? `About ${(value * WORDS_PER_PAGE).toLocaleString()} words of text in IEEE two-column format, plus references. Longer papers take longer to write.`
          : 'Lume writes a concise paper of about 2 pages.'}
      </p>
    </fieldset>
  );
}
