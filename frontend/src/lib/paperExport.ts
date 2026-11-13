// Downloading a paper: Markdown (tables as tables, charts embedded, diagrams as Mermaid code) and LaTeX
// (a zip with figures/<id>.png when the paper has images, otherwise the .tex alone).
import type { Source } from './types';
import { type Paper, formatReference, toLatex } from './ieee';
import { type Numbering, FIGURE_LINE, figureSvg, isWide, resolveRefs, svgDataUrl, svgToPng } from './figures';

export function download(content: Blob | string, filename: string, type: string) {
  const url = URL.createObjectURL(content instanceof Blob ? content : new Blob([content], { type }));
  const a = Object.assign(document.createElement('a'), { href: url, download: filename });
  a.click();
  URL.revokeObjectURL(url);
}

const mdRow = (cells: string[]) => `| ${cells.map(c => c.replace(/\|/g, '\\|')).join(' | ')} |`;

function figureMarkdown(id: string, numbering: Numbering) {
  const entry = numbering.get(id);
  if (!entry) return '';
  const { figure, label } = entry;
  if (figure.kind === 'table' && figure.table) {
    const { columns, rows } = figure.table;
    return [`**${label}.** ${figure.caption}`, '', mdRow(columns), mdRow(columns.map(() => '---')), ...rows.map(mdRow)].join('\n');
  }
  if (figure.kind === 'chart' && figure.svg) return `![${label} ${figure.caption}](${svgDataUrl(figure.svg)})\n\n*${label} ${figure.caption}*`;
  if (figure.kind === 'diagram' && figure.mermaid) return `\`\`\`mermaid\n${figure.mermaid}\n\`\`\`\n\n*${label} ${figure.caption}*`;
  return '';
}

const bodyMarkdown = (body: string, numbering: Numbering) =>
  resolveRefs(body, numbering).split('\n').map(line => {
    const marker = line.match(FIGURE_LINE);
    return marker ? figureMarkdown(marker[1], numbering) : line;
  }).join('\n').trim();

export function paperMarkdown(paper: Paper, labels: string[], references: Source[], numbering: Numbering) {
  return [
    `# ${paper.title}`,
    paper.abstract && `**Abstract—** ${paper.abstract}`,
    paper.keywords && `**Index Terms—** ${paper.keywords}`,
    ...paper.sections.map((s, i) => `${s.level === 2 ? '##' : '###'} ${labels[i]} ${s.title}\n\n${bodyMarkdown(s.body, numbering)}`),
    `## References\n\n${references.map((r, i) => `[${i + 1}] ${formatReference(r)}`).join('\n\n')}`,
  ].filter(Boolean).join('\n\n') + '\n';
}

export async function downloadLatex(paper: Paper, references: Source[], numbering: Numbering, fileBase: string) {
  // Images first: a figure that can't be drawn is left out of the .tex, so it never points at a missing file
  const pngs = new Map<string, Blob>();
  const wide = new Set<string>();
  for (const { figure } of Array.from(numbering.values())) {
    if (figure.kind === 'table') continue;
    const svg = await figureSvg(figure).catch(() => null);
    const png = svg ? await svgToPng(svg).catch(() => null) : null;
    if (png) pngs.set(figure.id, png);
    if (png && svg && isWide(svg)) wide.add(figure.id);
  }
  const usable: Numbering = new Map(Array.from(numbering).filter(([id, { figure }]) => figure.kind === 'table' || pngs.has(id)));
  const tex = toLatex(paper, references, usable, wide);
  if (!pngs.size) {
    download(tex, `${fileBase}.tex`, 'application/x-tex');
    return;
  }
  const { default: JSZip } = await import('jszip');
  const zip = new JSZip();
  zip.file(`${fileBase}.tex`, tex);
  pngs.forEach((png, id) => zip.file(`figures/${id}.png`, png));
  download(await zip.generateAsync({ type: 'blob' }), `${fileBase}_latex.zip`, 'application/zip');
}
