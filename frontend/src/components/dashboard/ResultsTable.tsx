import React from 'react';
import type { Attempt } from '@/lib/types';

type Results = NonNullable<Attempt['results']>;

/** Results of code built from scratch: one row per variant, one column per metric, mean ± spread.
 *  "quicksort.seconds" is variant "quicksort", metric "seconds"; a name without a dot is its own row. */
export default function ResultsTable({ results }: { results: Results }) {
  const rows = new Map<string, Map<string, { mean: number; spread: number }>>();
  Object.entries(results).forEach(([name, value]) => {
    const at = name.lastIndexOf('.');
    const [variant, metric] = at > 0 ? [name.slice(0, at), name.slice(at + 1)] : [name, 'value'];
    rows.set(variant, (rows.get(variant) ?? new Map()).set(metric, value));
  });
  const metrics = Array.from(new Set(Array.from(rows.values()).flatMap(m => Array.from(m.keys()))));
  if (rows.size === 0) return <p className="text-sm text-mistral-black/60">No results yet: the evaluation runs, but no variant is built.</p>;
  return (
    <div className="overflow-x-auto border border-mistral-black/10">
      <table className="w-full text-sm">
        <thead className="bg-mistral-beige/60 text-left text-mistral-black/70">
          <tr><th className="px-3 py-2 font-semibold">Variant</th>{metrics.map(m => <th key={m} className="px-3 py-2 font-semibold">{m}</th>)}</tr>
        </thead>
        <tbody>
          {Array.from(rows.entries()).map(([variant, values]) => (
            <tr key={variant} className="border-t border-mistral-black/10">
              <td className="px-3 py-2 font-semibold text-mistral-black">{variant}</td>
              {metrics.map(m => {
                const v = values.get(m);
                return <td key={m} className="px-3 py-2 whitespace-nowrap text-mistral-black">
                  {v ? <>{v.mean.toPrecision(4)}{v.spread ? <span className="text-mistral-black/60"> ±{v.spread.toPrecision(2)}</span> : null}</> : '—'}
                </td>;
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
