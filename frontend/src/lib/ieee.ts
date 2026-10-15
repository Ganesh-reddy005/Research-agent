// Typesetting a Lume paper in IEEE style: parsing, citation renumbering, reference
// formatting, LaTeX (IEEEtran) export and print-to-PDF.
import type { Source } from './types';

export type PaperSection = { level: 2 | 3; title: string; body: string };
export type Paper = { title: string; abstract: string; keywords: string; sections: PaperSection[] };

const NOT_SECTIONS = /^(references|bibliography|works cited|sources)$/i;

/** "I. Introduction", "1. Introduction", "Section 2: X" -> plain heading text. */
const cleanHeading = (text: string) =>
  text.replace(/\*\*/g, '').replace(/^(section\s+)?([IVXLC]+|\d+(\.\d+)*)[.):]?\s+/i, '').trim();

/** Split the model's Markdown into title, abstract, index terms and sections. */
export function parsePaper(markdown: string, fallbackTitle: string): Paper {
  let title = '';
  const sections: PaperSection[] = [];
  let current: PaperSection | null = null;

  for (const line of markdown.replace(/\r/g, '').split('\n')) {
    const heading = line.match(/^(#{1,4})\s+(.*?)\s*#*\s*$/);
    if (heading) {
      const text = cleanHeading(heading[2]);
      if (heading[1].length === 1 && !title) {
        title = text;
        continue;
      }
      current = { level: heading[1].length >= 3 ? 3 : 2, title: text, body: '' };
      sections.push(current);
    } else if (current) {
      current.body += line + '\n';
    }
  }

  const take = (pattern: RegExp) => {
    const i = sections.findIndex(s => pattern.test(s.title));
    return i === -1 ? '' : sections.splice(i, 1)[0].body.trim();
  };
  const abstract = take(/^abstract$/i);
  const keywords = take(/^(index terms|keywords)$/i);

  return {
    title: title || fallbackTitle,
    abstract,
    keywords: keywords.replace(/\.$/, ''),
    sections: sections.filter(s => !NOT_SECTIONS.test(s.title)),
  };
}

const CITATION = /\[(\d+(?:\s*,\s*\d+)*)\](?!\()/g;

/**
 * IEEE numbers references in order of first citation and lists only cited works.
 * Rewrites [7] -> [1] etc. and returns the cited sources in their new order.
 * Numbers that match no retrieved source become [?].
 */
export function renumberCitations(paper: Paper, sources: Source[]) {
  const newNumber = new Map<number, number>();
  const cited: Source[] = [];
  const rewrite = (text: string) =>
    text.replace(CITATION, (_, list: string) => {
      const nums = list.split(',').map(n => {
        const old = Number(n.trim());
        if (!sources[old - 1]) return '?';
        if (!newNumber.has(old)) {
          newNumber.set(old, cited.length + 1);
          cited.push(sources[old - 1]);
        }
        return String(newNumber.get(old));
      });
      return nums.map(n => `[${n}]`).join(', ');
    });

  const renumbered: Paper = {
    ...paper,
    abstract: rewrite(paper.abstract),
    sections: paper.sections.map(s => ({ ...s, body: rewrite(s.body) })),
  };
  return { paper: renumbered, references: cited };
}

const ROMAN: [number, string][] = [[10, 'X'], [9, 'IX'], [5, 'V'], [4, 'IV'], [1, 'I']];
export function roman(n: number) {
  let out = '';
  for (const [value, numeral] of ROMAN) while (n >= value) { out += numeral; n -= value; }
  return out;
}

/** Section numbering: I, II, III for sections; A, B, C for subsections within a section. */
export function sectionLabels(sections: PaperSection[]) {
  let major = 0, minor = 0;
  return sections.map(s => {
    if (s.level === 2) { major += 1; minor = 0; return `${roman(major)}.`; }
    minor += 1;
    return `${String.fromCharCode(64 + minor)}.`;
  });
}

/** "Ashish Vaswani" -> "A. Vaswani" */
const initials = (name: string) => {
  const parts = name.trim().split(/\s+/);
  if (parts.length < 2) return name.trim();
  return [...parts.slice(0, -1).map(p => `${p[0]}.`), parts[parts.length - 1]].join(' ');
};

function formatAuthors(authors: string[] = []) {
  if (!authors.length) return '';
  if (authors.length > 3) return `${initials(authors[0])} et al.`;
  const names = authors.map(initials);
  return names.length === 1 ? names[0] : `${names.slice(0, -1).join(', ')}${names.length > 2 ? ',' : ''} and ${names[names.length - 1]}`;
}

/** IEEE-style reference entry, as plain text: A. Author et al., “Title,” arXiv, 2026. [Online]. Available: url */
export function formatReference(s: Source) {
  const venue = s.url.startsWith('local://') ? 'Private library' : s.source === 'Web' ? '' : s.source;
  const parts = [formatAuthors(s.authors), `“${s.title}”`, venue, s.year ? String(s.year) : ''].filter(Boolean);
  // Commas between parts (inside the closing quote after a title), a period at the end
  let text = parts
    .map((part, i) => (i === parts.length - 1 ? part : part.endsWith('”') ? `${part.slice(0, -1)},”` : `${part},`))
    .join(' ');
  text = text.endsWith('”') ? `${text.slice(0, -1)}.”` : text.endsWith('.') ? text : `${text}.`;
  if (s.url.startsWith('http')) text += ` [Online]. Available: ${s.url}`;
  return text;
}

// ---------------------------------------------------------------------------------
// LaTeX (IEEEtran) export

const LATEX_SPECIALS: Record<string, string> = {
  '\\': '\\textbackslash{}', '&': '\\&', '%': '\\%', '$': '\\$', '#': '\\#', '_': '\\_',
  '{': '\\{', '}': '\\}', '~': '\\textasciitilde{}', '^': '\\textasciicircum{}',
};
const escapeLatex = (text: string) => text.replace(/[\\&%$#_{}~^]/g, c => LATEX_SPECIALS[c]);

function inlineToLatex(text: string) {
  const links: string[] = [];
  let out = text.replace(/\[([^\]]+)\]\((https?:[^)\s]+)\)/g, (_, label, url) => {
    links.push(`${escapeLatex(label)} (\\url{${url}})`);
    return `\u0000${links.length - 1}\u0000`;
  });
  out = escapeLatex(out)
    .replace(CITATION, (_, list: string) => `\\cite{${list.split(',').map(n => `ref${n.trim()}`).join(',')}}`)
    .replace(/\*\*(.+?)\*\*/g, '\\textbf{$1}')
    .replace(/\*(.+?)\*/g, '\\emph{$1}')
    .replace(/`(.+?)`/g, '\\texttt{$1}');
  return out.replace(/\u0000(\d+)\u0000/g, (_, i) => links[Number(i)]);
}

function blockToLatex(body: string) {
  const out: string[] = [];
  let list: 'itemize' | 'enumerate' | null = null;
  const closeList = () => { if (list) { out.push(`\\end{${list}}`); list = null; } };

  for (const line of body.split('\n')) {
    const bullet = line.match(/^\s*[-*]\s+(.*)/);
    const numbered = line.match(/^\s*\d+[.)]\s+(.*)/);
    const item = bullet || numbered;
    if (item) {
      const kind = bullet ? 'itemize' : 'enumerate';
      if (list !== kind) { closeList(); out.push(`\\begin{${kind}}`); list = kind; }
      out.push(`  \\item ${inlineToLatex(item[1])}`);
    } else {
      closeList();
      out.push(line.trim() ? inlineToLatex(line.trim()) : '');
    }
  }
  closeList();
  return out.join('\n').replace(/\n{3,}/g, '\n\n').trim();
}

export function toLatex(paper: Paper, references: Source[]) {
  const sections = paper.sections
    .map(s => `\\${s.level === 2 ? 'section' : 'subsection'}{${escapeLatex(s.title)}}\n${blockToLatex(s.body)}`)
    .join('\n\n');
  const bib = references
    .map((s, i) => `\\bibitem{ref${i + 1}} ${escapeLatex(formatReference(s).replace(/ \[Online\]\. Available: .*$/, ''))}${
      s.url.startsWith('http') ? ` [Online]. Available: \\url{${s.url}}` : ''}`)
    .join('\n');

  return `% Generated by Lume. Compile with pdflatex (e.g. in Overleaf).
\\documentclass[conference]{IEEEtran}
\\usepackage[utf8]{inputenc}
\\usepackage[T1]{fontenc}
\\usepackage{cite}
\\usepackage{url}

\\begin{document}

\\title{${escapeLatex(paper.title)}}

% TODO: replace with your name and affiliation
\\author{\\IEEEauthorblockN{Author Name}
\\IEEEauthorblockA{Affiliation \\\\ email@example.com}}

\\maketitle
${paper.abstract ? `\n\\begin{abstract}\n${blockToLatex(paper.abstract)}\n\\end{abstract}\n` : ''}${
  paper.keywords ? `\n\\begin{IEEEkeywords}\n${escapeLatex(paper.keywords)}\n\\end{IEEEkeywords}\n` : ''}
${sections}

\\begin{thebibliography}{${Math.max(references.length, 1)}}
${bib}
\\end{thebibliography}

\\end{document}
`;
}

// ---------------------------------------------------------------------------------
// Styles shared by the on-screen paper and the printed PDF

export const IEEE_CSS = `
.ieee-paper { font-family: "Times New Roman", Times, "Nimbus Roman", serif; color: #111; font-size: 15px; line-height: 1.45; }
.ieee-paper .ieee-title { font-size: 26px; font-weight: normal; text-align: center; line-height: 1.2; margin: 0 0 10px; }
.ieee-paper .ieee-byline { font-size: 13px; text-align: center; color: #444; margin: 0 0 26px; }
.ieee-paper .ieee-body { column-gap: 28px; }
@media (min-width: 1024px) { .ieee-paper .ieee-body { column-count: 2; } }
.ieee-paper p { text-align: justify; hyphens: auto; margin: 0 0 8px; text-indent: 1em; }
.ieee-paper .ieee-abstract, .ieee-paper .ieee-keywords { font-size: 13.5px; font-weight: bold; text-indent: 0; }
.ieee-paper .ieee-abstract em, .ieee-paper .ieee-keywords em { font-style: italic; }
.ieee-paper h2 { font-size: 15px; font-weight: normal; font-variant: small-caps; letter-spacing: 0.03em; text-align: center; margin: 20px 0 8px; break-after: avoid; }
.ieee-paper h3 { font-size: 15px; font-weight: normal; font-style: italic; margin: 14px 0 6px; break-after: avoid; }
.ieee-paper ul, .ieee-paper ol:not(.ieee-refs) { margin: 0 0 8px 1.4em; padding: 0; }
.ieee-paper ul { list-style: disc; } .ieee-paper ol:not(.ieee-refs) { list-style: decimal; }
.ieee-paper li p { text-indent: 0; margin: 0; }
.ieee-paper a { color: inherit; text-decoration: none; }
.ieee-paper a:hover { color: #ff511c; }
.ieee-paper .ieee-refs { list-style: none; margin: 0; padding: 0; font-size: 12.5px; line-height: 1.35; }
.ieee-paper .ieee-refs li { display: grid; grid-template-columns: 2.2em 1fr; margin-bottom: 5px; break-inside: avoid; }
.ieee-paper .ieee-refs a { word-break: break-all; }
@media print {
  @page { size: letter; margin: 0.75in 0.625in; }
  body { margin: 0; }
  .ieee-paper { font-size: 10pt; line-height: 1.3; }
  .ieee-paper .ieee-title { font-size: 22pt; }
  .ieee-paper .ieee-byline { font-size: 10pt; }
  .ieee-paper .ieee-body { column-count: 2; column-gap: 0.25in; }
  .ieee-paper .ieee-abstract, .ieee-paper .ieee-keywords { font-size: 9pt; }
  .ieee-paper h2, .ieee-paper h3 { font-size: 10pt; }
  .ieee-paper .ieee-refs { font-size: 8pt; }
}
`;

const escapeHtml = (text: string) =>
  text.replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]!));

/** Print the paper through the browser ("Save as PDF"): real text, IEEE two-column layout. */
export function printPaper(element: HTMLElement, title: string) {
  const iframe = document.createElement('iframe');
  Object.assign(iframe.style, { position: 'fixed', right: '0', bottom: '0', width: '0', height: '0', border: '0' });
  document.body.appendChild(iframe);
  const doc = iframe.contentDocument!;
  doc.open();
  doc.write(`<!doctype html><html><head><meta charset="utf-8"><title>${escapeHtml(title)}</title><style>${IEEE_CSS}</style></head><body>${element.outerHTML}</body></html>`);
  doc.close();
  // Give the document a moment to lay out before opening the print dialog
  setTimeout(() => {
    iframe.contentWindow!.focus();
    iframe.contentWindow!.print();
    setTimeout(() => iframe.remove(), 1000);
  }, 250);
}
