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
    <div className="w-full max-w-4xl mx-auto mt-8 bg-gray-900/80 border border-gray-800 rounded-xl overflow-hidden shadow-2xl font-sans">
      <div className="bg-gray-950 px-4 py-3 border-b border-gray-800 flex items-center gap-2">
        <Terminal className="w-5 h-5 text-cyan-500" />
        <h3 className="text-gray-200 font-mono text-sm font-semibold">Backend Activity Logs</h3>
      </div>

      <div className="divide-y divide-gray-800/50">
        {/* Planner Logs */}
        {logs.searchQueries.length > 0 && (
          <div>
            <button 
              onClick={() => toggleSection('queries')}
              className="w-full px-6 py-4 flex items-center justify-between text-left hover:bg-gray-800/30 transition-colors"
            >
              <span className="text-cyan-400 font-medium font-sans">1. Planner Output ({logs.searchQueries.length} Search Queries)</span>
              {openSection === 'queries' ? <ChevronUp className="w-4 h-4 text-gray-500" /> : <ChevronDown className="w-4 h-4 text-gray-500" />}
            </button>
            {openSection === 'queries' && (
              <motion.div 
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                className="px-6 pb-4 pt-2 overflow-hidden"
              >
                <ul className="list-disc list-inside space-y-1 text-gray-300 font-mono text-xs">
                  {logs.searchQueries.map((q, i) => (
                    <li key={i}>{q}</li>
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
              className="w-full px-6 py-4 flex items-center justify-between text-left hover:bg-gray-800/30 transition-colors"
            >
              <span className="text-cyan-400 font-medium font-sans">2. Retriever Output ({logs.sources.length} Raw Sources)</span>
              {openSection === 'sources' ? <ChevronUp className="w-4 h-4 text-gray-500" /> : <ChevronDown className="w-4 h-4 text-gray-500" />}
            </button>
            {openSection === 'sources' && (
              <motion.div 
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                className="px-6 pb-4 pt-2 max-h-96 overflow-y-auto custom-scrollbar overflow-hidden"
              >
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
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
              className="w-full px-6 py-4 flex items-center justify-between text-left hover:bg-gray-800/30 transition-colors"
            >
              <span className="text-cyan-400 font-medium font-sans">3. Writer Output (Draft Report Preview)</span>
              {openSection === 'writer' ? <ChevronUp className="w-4 h-4 text-gray-500" /> : <ChevronDown className="w-4 h-4 text-gray-500" />}
            </button>
            {openSection === 'writer' && (
              <motion.div 
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                className="px-6 pb-4 pt-2 max-h-96 overflow-y-auto custom-scrollbar bg-gray-950/50 rounded-lg m-2 border border-gray-800/50 p-4 overflow-hidden"
              >
                <div className="prose prose-sm prose-invert max-w-none text-gray-300 opacity-80 font-sans">
                  <ReactMarkdown>{logs.draftReport}</ReactMarkdown>
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
              className="w-full px-6 py-4 flex items-center justify-between text-left hover:bg-gray-800/30 transition-colors"
            >
              <span className="text-cyan-400 font-medium font-sans">4. Critic Output (Final Refined Report)</span>
              {openSection === 'critic' ? <ChevronUp className="w-4 h-4 text-gray-500" /> : <ChevronDown className="w-4 h-4 text-gray-500" />}
            </button>
            {openSection === 'critic' && (
              <motion.div 
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                className="px-6 pb-4 pt-2 max-h-96 overflow-y-auto custom-scrollbar bg-cyan-950/20 rounded-lg m-2 border border-cyan-800/30 p-4 overflow-hidden"
              >
                <div className="prose prose-sm prose-invert max-w-none text-gray-200 font-sans">
                  <ReactMarkdown>{logs.refinedReport}</ReactMarkdown>
                </div>
              </motion.div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
