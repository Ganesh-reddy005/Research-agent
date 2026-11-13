import React from 'react';
import type { Attempt } from '@/lib/types';

const VERDICT_STYLE: Record<Attempt['verdict'], string> = {
  baseline: 'text-mistral-black/70 border-mistral-black/20',
  improved: 'text-emerald-700 border-emerald-600/40 bg-emerald-50',
  'no gain': 'text-mistral-black/70 border-mistral-black/20',
  worse: 'text-amber-800 border-amber-600/40 bg-amber-50',
  'failed checks': 'text-red-700 border-red-600/40 bg-red-50',
  crashed: 'text-red-700 border-red-600/40 bg-red-50',
};

const format = (n: number) => (Math.abs(n) >= 100 ? n.toFixed(1) : n.toPrecision(4));

/** The lab notebook as a table: every attempt, its verdict, its result and its change against the baseline. */
export default function AttemptsTable({ attempts, metric, goal }: {
  attempts: Attempt[];
  metric: string;
  goal: 'maximize' | 'minimize';
}) {
  const baseline = attempts.find(a => a.verdict === 'baseline')?.metric ?? null;
  return (
    <div className="overflow-x-auto border border-mistral-black/10">
      <table className="w-full text-sm">
        <thead className="bg-mistral-beige/60 text-left text-mistral-black/70">
          <tr>
            <th className="px-3 py-2 font-semibold">#</th>
            <th className="px-3 py-2 font-semibold">Idea</th>
            <th className="px-3 py-2 font-semibold">Result</th>
            <th className="px-3 py-2 font-semibold whitespace-nowrap">{metric}</th>
            <th className="px-3 py-2 font-semibold whitespace-nowrap">vs baseline</th>
          </tr>
        </thead>
        <tbody>
          {attempts.map(a => {
            const change = baseline && a.metric !== null && a.verdict !== 'baseline' ? (a.metric - baseline) / baseline * 100 : null;
            const better = change !== null && (goal === 'maximize' ? change > 0 : change < 0);
            return (
              <tr key={a.n} className="border-t border-mistral-black/10 align-top">
                <td className="px-3 py-2 text-mistral-black/60">{a.n}</td>
                <td className="px-3 py-2 text-mistral-black">{a.hypothesis}</td>
                <td className="px-3 py-2">
                  <span className={`inline-block px-2 py-0.5 border text-xs font-semibold whitespace-nowrap ${VERDICT_STYLE[a.verdict]}`}>{a.verdict}</span>
                </td>
                <td className="px-3 py-2 whitespace-nowrap text-mistral-black">
                  {a.metric === null ? '—' : <>{format(a.metric)}{a.spread ? <span className="text-mistral-black/60"> ±{a.spread.toPrecision(2)}</span> : null}</>}
                </td>
                <td className={`px-3 py-2 whitespace-nowrap ${change === null ? 'text-mistral-black/50' : better ? 'text-emerald-700' : 'text-amber-800'}`}>
                  {change === null ? '—' : `${change > 0 ? '+' : ''}${change.toFixed(1)}%`}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
