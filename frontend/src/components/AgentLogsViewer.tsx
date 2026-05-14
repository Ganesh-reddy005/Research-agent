import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Terminal } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { motion } from 'framer-motion';
import SourceCard from './SourceCard';

interface AgentLogsViewerProps {
  logs: {
    searchQueries: string[];
    sources: any[];
    draftReport: string | null;
    refinedReport: string | null;
  };
}

export default function AgentLogsViewer({ logs }: AgentLogsViewerProps) {
  const [openSection, setOpenSection] = useState<string | null>('queries');

  const toggleSection = (section: string) => {
    setOpenSection(openSection === section ? null : section);
  };

  const hasLogs = logs.searchQueries.length > 0 || logs.sources.length > 0 || logs.draftReport || logs.refinedReport;

  if (!hasLogs) return null;

  return (
    <div className="w-full max-w-4xl mx-auto mt-12 bg-white border border-mistral-border/50 shadow-md rounded-[2.5rem] overflow-hidden">
      <div className="bg-white px-8 py-6 border-b border-mistral-border/50 flex items-center gap-3">
        <Terminal className="w-4 h-4 text-mistral-orange" />
        <h3 className="text-mistral-black font-sans text-xs font-bold uppercase tracking-[0.2em] italic">Backend Activity Logs // Trace Mode</h3>
      </div>

      <div className="divide-y divide-mistral-border/50">
        {/* Planner Logs */}
        {logs.searchQueries.length > 0 && (
          <div>
            <button 
              onClick={() => toggleSection('queries')}
              className="w-full px-10 py-6 flex items-center justify-between text-left hover:bg-mistral-beige/30 transition-all"
            >
              <span className="text-mistral-black font-bold font-sans text-sm tracking-tight">01. Planner Output ({logs.searchQueries.length} Search Queries)</span>
              {openSection === 'queries' ? <ChevronUp className="w-4 h-4 text-mistral-black/30" /> : <ChevronDown className="w-4 h-4 text-mistral-black/30" />}
            </button>
            {openSection === 'queries' && (
              <motion.div 
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                className="px-10 pb-8 pt-2 overflow-hidden"
              >
                <ul className="space-y-3 text-mistral-black/70 font-mono text-xs font-medium">
                  {logs.searchQueries.map((q, i) => (
                    <li key={i} className="flex gap-3">
                      <span className="text-mistral-orange/50">{">"}</span>
                      {q}
                    </li>
                  ))}
                </ul>
              </motion.div>
            )}
          </div>
        )}

        {/* Retriever Logs */}
        {logs.sources.length > 0 && (
          <div>
            <button 
              onClick={() => toggleSection('sources')}
              className="w-full px-10 py-6 flex items-center justify-between text-left hover:bg-mistral-beige/30 transition-all"
            >
              <span className="text-mistral-black font-bold font-sans text-sm tracking-tight">02. Retriever Output ({logs.sources.length} Raw Sources)</span>
              {openSection === 'sources' ? <ChevronUp className="w-4 h-4 text-mistral-black/30" /> : <ChevronDown className="w-4 h-4 text-mistral-black/30" />}
            </button>
            {openSection === 'sources' && (
              <motion.div 
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                className="px-10 pb-10 pt-2 max-h-96 overflow-y-auto custom-scrollbar overflow-hidden"
              >
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {logs.sources.map((src, i) => (
                    <SourceCard key={i} index={i} source={src} />
                  ))}
                </div>
              </motion.div>
            )}
          </div>
        )}

        {/* Draft Report Log */}
        {logs.draftReport && (
          <div>
            <button 
              onClick={() => toggleSection('writer')}
              className="w-full px-10 py-6 flex items-center justify-between text-left hover:bg-mistral-beige/30 transition-all"
            >
              <span className="text-mistral-black font-bold font-sans text-sm tracking-tight">03. Writer Output (Draft Report Preview)</span>
              {openSection === 'writer' ? <ChevronUp className="w-4 h-4 text-mistral-black/30" /> : <ChevronDown className="w-4 h-4 text-mistral-black/30" />}
            </button>
            {openSection === 'writer' && (
              <motion.div 
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                className="px-10 pb-10 pt-2 overflow-hidden"
              >
                <div className="max-h-96 overflow-y-auto custom-scrollbar bg-mistral-beige/10 border border-mistral-border/50 rounded-2xl p-8">
                  <div className="prose prose-sm max-w-none text-mistral-black font-medium leading-relaxed font-sans">
                    <ReactMarkdown>{logs.draftReport}</ReactMarkdown>
                  </div>
                </div>
              </motion.div>
            )}
          </div>
        )}

        {/* Critic/Final Log */}
        {logs.refinedReport && (
          <div>
            <button 
              onClick={() => toggleSection('critic')}
              className="w-full px-10 py-6 flex items-center justify-between text-left hover:bg-mistral-beige/30 transition-all"
            >
              <span className="text-mistral-black font-bold font-sans text-sm tracking-tight">04. Critic Output (Final Refined Report)</span>
              {openSection === 'critic' ? <ChevronUp className="w-4 h-4 text-mistral-black/30" /> : <ChevronDown className="w-4 h-4 text-mistral-black/30" />}
            </button>
            {openSection === 'critic' && (
              <motion.div 
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                className="px-10 pb-10 pt-2 overflow-hidden"
              >
                <div className="max-h-[32rem] overflow-y-auto custom-scrollbar bg-mistral-orange/5 border border-mistral-orange/20 rounded-2xl p-10">
                  <div className="prose prose-sm max-w-none text-mistral-black font-medium leading-relaxed font-sans">
                    <ReactMarkdown>{logs.refinedReport}</ReactMarkdown>
                  </div>
                </div>
              </motion.div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
