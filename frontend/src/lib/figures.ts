// Figures in a Lume paper: the text holds [[FIGURE:id]] lines and [[REF:id]] references (the backend
// guarantees each figure appears once, inside a body section). Here they are numbered in order of
// appearance (Fig. 1, 2 … and TABLE I, II … separately, as IEEE does), drawn, and turned into files.
import type { PaperFigure } from './types';
import type { Paper } from './ieee';
import { roman } from './numerals';

export const FIGURE_LINE = /^\s*\[\[FIGURE:([A-Za-z0-9_-]+)\]\]\s*$/;
export const FIGURE_REF = /\[\[REF:([A-Za-z0-9_-]+)\]\]/g;

export type Block = { kind: 'text'; text: string } | { kind: 'figure'; id: string };

/** A section body as text runs and figure markers, in order. */
export function splitBlocks(body: string): Block[] {
  const blocks: Block[] = [];
  let text: string[] = [];
  const flush = () => { if (text.join('').trim()) blocks.push({ kind: 'text', text: text.join('\n') }); text = []; };
  for (const line of body.split('\n')) {
    const marker = line.match(FIGURE_LINE);
    if (marker) { flush(); blocks.push({ kind: 'figure', id: marker[1] }); } else text.push(line);
  }
  flush();
  return blocks;
}

export type Numbering = Map<string, { label: string; ref: string; figure: PaperFigure }>;

/** Figure and table numbers by first appearance; markers for figures that don't exist are left out. */
export function numberFigures(paper: Paper, figures: PaperFigure[]): Numbering {
  const byId = new Map(figures.map(f => [f.id, f]));
  const numbering: Numbering = new Map();
  let fig = 0, tab = 0;
  for (const section of paper.sections) {
    for (const block of splitBlocks(section.body)) {
      const figure = block.kind === 'figure' ? byId.get(block.id) : undefined;
      if (!figure || numbering.has(figure.id)) continue;
      if (figure.kind === 'table') { tab += 1; numbering.set(figure.id, { label: `TABLE ${roman(tab)}`, ref: `Table ${roman(tab)}`, figure }); }
      else { fig += 1; numbering.set(figure.id, { label: `Fig. ${fig}.`, ref: `Fig. ${fig}`, figure }); }
    }
  }
  return numbering;
}

/** [[REF:id]] -> "Fig. 2" / "Table I" (or the given replacement); unknown ids read "the figure". */
export const resolveRefs = (text: string, numbering: Numbering, as?: (id: string, ref: string) => string) =>
  text.replace(FIGURE_REF, (_, id: string) => {
    const n = numbering.get(id);
    return n ? (as ? as(id, n.ref) : n.ref) : 'the figure';
  });

const WIDE_RATIO = 2.4;  // wider than this, a figure is unreadable in one column: it spans both (IEEE figure*)

/** Whether an SVG is so much wider than tall that it should span both columns. */
export function isWide(svg: string) {
  const box = (svg.match(/viewBox="([^"]+)"/)?.[1] ?? '').split(/[\s,]+/).map(Number);
  return box.length === 4 && box[3] > 0 && box[2] / box[3] > WIDE_RATIO;
}

/** The SVG with its viewBox size as width and height: Mermaid writes width="100%", which leaves an <img> no
 *  natural size, so it would stretch to the column whatever its shape. */
export function withNaturalSize(svg: string) {
  const box = (svg.match(/viewBox="([^"]+)"/)?.[1] ?? '').split(/[\s,]+/).map(Number);
  if (box.length !== 4 || !box[2] || !box[3]) return svg;
  return svg.replace(/<svg\b([^>]*)>/, (_, attrs: string) =>
    `<svg${attrs.replace(/\s(width|height)="[^"]*"/g, '').replace(/\sstyle="[^"]*"/, '')} width="${box[2]}" height="${box[3]}">`);
}

export const svgDataUrl = (svg: string) => `data:image/svg+xml;base64,${btoa(unescape(encodeURIComponent(svg)))}`;

// ---- Diagrams (Mermaid, loaded only when a paper has one) --------------------------------

const rendered = new Map<string, Promise<string>>();
let counter = 0;

/** The diagram's SVG, rendered once per source. Labels are plain SVG text (no HTML), so it prints and rasterises. */
export function diagramSvg(source: string): Promise<string> {
  if (!rendered.has(source)) {
    rendered.set(source, import('mermaid').then(async ({ default: mermaid }) => {
      mermaid.initialize({
        startOnLoad: false, securityLevel: 'strict', theme: 'neutral', fontFamily: 'Times New Roman, Times, serif',
        flowchart: { htmlLabels: false, curve: 'basis' }, themeVariables: { fontSize: '13px' },
      });
      const { svg } = await mermaid.render(`lume-diagram-${counter++}`, source);
      return withNaturalSize(svg);
    }));
  }
  return rendered.get(source)!;
}

/** The figure's SVG, whatever its kind (tables have none). */
export async function figureSvg(figure: PaperFigure): Promise<string | null> {
  if (figure.kind === 'chart' && figure.svg) return figure.svg;
  if (figure.kind === 'diagram' && figure.mermaid) return diagramSvg(figure.mermaid);
  return null;
}

/** A PNG of an SVG at print resolution (about 300 dpi at one IEEE column), for the LaTeX export. */
export async function svgToPng(svg: string, maxPixels = 2400): Promise<Blob> {
  const doc = new DOMParser().parseFromString(svg, 'image/svg+xml');
  const root = doc.documentElement;
  const box = (root.getAttribute('viewBox') || '').split(/[\s,]+/).map(Number);
  const width = box.length === 4 && box[2] ? box[2] : parseFloat(root.getAttribute('width') || '800');
  const height = box.length === 4 && box[3] ? box[3] : parseFloat(root.getAttribute('height') || '600');
  root.setAttribute('width', String(width));
  root.setAttribute('height', String(height));
  const image = new Image();
  image.src = svgDataUrl(new XMLSerializer().serializeToString(root));
  await image.decode();
  const scale = Math.min(maxPixels / Math.max(width, height), 4);
  const canvas = Object.assign(document.createElement('canvas'), { width: Math.round(width * scale), height: Math.round(height * scale) });
  const ctx = canvas.getContext('2d')!;
  ctx.fillStyle = '#fff';
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.drawImage(image, 0, 0, canvas.width, canvas.height);
  return new Promise((resolve, reject) => canvas.toBlob(b => (b ? resolve(b) : reject(new Error('PNG export failed'))), 'image/png'));
}
