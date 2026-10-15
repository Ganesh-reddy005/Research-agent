"use client";

import React, { useMemo, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { AlertTriangle, ChevronDown, CircleCheck, Download, FileCode2, FileText } from 'lucide-react';
import type { CitationAudit, Source } from '@/lib/types';
import {
  IEEE_CSS, formatReference, parsePaper, printPaper, renumberCitations, sectionLabels, toLatex,
} from '@/lib/ieee';
import { Button } from './ui';

// [3] -> link to reference 3 ([?] and real markdown links are left alone)
const linkCitations = (md: string) => md.replace(/\[(\d+)\](?!\()/g, '[[$1]](#ref-$1)');

const link = ({ href, children }: { href?: string; children?: React.ReactNode }) =>
  href?.startsWith('#ref-')
    ? <a href={href}>{children}</a>
    : <a href={href} target="_blank" rel="noopener noreferrer">{children}</a>;

/** Paragraph-level Markdown inside the IEEE layout. */
function Body({ text }: { text: string }) {
  return <ReactMarkdown components={{ a: link }}>{linkCitations(text)}</ReactMarkdown>;
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
          ? `${invalid.length} citation${invalid.length > 1 ? 's' : ''} ${invalid.length > 1 ? "don't" : "doesn't"} match any of the ${sourceCount} retrieved sources and ${invalid.length > 1 ? 'are' : 'is'} shown as [?] in the paper. Treat ${invalid.length > 1 ? 'them' : 'it'} as unverified.`
          : audit.total_citations_found > 0 && 'Every citation points to a source Lume actually retrieved.'}
      </p>
      <p className="text-xs text-mistral-black/60 leading-relaxed">
        This check confirms each citation points to a real retrieved source. It does not yet confirm that the source
        supports the sentence it is attached to, so review key claims before submitting.
      </p>
    </section>
  );
}

function download(content: string, filename: string, type: string) {
  const url = URL.createObjectURL(new Blob([content], { type }));
  const a = Object.assign(document.createElement('a'), { href: url, download: filename });
  a.click();
  URL.revokeObjectURL(url);
}

export default function StageCompleted({ topic, report, sources, audit, reportRef, threadId }: {
  topic: string;
  report: string;
  sources: Source[];
  audit?: CitationAudit;
  reportRef: React.RefObject<HTMLDivElement>;
  threadId: string | null;
}) {
  const [showRetrieved, setShowRetrieved] = useState(false);
  // IEEE: references numbered by first citation, cited works only
  const { paper, references } = useMemo(() => renumberCitations(parsePaper(report, topic), sources), [report, topic, sources]);
  const labels = sectionLabels(paper.sections);
  const fileBase = `Lume_${(threadId ?? 'paper').slice(0, 8)}`;
  const date = new Date().toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' });

  const downloadMarkdown = () => {
    const body = [
      `# ${paper.title}`,
      paper.abstract && `**Abstract—** ${paper.abstract}`,
      paper.keywords && `**Index Terms—** ${paper.keywords}`,
      ...paper.sections.map((s, i) => `${s.level === 2 ? '##' : '###'} ${labels[i]} ${s.title}\n\n${s.body.trim()}`),
      `## References\n\n${references.map((r, i) => `[${i + 1}] ${formatReference(r)}`).join('\n\n')}`,
    ].filter(Boolean).join('\n\n');
    download(body + '\n', `${fileBase}.md`, 'text/markdown');
  };

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-center gap-3 sm:justify-between">
        <p className="text-sm text-mistral-black/65">Your draft is ready, typeset in IEEE style.</p>
        <div className="flex flex-wrap gap-2">
          <Button variant="secondary" onClick={downloadMarkdown}>
            <FileText className="w-4 h-4" aria-hidden /> Markdown
          </Button>
          <Button variant="secondary" onClick={() => download(toLatex(paper, references), `${fileBase}.tex`, 'application/x-tex')}>
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
                <Body text={s.body} />
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
