"use client";

import React, { useMemo, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { AlertTriangle, CircleCheck, Download, FileText } from 'lucide-react';
import type { CitationAudit, Source } from '@/lib/types';
import { Button } from './ui';

// [3] -> link to the matching reference (skips real markdown links like [text](url))
const linkCitations = (md: string) => md.replace(/\[(\d+)\](?!\()/g, '[[$1]](#ref-$1)');

const citedNumbers = (md: string) => new Set(Array.from(md.matchAll(/\[(\d+)\]/g), m => Number(m[1])));

const sourceHref = (url: string) => (url.startsWith('http') ? url : undefined);

function CitationCheck({ audit, sourceCount }: { audit: CitationAudit; sourceCount: number }) {
  const invalid = audit.invalid_citations ?? [];
  const ok = invalid.length === 0 && audit.total_citations_found > 0;
  return (
    <section className={`p-5 border space-y-2 ${ok ? 'border-mistral-black/15 bg-mistral-beige/40' : 'border-amber-300 bg-amber-50'}`}>
      <div className="flex items-center gap-2 text-sm font-semibold text-mistral-black">
        {ok ? <CircleCheck className="w-4 h-4 text-mistral-orange" aria-hidden /> : <AlertTriangle className="w-4 h-4 text-amber-600" aria-hidden />}
        Citation check
      </div>
      <p className="text-sm text-mistral-black/80 leading-relaxed">
        {audit.total_citations_found === 0
          ? 'This draft contains no numbered citations.'
          : `${audit.total_citations_found} citations referring to ${audit.unique_sources_cited} different sources. `}
        {invalid.length > 0
          ? `Citation${invalid.length > 1 ? 's' : ''} ${invalid.map(n => `[${n}]`).join(', ')} ${invalid.length > 1 ? "don't" : "doesn't"} match any of the ${sourceCount} retrieved sources. Treat ${invalid.length > 1 ? 'them' : 'it'} as unverified.`
          : audit.total_citations_found > 0 && 'Every citation points to a source Lume actually retrieved.'}
      </p>
      <p className="text-xs text-mistral-black/60 leading-relaxed">
        This check confirms each citation points to a real retrieved source. It does not yet confirm that the source
        supports the sentence it is attached to, so review key claims before submitting.
      </p>
    </section>
  );
}

export default function StageCompleted({ topic, report, sources, audit, reportRef, threadId }: {
  topic: string;
  report: string;
  sources: Source[];
  audit?: CitationAudit;
  reportRef: React.RefObject<HTMLDivElement>;
  threadId: string | null;
}) {
  const [showAll, setShowAll] = useState(false);
  const [exporting, setExporting] = useState(false);
  const cited = useMemo(() => citedNumbers(report), [report]);
  const markdown = useMemo(() => linkCitations(report), [report]);

  // Numbering must match the citations: [n] is raw_sources[n - 1]
  const numbered = sources.map((s, i) => ({ ...s, n: i + 1 }));
  const visible = showAll ? numbered : numbered.filter(s => cited.has(s.n));
  const fileBase = `Lume_${(threadId ?? 'report').slice(0, 8)}`;

  const downloadPdf = async () => {
    if (!reportRef.current) return;
    setExporting(true);
    try {
      const html2pdf = (await import('html2pdf.js')).default;
      await html2pdf().set({
        margin: [0.6, 0.6, 0.6, 0.6],
        filename: `${fileBase}.pdf`,
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { scale: 2 },
        jsPDF: { unit: 'in', format: 'letter', orientation: 'portrait' },
      }).from(reportRef.current).save();
    } finally {
      setExporting(false);
    }
  };

  const downloadMarkdown = () => {
    const refs = numbered.filter(s => cited.has(s.n)).map(s => `[${s.n}] ${s.title}. ${s.url}`).join('\n');
    const blob = new Blob([`# ${topic}\n\n${report}\n\n## References\n\n${refs}\n`], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = Object.assign(document.createElement('a'), { href: url, download: `${fileBase}.md` });
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-center gap-3 sm:justify-between">
        <p className="text-sm text-mistral-black/65">Your draft is ready. Review it, then download.</p>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={downloadMarkdown}>
            <FileText className="w-4 h-4" aria-hidden /> Markdown
          </Button>
          <Button onClick={downloadPdf} loading={exporting}>
            <Download className="w-4 h-4" aria-hidden /> PDF
          </Button>
        </div>
      </div>

      {audit && <CitationCheck audit={audit} sourceCount={sources.length} />}

      <div ref={reportRef} className="bg-white border border-mistral-black/10 px-6 py-10 sm:px-14 sm:py-14">
        <h1 className="font-serif text-3xl sm:text-4xl text-mistral-black tracking-tight leading-tight mb-10">{topic}</h1>
        <article className="prose prose-lg max-w-none prose-headings:font-serif prose-headings:font-semibold prose-headings:tracking-tight prose-p:text-mistral-black/85 prose-p:leading-relaxed prose-a:text-mistral-orange prose-a:no-underline hover:prose-a:underline">
          <ReactMarkdown
            components={{
              a: ({ href, children }) =>
                href?.startsWith('#ref-')
                  ? <a href={href} className="font-semibold text-mistral-orange">{children}</a>
                  : <a href={href} target="_blank" rel="noopener noreferrer">{children}</a>,
            }}
          >
            {markdown}
          </ReactMarkdown>
        </article>

        {numbered.length > 0 && (
          <section className="mt-14 pt-8 border-t border-mistral-black/15 space-y-5">
            <h2 className="font-serif text-2xl font-semibold text-mistral-black">References</h2>
            <ol className="space-y-3">
              {visible.map(s => (
                <li key={s.n} id={`ref-${s.n}`} className="flex gap-3 text-sm leading-relaxed scroll-mt-24">
                  <span className="font-semibold text-mistral-orange tabular-nums shrink-0">[{s.n}]</span>
                  <span className="space-y-0.5">
                    {sourceHref(s.url)
                      ? <a href={s.url} target="_blank" rel="noopener noreferrer" className="text-mistral-black hover:text-mistral-orange underline decoration-mistral-black/20 underline-offset-2">{s.title}</a>
                      : <span className="text-mistral-black">{s.title}</span>}
                    <span className="block text-mistral-black/60">
                      {s.url.startsWith('local://') ? 'Your library' : s.source}
                    </span>
                  </span>
                </li>
              ))}
            </ol>
            {numbered.length > visible.length || showAll ? (
              <Button variant="ghost" onClick={() => setShowAll(!showAll)} className="!px-0" data-html2canvas-ignore>
                {showAll ? 'Show only cited sources' : `Show all ${numbered.length} retrieved sources`}
              </Button>
            ) : null}
          </section>
        )}
      </div>
    </div>
  );
}
