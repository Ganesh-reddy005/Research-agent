"use client";

import React from 'react';
import { motion } from 'framer-motion';
import { ShieldCheck, AlertCircle, Loader2 } from 'lucide-react';

interface StageCompletedProps {
  report: string;
  allSources: any[];
  auditLog: any;
  reportRef: React.RefObject<HTMLDivElement>;
}

export default function StageCompleted({ report, allSources, auditLog, reportRef }: StageCompletedProps) {
  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-16 pb-40 py-8 max-w-4xl mx-auto px-4">
      <div ref={reportRef} className="bg-white p-12 md:p-24 border border-mistral-black/5 shadow-sm relative">
        {/* Auditor Status Badge */}
        <div className="absolute top-8 right-8">
           {auditLog ? (
             <motion.div 
               initial={{ opacity: 0 }}
               animate={{ opacity: 1 }}
               className={`flex items-center gap-2 px-4 py-1.5 border text-[8px] font-bold font-mono uppercase tracking-widest ${auditLog.invalid_citations?.length > 0 ? 'bg-red-500 text-white border-red-600' : 'bg-mistral-orange text-white border-mistral-orange'}`}
             >
               {auditLog.invalid_citations?.length > 0 ? <AlertCircle className="w-3 h-3" /> : <ShieldCheck className="w-3 h-3" />}
               {auditLog.invalid_citations?.length > 0 ? 'Integrity Failure' : 'Integrity Verified'}
             </motion.div>
           ) : (
             <div className="flex items-center gap-2 px-4 py-1.5 border border-mistral-black/5 bg-mistral-beige text-mistral-black/30 text-[8px] font-bold font-mono uppercase tracking-widest">
               <Loader2 className="w-3 h-3 animate-spin" />
               Auditing Metadata...
             </div>
           )}
        </div>

        <div className="mb-20 space-y-4">
          <div className="text-[9px] font-bold font-mono uppercase tracking-[0.4em] text-mistral-black/20">Technical Publication / 0x4f2a</div>
          <div className="h-[1px] w-12 bg-mistral-orange" />
        </div>
        
        <article className="max-w-2xl mx-auto">
          {report.split('\n').map((line, i) => {
            if (line.startsWith('## ')) return <h2 key={i} className="text-3xl text-mistral-black mt-20 mb-8 font-serif font-bold tracking-tight border-b border-mistral-black/5 pb-6">{line.replace('## ', '')}</h2>;
            if (line.startsWith('### ')) return <h3 key={i} className="text-xl text-mistral-black mt-12 mb-6 font-serif font-bold tracking-tight">{line.replace('### ', '')}</h3>;
            if (!line.trim()) return <div key={i} className="h-4" />;
            return <p key={i} className="text-mistral-black/80 leading-[1.7] mb-8 text-lg font-serif text-justify">{line}</p>;
          })}

          {/* Verification Panel */}
          {auditLog && (
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="mt-24 p-10 border border-mistral-black/5 bg-[#F5F2ED]/20 space-y-10"
            >
               <div className="flex justify-between items-end">
                  <div className="space-y-2">
                    <h3 className="text-2xl font-serif font-bold tracking-tight text-mistral-black uppercase">Integrity Report</h3>
                    <p className="text-[8px] text-mistral-black/30 font-bold font-mono uppercase tracking-widest">Automated source-mapping validation</p>
                  </div>
                  <div className="flex gap-10">
                     <div className="text-right">
                        <div className="text-[8px] font-bold font-mono text-mistral-black/30 uppercase tracking-widest mb-1">Citations</div>
                        <div className="text-3xl font-mono font-bold text-mistral-orange">{auditLog.total_citations_found}</div>
                     </div>
                     <div className="text-right">
                        <div className="text-[8px] font-bold font-mono text-mistral-black/30 uppercase tracking-widest mb-1">Verified</div>
                        <div className="text-3xl font-mono font-bold text-mistral-orange">{auditLog.unique_sources_cited}</div>
                     </div>
                  </div>
               </div>
               
               {auditLog.invalid_citations?.length > 0 ? (
                  <div className="p-6 border-l-2 border-red-500 bg-red-50/30 text-red-900 flex gap-6 items-start">
                     <AlertCircle className="w-5 h-5 shrink-0 text-red-500" />
                     <div className="space-y-2">
                        <div className="text-[9px] font-bold font-mono uppercase tracking-widest text-red-600">Traceability Error</div>
                        <p className="text-base font-serif italic">The agent collective failed to ground specific claims. Critical audit required.</p>
                     </div>
                  </div>
               ) : (
                  <div className="p-8 border-l-2 border-mistral-orange bg-white text-mistral-black flex gap-6 items-start">
                     <ShieldCheck className="w-6 h-6 shrink-0 text-mistral-orange" />
                     <div className="space-y-2">
                        <div className="text-[9px] font-bold font-mono uppercase tracking-widest text-mistral-orange/60">Source Grounding Success</div>
                        <p className="text-base font-serif italic text-mistral-black/70">Every technical claim within this manuscript is programmatically anchored to validated corpus materials.</p>
                     </div>
                  </div>
               )}
            </motion.div>
          )}

          {/* Reference Library */}
          {allSources.length > 0 && (
            <div className="mt-40 pt-20 border-t border-mistral-black/5">
              <h2 className="text-2xl font-serif font-bold tracking-tight mb-16 text-mistral-black text-center uppercase">Reference Library</h2>
              <div className="space-y-6">
                {allSources.slice(0, 20).map((src, i) => (
                  <div key={i} className="p-8 bg-white border border-mistral-black/5 flex gap-8 group hover:border-mistral-orange/30 transition-all">
                    <span className="font-bold text-mistral-orange/30 font-mono text-xl group-hover:text-mistral-orange transition-colors">[{String(i + 1).padStart(2, '0')}]</span>
                    <div className="space-y-3">
                      <span className="text-mistral-black font-serif font-bold text-xl leading-snug tracking-tight group-hover:text-mistral-orange transition-colors cursor-pointer">{src.title}</span> 
                      <div className="flex items-center gap-4 font-mono text-[8px] font-bold">
                        <span className="px-3 py-1 bg-mistral-black text-white uppercase tracking-widest">{src.source}</span>
                        <span className="text-mistral-black/20 truncate max-w-xs">{src.url}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </article>
      </div>
    </motion.div>
  );
}
