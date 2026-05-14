import React from 'react';
import { ExternalLink } from 'lucide-react';

interface SourceCardProps {
  source: {
    title: string;
    url: string;
    summary: string;
  };
  index: number;
}

export default function SourceCard({ source, index }: SourceCardProps) {
  return (
    <a 
      href={source.url} 
      target="_blank" 
      rel="noreferrer"
      className="block p-8 bg-white border border-mistral-border/30 shadow-sm rounded-3xl hover:border-mistral-orange/20 hover:shadow-xl transition-all active:scale-[0.98] group"
    >
      <div className="flex flex-col gap-6">
        <div className="flex items-center justify-between">
          <span className="text-[9px] font-bold font-mono text-mistral-orange bg-mistral-orange/5 px-4 py-1.5 uppercase tracking-[0.2em] rounded-lg border border-mistral-orange/10 italic">
            Reference Node [{index + 1}]
          </span>
          <ExternalLink className="w-4 h-4 text-mistral-black/10 group-hover:text-mistral-orange transition-colors" />
        </div>
        <div className="space-y-4">
          <h4 className="font-serif font-bold text-2xl text-mistral-black group-hover:text-mistral-orange transition-colors leading-tight tracking-tight">
            {source.title}
          </h4>
          <p className="text-xs font-sans text-mistral-black/40 line-clamp-2 leading-relaxed font-medium italic">
            {source.summary}
          </p>
        </div>
      </div>
    </a>
  );
}
