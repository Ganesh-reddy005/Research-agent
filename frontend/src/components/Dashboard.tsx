"use client";

import React, { useState, useEffect, useRef } from 'react';
import { 
  Search, 
  Send, 
  ChevronRight, 
  Loader2, 
  AlertCircle,
  FileText,
  Activity,
  Layers,
  Sparkles,
  Download,
  ChevronDown,
  ChevronUp,
  Book,
  Database,
  Cpu,
  CheckCircle,
  FileSearch,
  Zap,
  Flame
} from 'lucide-react';
import { startResearch, resumeResearch } from '@/lib/api';
import { motion, AnimatePresence } from 'framer-motion';

// --- Types ---
type Stage = 'idle' | 'clarification' | 'planning' | 'researching' | 'reviewing' | 'completed';
type ResearchMode = 'light' | 'deep';

export default function Dashboard() {
  const [topic, setTopic] = useState('');
  const [stage, setStage] = useState<Stage>('idle');
  const [researchMode, setResearchMode] = useState<ResearchMode>('deep');
  const [threadId, setThreadId] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  
  // State from backend
  const [questions, setQuestions] = useState<any[]>([]);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [plan, setPlan] = useState<any>(null);
  const [brief, setBrief] = useState('');
  const [logs, setLogs] = useState<any[]>([]);
  const [report, setReport] = useState('');
  const [allSources, setAllSources] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [expandedLog, setExpandedLog] = useState<number | null>(null);
  
  // Streaming Thought
  const [activeThought, setActiveThought] = useState<{agent: string, text: string} | null>(null);
  
  const scrollRef = useRef<HTMLDivElement>(null);
  const reportRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs, activeThought]);

  const callbacks = {
    onStep: (step: string, state: any, tid: string) => {
      setThreadId(tid);
      console.log(`Step: ${step}`, state);
      
      if (state.clarification_questions) setQuestions(state.clarification_questions);
      if (state.research_plan) setPlan(state.research_plan);
      if (state.research_brief) setBrief(state.research_brief);
      if (state.final_report) setReport(state.final_report);
      if (state.raw_sources) setAllSources(state.raw_sources);
      
      // Clear thought when step ends
      setActiveThought(null);
      
      // Add to logs
      setLogs(prev => [...prev, { step, timestamp: new Date().toLocaleTimeString(), data: state }]);
    },
    onThought: (agent: string, token: string) => {
      setActiveThought(prev => ({
        agent: agent,
        text: (prev?.agent === agent ? prev.text : '') + token
      }));
    },
    onInterrupt: (tid: string, next: string[]) => {
      setThreadId(tid);
      setIsProcessing(false);
      if (next.includes('planning')) setStage('clarification');
      if (next.includes('retriever')) setStage('planning');
    },
    onDone: (tid: string) => {
      setStage('completed');
      setIsProcessing(false);
    },
    onError: (err: string) => {
      setError(err);
      setIsProcessing(false);
    }
  };

  const handleStart = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!topic.trim()) return;
    
    setStage('researching');
    setIsProcessing(true);
    setError(null);
    setLogs([]);
    setReport('');
    setAllSources([]);
    
    await startResearch(topic, callbacks, researchMode);
  };

  const handleAnswerSubmit = async () => {
    setIsProcessing(true);
    await resumeResearch(threadId!, 'answer', { answers }, callbacks);
  };

  const handlePlanApprove = async () => {
    setStage('researching');
    setIsProcessing(true);
    await resumeResearch(threadId!, 'approve', { approved: true, mode: researchMode }, callbacks);
  };

  const handleExport = () => {
    if (!reportRef.current) return;
    const html2pdf = (window as any).html2pdf;
    if (!html2pdf) {
      alert("PDF exporter loading. Please try again in a moment.");
      return;
    }

    const opt = {
      margin: 1,
      filename: `Research_Report_${threadId?.slice(0, 8)}.pdf`,
      image: { type: 'jpeg', quality: 0.98 },
      html2canvas: { scale: 2 },
      jsPDF: { unit: 'in', format: 'letter', orientation: 'portrait' }
    };

    html2pdf().set(opt).from(reportRef.current).save();
  };

  // Helper to get icon for agent
  const getAgentIcon = (name: string) => {
    switch (name.toLowerCase()) {
      case 'clarification': return <FileSearch className="w-4 h-4" />;
      case 'planning': return <Layers className="w-4 h-4" />;
      case 'retriever': return <Search className="w-4 h-4" />;
      case 'indexer': return <Database className="w-4 h-4" />;
      case 'synthesis': return <Cpu className="w-4 h-4" />;
      case 'writer': return <Book className="w-4 h-4" />;
      case 'critic': return <CheckCircle className="w-4 h-4" />;
      case 'refinement': return <Sparkles className="w-4 h-4" />;
      default: return <Activity className="w-4 h-4" />;
    }
  };

  return (
    <div className="flex h-screen bg-parchment overflow-hidden selection:bg-sage/30">
      {/* --- External Scripts --- */}
      <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js" async />

      {/* --- Left Panel: Sidebar / History --- */}
      <aside className="w-64 border-r border-parchment-dark bg-parchment-dark/50 flex flex-col">
        <div className="p-6">
          <div className="flex items-center gap-2 text-deep-green font-serif text-xl font-bold">
            <Sparkles className="w-6 h-6" />
            <span>Research AI</span>
          </div>
        </div>
        
        <nav className="flex-1 px-4 space-y-1">
          <button 
            onClick={() => { setStage('idle'); setTopic(''); setLogs([]); setReport(''); setAllSources([]); }}
            className="flex items-center gap-3 w-full p-2 rounded-lg bg-white/50 text-deep-green shadow-sm border border-parchment-dark text-sm hover:bg-white transition-colors"
          >
            <Zap className="w-4 h-4" />
            <span>New Session</span>
          </button>
          <div className="pt-6 pb-2 px-2 text-[10px] uppercase tracking-wider text-gray-400 font-bold">Recently Refined</div>
          <div className="space-y-1">
            {['Quantum Encryption', 'Graphene Synthesis', 'LLM Agentic Workflows'].map(t => (
              <button key={t} className="flex items-center gap-3 w-full p-2 rounded-lg text-gray-500 hover:bg-white/30 text-xs text-left truncate">
                <FileText className="w-3.5 h-3.5" />
                {t}
              </button>
            ))}
          </div>
        </nav>
      </aside>

      {/* --- Center: Main Content --- */}
      <main className="flex-1 flex flex-col relative overflow-y-auto">
        <header className="h-16 flex items-center justify-between px-8 border-b border-parchment-dark sticky top-0 bg-parchment/80 backdrop-blur-md z-10">
          <div className="text-xs text-gray-400 font-medium tracking-wide">
            {stage === 'idle' ? 'System Discovery' : `Session: ${threadId?.slice(0, 8)}...`}
          </div>
          <div className="flex items-center gap-4">
            {stage === 'completed' && (
              <button 
                onClick={handleExport}
                className="flex items-center gap-2 px-4 py-2 bg-deep-green text-white rounded-full text-xs font-bold hover:bg-deep-green-hover transition-all shadow-lg shadow-deep-green/20"
              >
                <Download className="w-3.5 h-3.5" />
                Export IEEE PDF
              </button>
            )}
          </div>
        </header>

        <div className="flex-1 max-w-4xl mx-auto w-full p-12 space-y-12">
          {stage === 'idle' ? (
            <div className="h-[70vh] flex flex-col items-center justify-center space-y-8">
              <div className="text-center space-y-4">
                <h1 className="text-6xl font-serif text-deep-green leading-tight">
                  Accelerate your <br /> <span className="italic">intellectual discovery.</span>
                </h1>
                <p className="text-gray-500 italic font-serif text-lg">Cross-reference 50+ academic sources in seconds.</p>
              </div>
              
              <div className="w-full max-w-xl space-y-6">
                <form onSubmit={handleStart} className="relative group">
                  <input 
                    type="text" 
                    value={topic}
                    onChange={e => setTopic(e.target.value)}
                    placeholder="Describe your research topic in technical detail..."
                    className="w-full px-8 py-6 rounded-3xl bg-white border border-parchment-dark shadow-2xl shadow-sage/10 focus:ring-2 focus:ring-sage focus:outline-none text-xl transition-all group-hover:shadow-sage/20 font-serif"
                  />
                  <button type="submit" className="absolute right-4 top-1/2 -translate-y-1/2 p-3 bg-deep-green text-white rounded-2xl hover:bg-deep-green-hover transition-all active:scale-95">
                    <ChevronRight className="w-6 h-6" />
                  </button>
                </form>

                <div className="flex items-center justify-center gap-4 bg-white/50 p-2 rounded-2xl border border-parchment-dark w-fit mx-auto shadow-sm">
                  <button 
                    onClick={() => setResearchMode('light')}
                    className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all ${researchMode === 'light' ? 'bg-white text-deep-green shadow-sm border border-parchment-dark' : 'text-gray-400 hover:text-gray-600'}`}
                  >
                    <Zap className="w-3.5 h-3.5" />
                    Light Search (15 Papers)
                  </button>
                  <button 
                    onClick={() => setResearchMode('deep')}
                    className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all ${researchMode === 'deep' ? 'bg-white text-deep-green shadow-sm border border-parchment-dark' : 'text-gray-400 hover:text-gray-600'}`}
                  >
                    <Flame className="w-3.5 h-3.5" />
                    Deep Research (50+ Papers)
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <AnimatePresence mode="wait">
              {stage === 'clarification' && (
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-12">
                  <div className="space-y-4">
                    <h2 className="text-4xl font-serif text-deep-green">Session Alignment</h2>
                    <p className="text-gray-500 italic border-l-2 border-sage pl-4">To ensure academic precision, I need to refine the investigation parameters.</p>
                  </div>
                  
                  <div className="space-y-8">
                    {questions.map((q, i) => (
                      <div key={q.id} className="space-y-3">
                        <label className="text-[10px] font-bold text-sage uppercase tracking-widest flex items-center gap-2">
                          <span className="w-5 h-5 rounded-full bg-sage/10 flex items-center justify-center text-[10px] border border-sage/20">{i+1}</span>
                          {q.question}
                        </label>
                        <input 
                          type="text" 
                          placeholder="Provide context..."
                          className="w-full bg-transparent border-b border-parchment-dark focus:border-sage py-3 outline-none text-deep-green text-lg italic font-serif transition-colors"
                          onChange={e => setAnswers({ ...answers, [q.id]: e.target.value })}
                        />
                      </div>
                    ))}
                  </div>

                  <button 
                    onClick={handleAnswerSubmit}
                    disabled={isProcessing}
                    className="w-full sm:w-auto px-10 py-4 bg-deep-green text-white rounded-2xl hover:bg-deep-green-hover disabled:bg-gray-300 shadow-xl shadow-deep-green/20 transition-all font-bold tracking-wider text-sm flex items-center justify-center gap-3"
                  >
                    {isProcessing ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
                    Lock Scopes & Proceed
                  </button>
                </motion.div>
              )}

              {stage === 'planning' && (
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-12">
                  <div className="space-y-3">
                    <h2 className="text-4xl font-serif text-deep-green">Structural Blueprint</h2>
                    <p className="text-gray-500 font-serif italic text-lg">Proposed architecture for the final paper.</p>
                  </div>

                  <div className="bg-white border border-parchment-dark rounded-[2.5rem] shadow-2xl shadow-sage/5 overflow-hidden">
                    <div className="p-8 border-b border-parchment-dark/50 bg-parchment-dark/10">
                      <h3 className="text-[10px] font-bold text-gray-400 uppercase tracking-[0.2em] mb-4">Research Brief</h3>
                      <p className="text-gray-700 leading-relaxed font-serif text-lg leading-loose">{brief}</p>
                    </div>
                    
                    <div className="p-8 space-y-6">
                      <h3 className="text-[10px] font-bold text-gray-400 uppercase tracking-[0.2em]">Validated Sections</h3>
                      <div className="grid gap-4">
                        {plan?.sections?.map((s: any, i: number) => (
                          <div key={i} className="flex gap-6 p-6 rounded-3xl bg-parchment/30 border border-transparent hover:border-sage/20 transition-all duration-300 group">
                            <div className="text-2xl font-serif text-sage opacity-20 group-hover:opacity-60 transition-opacity">0{i+1}</div>
                            <div className="space-y-1">
                              <div className="font-bold text-deep-green text-lg">{s.title}</div>
                              <div className="text-sm text-gray-500 font-serif leading-relaxed line-clamp-2">{s.description}</div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="flex flex-col sm:flex-row gap-4">
                    <button 
                      onClick={handlePlanApprove}
                      disabled={isProcessing}
                      className="px-10 py-5 bg-deep-green text-white rounded-2xl hover:bg-deep-green-hover disabled:bg-gray-300 shadow-2xl shadow-deep-green/20 font-bold tracking-widest text-xs uppercase"
                    >
                      Initialize Full Extraction
                    </button>
                    <button className="px-10 py-5 border-2 border-parchment-dark bg-white rounded-2xl hover:border-sage/40 text-gray-500 text-xs font-bold uppercase tracking-widest transition-all">
                      Adjust Methodology
                    </button>
                  </div>
                </motion.div>
              )}

              {(stage === 'researching' && isProcessing) && (
                <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-8">
                  <div className="flex items-center justify-between bg-white/80 backdrop-blur-md border border-parchment-dark p-6 rounded-[2rem] shadow-xl">
                    <div className="flex items-center gap-4">
                      <div className="p-3 bg-deep-green text-white rounded-2xl animate-pulse">
                        {getAgentIcon(activeThought?.agent || 'system')}
                      </div>
                      <div>
                        <div className="text-[10px] font-bold text-sage uppercase tracking-widest">Active Intelligence</div>
                        <div className="text-xl font-serif text-deep-green capitalize">{activeThought?.agent || 'System'} is working...</div>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Loader2 className="w-5 h-5 text-sage animate-spin" />
                    </div>
                  </div>

                  <div className="bg-white border border-parchment-dark rounded-[3rem] shadow-2xl p-10 min-h-[50vh] relative overflow-hidden group">
                    <div className="absolute top-0 left-0 w-full h-1 bg-parchment-dark">
                      <motion.div 
                        className="h-full bg-deep-green"
                        animate={{ width: ['0%', '100%'] }}
                        transition={{ duration: 10, repeat: Infinity }}
                      />
                    </div>
                    
                    <div className="prose prose-stone max-w-none font-serif">
                      <div className="text-xs font-bold text-gray-300 uppercase tracking-widest mb-8 flex items-center gap-2">
                        <Zap className="w-3 h-3" />
                        Live Streamed Intelligence
                      </div>
                      
                      {activeThought ? (
                        <div className="text-gray-800 leading-[2] text-xl whitespace-pre-wrap animate-in fade-in slide-in-from-bottom-2 duration-500">
                          {activeThought.text}
                          <span className="inline-block w-2 h-5 bg-deep-green ml-1 animate-pulse" />
                        </div>
                      ) : (
                        <div className="h-full flex flex-col items-center justify-center py-20 opacity-30 italic font-serif">
                          Waiting for agent signals...
                        </div>
                      )}
                    </div>
                  </div>
                </motion.div>
              )}

              {(stage === 'completed' || (stage === 'reviewing' && report)) && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-16 pb-32">
                  <div ref={reportRef} className="prose prose-stone max-w-none font-serif bg-white p-12 md:p-20 rounded-[3rem] shadow-2xl border border-parchment-dark">
                    <div className="text-center mb-16 space-y-4">
                      <div className="text-xs font-bold uppercase tracking-[0.3em] text-sage">Technical Manuscript</div>
                      <div className="h-px w-24 bg-sage/30 mx-auto" />
                    </div>
                    
                    {report.split('\n').map((line, i) => {
                      if (line.startsWith('## ')) return <h2 key={i} className="text-3xl text-deep-green mt-16 mb-8 border-b border-parchment-dark pb-3 font-serif italic">{line.replace('## ', '')}</h2>;
                      if (line.startsWith('### ')) return <h3 key={i} className="text-xl text-deep-green mt-12 mb-6 font-bold">{line.replace('### ', '')}</h3>;
                      if (!line.trim()) return <br key={i} />;
                      return <p key={i} className="text-gray-800 leading-[2.2] mb-8 text-lg indent-8">{line}</p>;
                    })}

                    {/* --- Reference Gallery inside Report (for PDF) --- */}
                    {allSources.length > 0 && (
                      <div className="mt-24 pt-12 border-t-2 border-parchment-dark border-dashed">
                        <h2 className="text-2xl font-serif italic mb-8">References & Research Methodology</h2>
                        <div className="grid gap-6">
                          {allSources.slice(0, 15).map((src, i) => (
                            <div key={i} className="text-sm text-gray-600 font-serif leading-relaxed">
                              [{i+1}] "{src.title}". Retrieved from <span className="underline italic text-sage">{src.url}</span>. ({src.source})
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          )}
        </div>
      </main>

      {/* --- Right Panel: Agent Discovery Lab --- */}
      <aside className="w-[22rem] border-l border-parchment-dark bg-white flex flex-col shadow-inner">
        <div className="p-8 border-b border-parchment-dark flex items-center justify-between bg-parchment-dark/5">
          <div className="text-[10px] font-bold text-gray-400 uppercase tracking-[0.2em] flex items-center gap-3">
            <Activity className="w-4 h-4 text-sage" />
            Agent Signals
          </div>
          {isProcessing && (
            <div className="flex gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-sage animate-bounce [animation-delay:-0.3s]" />
              <span className="w-1.5 h-1.5 rounded-full bg-sage animate-bounce [animation-delay:-0.15s]" />
              <span className="w-1.5 h-1.5 rounded-full bg-sage animate-bounce" />
            </div>
          )}
        </div>
        
        <div ref={scrollRef} className="flex-1 overflow-y-auto p-6 space-y-6 bg-parchment-dark/5">
          {/* --- Live Thought Stream --- */}
          {activeThought && (
            <motion.div 
              initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }}
              className="p-5 rounded-[1.5rem] bg-deep-green text-white/90 shadow-2xl shadow-deep-green/20"
            >
              <div className="flex items-center gap-2 mb-3">
                <div className="p-1 hex-bg rounded-lg bg-white/10">{getAgentIcon(activeThought.agent)}</div>
                <div className="text-[9px] font-bold uppercase tracking-widest">{activeThought.agent} thinking...</div>
              </div>
              <div className="text-xs font-serif leading-relaxed italic opacity-80 break-words line-clamp-6">
                {activeThought.text}
              </div>
            </motion.div>
          )}

          {logs.map((log, i) => (
            <div key={i} className="space-y-3">
              <button 
                onClick={() => setExpandedLog(expandedLog === i ? null : i)}
                className="w-full text-left p-4 rounded-2xl border border-parchment-dark/50 bg-white hover:shadow-lg hover:border-sage/30 transition-all flex items-center justify-between group"
              >
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-xl border border-parchment-dark/50 text-sage group-hover:bg-sage/10 transition-colors`}>
                    {getAgentIcon(log.step)}
                  </div>
                  <div>
                    <div className="text-[9px] font-bold text-gray-300 uppercase tracking-tighter mb-0.5">{log.timestamp}</div>
                    <div className="text-xs font-bold text-deep-green capitalize">{log.step} Complete</div>
                  </div>
                </div>
                {expandedLog === i ? <ChevronUp className="w-4 h-4 text-gray-300" /> : <ChevronDown className="w-4 h-4 text-gray-300" />}
              </button>
              
              <AnimatePresence>
                {expandedLog === i && (
                  <motion.div 
                    initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }}
                    className="overflow-hidden bg-white/50 border border-parchment-dark/50 rounded-2xl mx-1"
                  >
                    <pre className="p-4 text-[10px] text-gray-500 overflow-x-auto font-mono leading-relaxed max-h-64">
                      {JSON.stringify(log.data, null, 2)}
                    </pre>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          ))}

          {logs.length === 0 && !activeThought && (
            <div className="h-full flex flex-col items-center justify-center opacity-10 text-center space-y-6 mt-20">
              <Layers className="w-20 h-20" />
              <div className="text-xs uppercase font-bold tracking-[0.3em]">Quantum Void</div>
            </div>
          )}
        </div>
        
        {error && (
          <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} className="m-6 p-4 bg-red-50 border border-red-100 rounded-2xl flex gap-4 items-start shadow-xl">
            <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
            <div className="text-xs text-red-600 font-medium leading-relaxed">{error}</div>
          </motion.div>
        )}
      </aside>
    </div>
  );
}
