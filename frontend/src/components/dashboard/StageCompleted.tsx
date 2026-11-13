"use client";

import React, { useMemo, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ChevronDown, Download, FileCode2, FileText } from 'lucide-react';
import type { CitationAudit, PaperFigure as Figure, Source } from '@/lib/types';
import {
  IEEE_CSS, WORDS_PER_PAGE, formatReference, paperWords, parsePaper, printPaper, renumberCitations, sectionLabels,
} from '@/lib/ieee';
import { type Numbering, numberFigures, resolveRefs, splitBlocks } from '@/lib/figures';
import { download, downloadLatex, paperMarkdown } from '@/lib/paperExport';
import { Button } from './ui';
import CitationCheck from './CitationCheck';
import PaperFigure from './PaperFigure';

// [3] -> link to reference 3 ([?] and real markdown links are left alone)
const linkCitations = (md: string) => md.replace(/\[(\d+)\](?!\()/g, '[[$1]](#ref-$1)');

const link = ({ href, children }: { href?: string; children?: React.ReactNode }) =>
  href?.startsWith('#ref-')
    ? <a href={href}>{children}</a>
    : <a href={href} target="_blank" rel="noopener noreferrer">{children}</a>;

/** A section body in the IEEE layout: Markdown runs (tables included) with figures where the text places them. */
function Body({ text, numbering }: { text: string; numbering: Numbering }) {
  return (
    <>
      {splitBlocks(text).map((block, i) => block.kind === 'figure'
        ? <PaperFigure key={i} id={block.id} numbering={numbering} />
        : <ReactMarkdown key={i} remarkPlugins={[remarkGfm]} components={{ a: link }}>{linkCitations(resolveRefs(block.text, numbering))}</ReactMarkdown>)}
    </>
  );
}

/** Markdown inside an existing paragraph (abstract): no extra <p>. */
function Inline({ text }: { text: string }) {
  return (
    <ReactMarkdown components={{ a: link, p: ({ children }) => <>{children}</> }}>
      {linkCitations(text)}
    </ReactMarkdown>
  );
}

function Reference({ source }: { source: Source }) {
  const [text, url] = formatReference(source).split(' [Online]. Available: ');
  return (
    <>
      {text}
      {url && <> [Online]. Available: <a href={url} target="_blank" rel="noopener noreferrer">{url}</a></>}
    </>
  );
}

export default function StageCompleted({ topic, report, sources, figures, audit, targetPages, reportRef, threadId }: {
  topic: string;
  report: string;
  sources: Source[];
  figures: Figure[];
  audit?: CitationAudit;
  targetPages?: number;
  reportRef: React.RefObject<HTMLDivElement>;
  threadId: string | null;
}) {
  const [showRetrieved, setShowRetrieved] = useState(false);
  // IEEE: references numbered by first citation, cited works only
  const { paper, references } = useMemo(() => renumberCitations(parsePaper(report, topic), sources), [report, topic, sources]);
  const numbering = useMemo(() => numberFigures(paper, figures), [paper, figures]);
  const labels = sectionLabels(paper.sections);
  const [exporting, setExporting] = useState(false);
  const words = paperWords(paper);
  const pages = Math.max(1, Math.round(words / WORDS_PER_PAGE));
  const fileBase = `Lume_${(threadId ?? 'paper').slice(0, 8)}`;
  const date = new Date().toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' });

  const exportLatex = async () => {
    setExporting(true);
    try { await downloadLatex(paper, references, numbering, fileBase); } finally { setExporting(false); }
  };

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-center gap-3 sm:justify-between">
        <p className="text-sm text-mistral-black/65">
          Your draft is ready, typeset in IEEE style: about {pages} page{pages === 1 ? '' : 's'} ({words.toLocaleString()} words)
          {targetPages ? `, for a target of ${targetPages}` : ''}.
        </p>
        <div className="flex flex-wrap gap-2">
          <Button variant="secondary" onClick={() => download(paperMarkdown(paper, labels, references, numbering), `${fileBase}.md`, 'text/markdown')}>
            <FileText className="w-4 h-4" aria-hidden /> Markdown
          </Button>
          <Button variant="secondary" onClick={exportLatex} loading={exporting}>
            <FileCode2 className="w-4 h-4" aria-hidden /> LaTeX (IEEE)
          </Button>
          <Button onClick={() => reportRef.current && printPaper(reportRef.current, paper.title)}>
            <Download className="w-4 h-4" aria-hidden /> PDF
          </Button>
        </div>
      </div>

      {audit && <CitationCheck audit={audit} sourceCount={sources.length} />}

      <style>{IEEE_CSS}</style>
      <div className="bg-white border border-mistral-black/10 px-6 py-10 sm:px-12 sm:py-14 shadow-sm">
        <div ref={reportRef} className="ieee-paper">
          <h1 className="ieee-title">{paper.title}</h1>
          <p className="ieee-byline">Draft generated with Lume · {date}</p>
          <div className="ieee-body">
            {paper.abstract && (
              <p className="ieee-abstract"><em>Abstract</em>—<Inline text={paper.abstract} /></p>
            )}
            {paper.keywords && (
              <p className="ieee-keywords"><em>Index Terms</em>—{paper.keywords}.</p>
            )}
            {paper.sections.map((s, i) => (
              <section key={i}>
                {s.level === 2 ? <h2>{labels[i]} {s.title}</h2> : <h3>{labels[i]} {s.title}</h3>}
                <Body text={s.body} numbering={numbering} />
              </section>
            ))}
            {references.length > 0 && (
              <section>
                <h2>References</h2>
                <ol className="ieee-refs">
                  {references.map((r, i) => (
                    <li key={i} id={`ref-${i + 1}`}>
                      <span>[{i + 1}]</span>
                      <span><Reference source={r} /></span>
                    </li>
                  ))}
                </ol>
              </section>
            )}
          </div>
        </div>
      </div>

      {sources.length > 0 && (
        <section className="space-y-3">
          <button
            onClick={() => setShowRetrieved(!showRetrieved)}
            aria-expanded={showRetrieved}
            className="flex items-center gap-2 text-sm font-semibold text-mistral-black/70 hover:text-mistral-black"
          >
            All {sources.length} sources Lume retrieved ({references.length} cited)
            <ChevronDown className={`w-4 h-4 transition-transform ${showRetrieved ? 'rotate-180' : ''}`} aria-hidden />
          </button>
          {showRetrieved && (
            <ul className="space-y-2">
              {sources.map((s, i) => (
                <li key={i} className="text-sm leading-relaxed">
                  {s.url.startsWith('http')
                    ? <a href={s.url} target="_blank" rel="noopener noreferrer" className="text-mistral-black hover:text-mistral-orange underline decoration-mistral-black/20 underline-offset-2">{s.title}</a>
                    : <span className="text-mistral-black">{s.title}</span>}
                  <span className="text-mistral-black/60"> · {s.url.startsWith('local://') ? 'Your library' : s.source}{s.year ? `, ${s.year}` : ''}</span>
                </li>
              ))}
            </ul>
          )}
        </section>
      )}
    </div>
  );
}
