import React from 'react';
import { AlertTriangle, CircleCheck } from 'lucide-react';
import type { CitationAudit } from '@/lib/types';

/** Whether every [n] in the paper points to a source Lume retrieved. */
export default function CitationCheck({ audit, sourceCount }: { audit: CitationAudit; sourceCount: number }) {
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
