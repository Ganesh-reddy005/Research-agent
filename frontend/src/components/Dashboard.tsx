"use client";

import React, { useState, useEffect, useRef } from 'react';
import { Download, AlertCircle, Activity } from 'lucide-react';
import { startResearch, resumeResearch, chatWithData, brainstormResearch } from '@/lib/api';
import { AnimatePresence, motion } from 'framer-motion';

// Modular Components
import Sidebar from './dashboard/Sidebar';
import AgentLogsPanel from './dashboard/AgentLogsPanel';
import LibraryPanel from './dashboard/LibraryPanel';
import StageIdle from './dashboard/StageIdle';
import StageClarification from './dashboard/StageClarification';
import StagePlanning from './dashboard/StagePlanning';
import StageResearching from './dashboard/StageResearching';
import StageReview from './dashboard/StageReview';
import StageCompleted from './dashboard/StageCompleted';
import StageBrainstorm from './dashboard/StageBrainstorm';

// --- Types ---
type Stage = 'idle' | 'clarification' | 'planning' | 'researching' | 'assistance_review' | 'reviewing' | 'completed' | 'brainstorming';
type ResearchMode = 'light' | 'deep';

export default function Dashboard() {
  const [topic, setTopic] = useState('');
  const [stage, setStage] = useState<Stage>('idle');
  const [researchMode, setResearchMode] = useState<ResearchMode>('chat');
  const [threadId, setThreadId] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isLogsOpen, setIsLogsOpen] = useState(false);
  const [isLibraryOpen, setIsLibraryOpen] = useState(false);
  
  // State from backend
  const [questions, setQuestions] = useState<any[]>([]);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [plan, setPlan] = useState<any>(null);
  const [brief, setBrief] = useState('');
  const [logs, setLogs] = useState<any[]>([]);
  const [report, setReport] = useState('');
  const [allSources, setAllSources] = useState<any[]>([]);
  const [auditLog, setAuditLog] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [expandedLog, setExpandedLog] = useState<number | null>(null);
  
  // Assistance specific state
  const [assistanceSummary, setAssistanceSummary] = useState('');
  const [chatQuery, setChatQuery] = useState('');
  const [chatHistory, setChatHistory] = useState<{role: 'user'|'assistant', text: string}[]>([]);
  
  // Brainstorm specific state
  const [brainstormHistory, setBrainstormHistory] = useState<{role: 'user'|'assistant', content: string}[]>([]);
  const [brainstormQuery, setBrainstormQuery] = useState('');

  // Streaming Thought
  const [activeThought, setActiveThought] = useState<{agent: string, text: string} | null>(null);
  
  const reportRef = useRef<HTMLDivElement>(null);

  const callbacks = {
    onStep: (step: string, state: any, tid: string) => {
      setThreadId(tid);
      if (state.clarification_questions) setQuestions(state.clarification_questions);
      if (state.research_plan) setPlan(state.research_plan);
      if (state.research_brief) setBrief(state.research_brief);
      if (state.assistance_summary) setAssistanceSummary(state.assistance_summary);
      if (state.final_report) setReport(state.final_report);
      if (state.raw_sources) setAllSources(state.raw_sources);
      if (state.citation_audit_log) setAuditLog(state.citation_audit_log);
      setActiveThought(null);
      setLogs(prev => [...prev, { step, timestamp: new Date().toLocaleTimeString(), data: state }]);
    },
    onThought: (agent: string, token: string) => {
      if (agent === 'brainstorm') {
        setBrainstormHistory(prev => {
          const last = prev[prev.length - 1];
          if (last?.role === 'assistant') {
            return [...prev.slice(0, -1), { ...last, content: last.content + token }];
          }
          return prev;
        });
        return;
      }

      if (['clarification', 'planning'].includes(agent.toLowerCase())) {
        setActiveThought(prev => ({
          agent: agent,
          text: (prev?.agent === agent && prev.text.includes('Organizing')) ? prev.text : 'Organizing research parameters...'
        }));
        return;
      }
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
      if (next.includes('synthesis')) setStage('assistance_review');
    },
    onDone: (tid: string) => {
      if (stage !== 'brainstorming') {
        setStage('completed');
      }
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

    // We check if the user is in brainstorming mode based on some state 
    // or just handle it here if topic is passed.
    // For now, let's assume if they click Run Discovery on the Research tab, it's startResearch.
    
    setStage('researching');
    setIsProcessing(true);
    setError(null);
    setLogs([]);
    setReport('');
    setAllSources([]);
    setAuditLog(null);
    await startResearch(topic, callbacks, researchMode);
  };

  const handleStartBrainstorm = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!topic.trim()) return;
    
    setStage('brainstorming');
    setIsProcessing(true);
    setError(null);
    
    const initialMessage = { role: 'user', content: topic };
    setBrainstormHistory([initialMessage, { role: 'assistant', content: '' }]);
    setTopic(''); // Clear topic for the chat
    
    await brainstormResearch([initialMessage], callbacks);
  };

  const handleBrainstormSubmit = async () => {
    if (!brainstormQuery.trim()) return;
    
    const userMsg = { role: 'user', content: brainstormQuery };
    const newHistory = [...brainstormHistory, userMsg];
    
    setBrainstormHistory([...newHistory, { role: 'assistant', content: '' }]);
    setBrainstormQuery('');
    setIsProcessing(true);
    
    await brainstormResearch(newHistory, callbacks);
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
      alert("PDF exporter loading...");
      return;
    }
    const opt = {
      margin: 0.5,
      filename: `Lume_Report_${threadId?.slice(0, 8)}.pdf`,
      image: { type: 'jpeg', quality: 0.98 },
      html2canvas: { scale: 2 },
      jsPDF: { unit: 'in', format: 'letter', orientation: 'portrait' }
    };
    html2pdf().set(opt).from(reportRef.current).save();
  };

  const handleChatSubmit = async () => {
    if (!chatQuery.trim() || !threadId) return;
    const queryText = chatQuery.trim();
    setChatHistory(prev => [...prev, { role: 'user', text: queryText }]);
    setIsProcessing(true);
    setChatQuery('');
    try {
      const response = await chatWithData(threadId, queryText);
      setChatHistory(prev => [...prev, { role: 'assistant', text: response.answer }]);
    } catch (err: any) {
      setChatHistory(prev => [...prev, { role: 'assistant', text: 'Error connecting to data vector store...' }]);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleCreateFullPaper = async () => {
    setStage('researching');
    setIsProcessing(true);
    await resumeResearch(threadId!, 'continue', {}, callbacks);
  };

  const resetResearch = () => {
    setStage('idle');
    setTopic('');
    setLogs([]);
    setReport('');
    setAllSources([]);
    setAuditLog(null);
    setError(null);
  };

  return (
    <div className="modern-subtle">
      <div className="flex h-screen w-full bg-[#F5F2ED] overflow-hidden selection:bg-mistral-orange selection:text-white font-sans">
        <Sidebar 
          onNewResearch={resetResearch} 
          onOpenLibrary={() => setIsLibraryOpen(!isLibraryOpen)}
          isLibraryOpen={isLibraryOpen}
        />

        <div className="flex-1 flex flex-col min-w-0 bg-white relative z-10 border-r border-mistral-black/5 shadow-sm">
          <header className="h-12 flex items-center justify-between px-6 bg-white border-b border-mistral-black/5 sticky top-0 z-30">
            <div className="flex items-center gap-4">
              <div className="text-[9px] font-bold text-mistral-black/30 uppercase tracking-[0.3em] font-mono">
                {stage === 'idle' ? 'Protocol Idle' : `Session // ${threadId?.slice(0, 8)}`}
              </div>
              {isProcessing && (
                <div className="flex gap-2 items-center px-2 py-0.5 border border-mistral-orange/20 bg-mistral-orange/5">
                  <span className="w-1 h-1 rounded-full bg-mistral-orange animate-pulse" />
                  <span className="text-[8px] font-bold text-mistral-orange uppercase tracking-widest">Active</span>
                </div>
              )}
            </div>
            <div className="flex items-center gap-3">
              {stage === 'completed' && (
                <button 
                  onClick={handleExport}
                  className="bg-mistral-black text-white px-3 py-1 text-[9px] font-bold uppercase tracking-widest hover:bg-mistral-orange transition-all"
                >
                  Export
                </button>
              )}
              <button 
                onClick={() => setIsLogsOpen(!isLogsOpen)}
                className={`p-1.5 transition-colors ${isLogsOpen ? 'text-mistral-orange' : 'text-mistral-black/30 hover:text-mistral-black'}`}
              >
                <Activity className="w-4 h-4" />
              </button>
            </div>
          </header>

          <main className="flex-1 overflow-y-auto custom-scrollbar">
            <div className={`mx-auto w-full transition-all duration-300 ${stage === 'idle' ? 'max-w-3xl' : 'max-w-4xl'} px-6 py-10`}>
              <AnimatePresence mode="wait">
                {stage === 'idle' && (
                  <StageIdle 
                    key="idle"
                    topic={topic}
                    setTopic={setTopic}
                    researchMode={researchMode}
                    setResearchMode={setResearchMode}
                    onSubmit={handleStart}
                    onBrainstorm={handleStartBrainstorm}
                  />
                )}
                {stage === 'brainstorming' && (
                  <StageBrainstorm 
                    key="brainstorming"
                    chatHistory={brainstormHistory}
                    chatQuery={brainstormQuery}
                    setChatQuery={setBrainstormQuery}
                    onChatSubmit={handleBrainstormSubmit}
                    isProcessing={isProcessing}
                  />
                )}
                {stage === 'clarification' && (
                  <StageClarification 
                    key="clarification"
                    questions={questions}
                    answers={answers}
                    setAnswers={setAnswers}
                    onSubmit={handleAnswerSubmit}
                    isProcessing={isProcessing}
                  />
                )}
                {stage === 'planning' && (
                  <StagePlanning 
                    key="planning"
                    brief={brief}
                    plan={plan}
                    onApprove={handlePlanApprove}
                    isProcessing={isProcessing}
                  />
                )}
                {stage === 'researching' && isProcessing && (
                  <StageResearching 
                    key="researching"
                    activeThought={activeThought}
                  />
                )}
                {stage === 'assistance_review' && (
                  <StageReview 
                    key="review"
                    summary={assistanceSummary}
                    chatHistory={chatHistory}
                    chatQuery={chatQuery}
                    setChatQuery={setChatQuery}
                    onChatSubmit={handleChatSubmit}
                    onGeneratePaper={handleCreateFullPaper}
                    isProcessing={isProcessing}
                  />
                )}
                {(stage === 'completed' || (stage === 'reviewing' && report)) && (
                  <StageCompleted 
                    key="completed"
                    report={report}
                    allSources={allSources}
                    auditLog={auditLog}
                    reportRef={reportRef}
                  />
                )}
              </AnimatePresence>
              
              {error && (
                <div className="my-8 p-4 border border-red-100 bg-red-50/50 flex gap-3 items-center">
                  <AlertCircle className="w-4 h-4 text-red-500" />
                  <div className="text-xs text-red-900 font-medium">{error}</div>
                </div>
              )}
            </div>
          </main>
        </div>

        <AnimatePresence>
          {isLogsOpen && (
            <motion.div
              initial={{ x: 300 }}
              animate={{ x: 0 }}
              exit={{ x: 300 }}
              transition={{ type: 'tween', duration: 0.2 }}
              className="fixed right-0 top-0 h-full w-[300px] z-40 shadow-2xl"
            >
              <AgentLogsPanel 
                logs={logs}
                activeThought={activeThought}
                isProcessing={isProcessing}
                expandedLog={expandedLog}
                setExpandedLog={setExpandedLog}
                onClose={() => setIsLogsOpen(false)}
              />
            </motion.div>
          )}

          {isLibraryOpen && (
            <motion.div
              initial={{ x: 300 }}
              animate={{ x: 0 }}
              exit={{ x: 300 }}
              transition={{ type: 'tween', duration: 0.2 }}
              className="fixed right-0 top-0 h-full w-[300px] z-40 shadow-2xl"
            >
              <LibraryPanel 
                onClose={() => setIsLibraryOpen(false)}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
