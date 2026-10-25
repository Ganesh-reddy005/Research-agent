import React from 'react';
import type { ProjectProfile } from '@/lib/types';
import { SectionLabel } from './ui';

const NOT_FOUND = 'Not found in the repository';

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="grid sm:grid-cols-[140px_1fr] gap-1 sm:gap-4">
      <dt className="text-sm font-semibold text-mistral-black/70">{label}</dt>
      <dd className="text-sm text-mistral-black/85 leading-relaxed">{children}</dd>
    </div>
  );
}

/** What Lume understood about the repository, so the author can correct it before planning. */
export default function ProjectSummary({ profile }: { profile: ProjectProfile }) {
  const stats = profile.stats;
  const languages = stats ? Object.keys(stats.languages).slice(0, 4).join(', ') : '';
  const list = (items?: string[]) => (items?.length ? items.join(', ') : NOT_FOUND);

  return (
    <section className="p-5 sm:p-6 border border-mistral-black/15 bg-mistral-beige/40 space-y-5">
      <div className="space-y-1">
        <SectionLabel>What Lume found in your repository</SectionLabel>
        <p className="text-base font-semibold text-mistral-black">
          <a href={profile.url} target="_blank" rel="noopener noreferrer" className="hover:text-mistral-orange underline decoration-mistral-black/20 underline-offset-2">
            {profile.name}
          </a>
          {profile.commit && <span className="text-sm font-normal text-mistral-black/60"> · {profile.branch} @ {profile.commit}</span>}
        </p>
        {stats && (
          <p className="text-sm text-mistral-black/65">
            {stats.files} files · {stats.lines.toLocaleString()} lines of code{languages && ` · ${languages}`}
          </p>
        )}
      </div>

      <dl className="space-y-3">
        {profile.summary && <Row label="What it does">{profile.summary}</Row>}
        {profile.approach && <Row label="Approach">{profile.approach}</Row>}
        {!!profile.architecture?.length && (
          <Row label="Components">
            <ul className="space-y-1">
              {profile.architecture.map(c => (
                <li key={c.component}><span className="font-semibold">{c.component}:</span> {c.role}</li>
              ))}
            </ul>
          </Row>
        )}
        <Row label="Tech stack">{list(profile.tech_stack)}</Row>
        <Row label="Results">{profile.evaluation || NOT_FOUND}</Row>
      </dl>

      <p className="text-xs text-mistral-black/60 leading-relaxed">
        The paper describes only what is here and what you tell Lume. If something is wrong or missing,
        such as results you measured outside the repository, say so in your answers below.
      </p>
    </section>
  );
}
