import React from 'react';

/** Mono section label, optionally tagged for capabilities that aren't shipped yet. */
export default function Eyebrow({ children, earlyAccess = false, dark = false }: {
  children: React.ReactNode;
  earlyAccess?: boolean;
  dark?: boolean;
}) {
  return (
    <div className={`flex flex-wrap items-center gap-3 font-mono text-[10px] font-bold uppercase tracking-[0.25em] ${dark ? 'text-white/50' : 'text-mistral-black/50'}`}>
      <span className="w-6 h-px bg-mistral-orange" aria-hidden />
      <span>{children}</span>
      {earlyAccess && (
        <span className="border border-mistral-orange text-mistral-orange px-2 py-0.5 tracking-[0.2em]">
          Early access
        </span>
      )}
    </div>
  );
}
