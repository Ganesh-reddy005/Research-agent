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
      className="block p-4 glass rounded-xl hover:bg-white/10 transition-colors border border-white/5 hover:border-cyan-500/30 group"
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <span className="inline-block text-xs font-semibold text-cyan-400 bg-cyan-950/50 px-2 py-1 rounded mb-2">
            [{index + 1}]
          </span>
          <h4 className="font-semibold text-gray-200 group-hover:text-cyan-300 transition-colors line-clamp-1">
            {source.title}
          </h4>
          <p className="text-sm text-gray-400 mt-2 line-clamp-2">
            {source.summary}
          </p>
        </div>
        <ExternalLink className="w-5 h-5 text-gray-500 group-hover:text-cyan-400 flex-shrink-0" />
      </div>
    </a>
  );
}
