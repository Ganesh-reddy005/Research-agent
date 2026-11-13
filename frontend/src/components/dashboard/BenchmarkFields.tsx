"use client";

import React, { useState } from 'react';
import type { BenchmarkSpec } from '@/lib/types';
import { FieldLabel, SectionLabel, inputClass } from './ui';
import BriefListField from './BriefListField';

const toLines = (checks: Record<string, string>) => Object.entries(checks).map(([name, command]) => `${name}: ${command}`);
const fromLines = (lines: string[]) => Object.fromEntries(lines.map(line => {
  const at = line.indexOf(':');
  return at > 0 ? [line.slice(0, at).trim(), line.slice(at + 1).trim()] : [line.trim(), line.trim()];
}).filter(([name, command]) => name && command));

/** The setup commands and how attempts are graded. Editable until the baseline is measured, then fixed. */
export default function BenchmarkFields({ setup, spec, locked, onChange }: {
  setup: string[];
  spec: BenchmarkSpec;
  locked: boolean;
  onChange: (setup: string[], spec: BenchmarkSpec) => void;
}) {
  const set = (patch: Partial<BenchmarkSpec>) => onChange(setup, { ...spec, ...patch });
  // Raw lines, so a new empty line can be typed into before it parses as "name: command"
  const [checkLines, setCheckLines] = useState(() => toLines(spec.checks));
  if (locked) {
    return (
      <section className="space-y-2 text-sm text-mistral-black/80">
        <SectionLabel>How attempts are graded (fixed since the baseline)</SectionLabel>
        {spec.build && <p>Build: <code>{spec.build}</code></p>}
        {Object.entries(spec.checks).map(([name, command]) => <p key={name}>Check “{name}”: <code>{command}</code></p>)}
        <p>Measure: <code>{spec.measure}</code> ({spec.read === 'time' ? 'run time' : spec.read}), {spec.repeats} repeats after {spec.warmup} warm-up</p>
        {spec.protected.length > 0 && <p>Protected: {spec.protected.join(', ')}</p>}
      </section>
    );
  }
  return (
    <div className="space-y-8">
      <BriefListField label="Setup commands" hint="Run once, with network: install dependencies and download any models or data. Nothing after this has network."
                      items={setup} placeholder="e.g. pip install -r requirements.txt" onChange={next => onChange(next, spec)} />
      <section className="space-y-3">
        <SectionLabel>How every attempt is graded</SectionLabel>
        <div>
          <FieldLabel htmlFor="build">Build command (optional)</FieldLabel>
          <input id="build" value={spec.build} onChange={e => set({ build: e.target.value })} className={inputClass} />
        </div>
        <div>
          <FieldLabel htmlFor="measure">Measure command: its run time, or the number it prints, is the metric</FieldLabel>
          <input id="measure" value={spec.measure} onChange={e => set({ measure: e.target.value })} className={inputClass} />
        </div>
        <FieldLabel htmlFor="read">How to read the metric: “time”, “json:key”, “regex:pattern”, or “json” for a results table</FieldLabel>
        <div className="grid sm:grid-cols-[1fr_auto_auto] gap-2">
          <input id="read" value={spec.read} onChange={e => set({ read: e.target.value })} className={inputClass} />
          <label className="flex items-center gap-2 text-sm text-mistral-black/70">Repeats
            <input type="number" min={2} max={20} value={spec.repeats} onChange={e => set({ repeats: Number(e.target.value) || 2 })}
                   className={`${inputClass} !w-20 !py-2`} /></label>
          <label className="flex items-center gap-2 text-sm text-mistral-black/70">Warm-up
            <input type="number" min={0} max={5} value={spec.warmup} onChange={e => set({ warmup: Number(e.target.value) || 0 })}
                   className={`${inputClass} !w-20 !py-2`} /></label>
        </div>
      </section>
      <BriefListField label="Checks" hint='Each line is "name: command"; every attempt must pass all of them.'
                      items={checkLines} placeholder="tests: python -m pytest -q"
                      onChange={lines => { setCheckLines(lines); set({ checks: fromLines(lines) }); }} />
      <BriefListField label="Protected files" hint="No attempt may change these: tests, benchmark inputs, anything the checks rely on."
                      items={spec.protected} placeholder="e.g. tests/*" onChange={globs => set({ protected: globs })} />
    </div>
  );
}
