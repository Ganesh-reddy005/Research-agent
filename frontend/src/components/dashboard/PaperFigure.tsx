"use client";

import React, { useEffect, useState } from 'react';
import type { Numbering } from '@/lib/figures';
import { diagramSvg, isWide, svgDataUrl } from '@/lib/figures';

/** One figure or table in the IEEE layout. Images are shown as <img> from data URLs, so nothing in an
 *  SVG can run, and the printed PDF keeps them. A diagram that can't be drawn shows its caption only. */
export default function PaperFigure({ id, numbering }: { id: string; numbering: Numbering }) {
  const entry = numbering.get(id);
  const [diagram, setDiagram] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);
  const source = entry?.figure.kind === 'diagram' ? entry.figure.mermaid : undefined;

  useEffect(() => {
    if (!source) return;
    let live = true;
    diagramSvg(source).then(svg => live && setDiagram(svg)).catch(() => live && setFailed(true));
    return () => { live = false; };
  }, [source]);

  if (!entry) return null;
  const { figure, label } = entry;

  if (figure.kind === 'table' && figure.table) {
    const wide = figure.table.columns.length > 3;
    return (
      <figure className={`ieee-figure ieee-table-figure${wide ? ' ieee-wide' : ''}`} id={id}>
        <figcaption className="ieee-table-caption">{label}<br />{figure.caption}</figcaption>
        <table className="ieee-table">
          <thead><tr>{figure.table.columns.map((c, i) => <th key={i}>{c}</th>)}</tr></thead>
          <tbody>{figure.table.rows.map((row, r) => <tr key={r}>{row.map((c, i) => <td key={i}>{c}</td>)}</tr>)}</tbody>
        </table>
      </figure>
    );
  }

  const svg = figure.kind === 'chart' ? figure.svg : diagram;
  return (
    <figure className={`ieee-figure${svg && isWide(svg) ? ' ieee-wide' : ''}`} id={id}>
      {svg
        // eslint-disable-next-line @next/next/no-img-element -- an inline data URL: nothing for next/image to optimise
        ? <img src={svgDataUrl(svg)} alt={figure.caption} className={figure.kind === 'diagram' ? 'ieee-diagram' : undefined} />
        : !failed && <div className="ieee-figure-loading" aria-hidden />}
      <figcaption>{label} {figure.caption}</figcaption>
    </figure>
  );
}
