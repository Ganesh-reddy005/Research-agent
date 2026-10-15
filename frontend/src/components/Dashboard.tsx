"use client";

import React, { useCallback, useEffect, useRef, useState } from 'react';
import type { User } from '@supabase/supabase-js';
import { AlertCircle, Menu, Activity } from 'lucide-react';
import { AnimatePresence, motion } from 'framer-motion';
import {
  startResearch, resumeResearch, chatWithData, brainstormResearch, getBrainstorm, getResearchSession, getSessions,
  type EventCallbacks, type ResumeData,
} from '@/lib/api';
import type { ActivityLog, ChatMessage, ResearchDepth, ResearchPlan, ResearchState, SessionSummary } from '@/lib/types';

import Sidebar from './dashboard/Sidebar';
import AgentLogsPanel from './dashboard/AgentLogsPanel';
import LibraryPanel from './dashboard/LibraryPanel';
import ProgressSteps from './dashboard/ProgressSteps';
import StageIdle from './dashboard/StageIdle';
import StageClarification from './dashboard/StageClarification';
import StagePlanning from './dashboard/StagePlanning';
import StageResearching from './dashboard/StageResearching';
import StageReview from './dashboard/StageReview';
import StageCompleted from './dashboard/StageCompleted';
import StageBrainstorm from './dashboard/StageBrainstorm';
import StageStalled from './dashboard/StageStalled';
import { Button } from './dashboard/ui';
import { agentStep } from './dashboard/agents';

type Stage = 'idle' | 'brainstorm' | 'loading' | 'working' | 'clarification' | 'planning' | 'review' | 'completed' | 'stalled';
type Panel = 'activity' | 'library' | null;

// Where the graph paused (its next node) decides what the user sees.
function stageFromNext(next: string[], state: ResearchState): Stage {
  if (next.includes('planning')) return 'clarification';
  if (next.includes('retriever')) return 'planning';
  if (next.includes('synthesis')) return 'review';
  if (next.length === 0) return state.final_report || state.draft_report ? 'completed' : 'stalled';
  return 'stalled'; // stopped mid-run (e.g. connection dropped); can be continued
}

const STAGE_STEP: Partial<Record<Stage, number>> = { clarification: 0, planning: 1, review: 3, completed: 4, stalled: 2 };

export default function Dashboard({ user }: { user: User }) {
  const [stage, setStage] = useState<Stage>('idle');
  const [threadId, setThreadId] = useState<string | null>(null);
  const [research, setResearch] = useState<ResearchState>({});
  const [depth, setDepth] = useState<ResearchDepth>('light');
  const [workingStep, setWorkingStep] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [logs, setLogs] = useState<ActivityLog[]>([]);
  const [activeThought, setActiveThought] = useState<{ agent: string; text: string } | null>(null);
  const [sourceChat, setSourceChat] = useState<ChatMessage[]>([]);
  const [brainstorm, setBrainstorm] = useState<ChatMessage[]>([]);
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [panel, setPanel] = useState<Panel>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const reportRef = useRef<HTMLDivElement>(null);

  const refreshSessions = useCallback(() => {
    getSessions().then(setSessions).catch(err => console.error('Failed to fetch sessions', err));
  }, []);
  useEffect(refreshSessions, [refreshSessions]);

  const clearProject = () => {
    setThreadId(null);
    setResearch({});
    setLogs([]);
    setActiveThought(null);
    setSourceChat([]);
    setBrainstorm([]);
    setError(null);
  };

  const callbacks: EventCallbacks = {
    onStep: (step, state, tid) => {
      setThreadId(tid);
      setResearch(prev => ({ ...prev, ...state }));
      setLogs(prev => [...prev, { step, time: new Date().toLocaleTimeString(), data: state }]);
      setActiveThought(null);
    },
    onThought: (agent, token) => {
      if (agent === 'brainstorm') {
        setBrainstorm(prev => {
          const last = prev[prev.length - 1];
          if (last?.role === 'assistant') return [...prev.slice(0, -1), { ...last, content: last.content + token }];
          return [...prev, { role: 'assistant', content: token }];
        });
        return;
      }
      const step = agentStep(agent);
      if (step !== undefined) setWorkingStep(step);
      setActiveThought(prev => ({ agent, text: (prev?.agent === agent ? prev.text : '') + token }));
    },
    onInterrupt: (tid, next) => {
      setThreadId(tid);
      setIsProcessing(false);
      setActiveThought(null);
      // Interrupts always name the paused-before node, so the state isn't needed here
      setStage(stageFromNext(next, {}));
      refreshSessions();
    },
    onDone: (tid) => {
      if (tid) setThreadId(tid); // a new brainstorm learns its chat id here
      setIsProcessing(false);
      setActiveThought(null);
      setStage(prev => (prev === 'brainstorm' ? prev : 'completed'));
      refreshSessions();
    },
    onError: (err) => {
      setError(err);
      setIsProcessing(false);
      // Drop the empty "Thinking…" placeholder of a failed brainstorm reply
      setBrainstorm(prev => {
        const last = prev[prev.length - 1];
        return last?.role === 'assistant' && !last.content ? prev.slice(0, -1) : prev;
      });
    },
  };

  const run = async (step: number, action: () => Promise<void>) => {
    setError(null);
    setWorkingStep(step);
    setStage('working');
    setIsProcessing(true);
    await action();
  };

  // --- Actions -------------------------------------------------------------

  const handleStart = (topic: string, chosenDepth: ResearchDepth) => {
    clearProject();
    setDepth(chosenDepth);
    setResearch({ topic, research_mode: chosenDepth });
    run(0, () => startResearch(topic, callbacks, chosenDepth));
  };

  const handleAnswers = (answers: Record<string, string>) => {
    setResearch(prev => ({ ...prev, user_answers: answers }));
    run(1, () => resumeResearch(threadId!, 'answer', { answers }, callbacks));
  };

  const handleApprovePlan = (plan: ResearchPlan) => {
    setResearch(prev => ({ ...prev, research_plan: plan }));
    const data: ResumeData = { mode: research.research_mode ?? depth, plan };
    run(2, () => resumeResearch(threadId!, 'approve', data, callbacks));
  };

  const handleWritePaper = () => run(4, () => resumeResearch(threadId!, 'continue', {}, callbacks));

  const handleContinue = () =>
    run(STAGE_STEP.stalled!, () => resumeResearch(threadId!, 'continue', {}, callbacks));

  const handleSourceQuestion = async (query: string) => {
    if (!threadId) return;
    setSourceChat(prev => [...prev, { role: 'user', content: query }]);
    setIsProcessing(true);
    try {
      const response = await chatWithData(threadId, query);
      setSourceChat(prev => [...prev, { role: 'assistant', content: response.answer }]);
    } catch {
      setSourceChat(prev => [...prev, { role: 'assistant', content: 'Sorry, I could not search the sources just now. Please try again.' }]);
    } finally {
      setIsProcessing(false);
    }
  };

  const sendBrainstorm = (text: string, chatId: string | null) => {
    setError(null);
    setBrainstorm(prev => [...prev, { role: 'user', content: text }, { role: 'assistant', content: '' }]);
    setIsProcessing(true);
    brainstormResearch(text, chatId, callbacks).finally(() => setIsProcessing(false));
  };

  const handleStartBrainstorm = (idea: string) => {
    clearProject();
    setStage('brainstorm');
    sendBrainstorm(idea, null);
  };

  const handleBrainstormMessage = (text: string) => sendBrainstorm(text, threadId);

  const loadBrainstorm = useCallback(async (chatId: string) => {
    setIsSidebarOpen(false);
    clearProject();
    setThreadId(chatId);
    setStage('loading');
    try {
      const { messages } = await getBrainstorm(chatId);
      setBrainstorm(messages);
      setStage('brainstorm');
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setStage('brainstorm');
    }
  }, []);

  const handleSelectSession = (session: SessionSummary) =>
    session.research_mode === 'brainstorm' ? loadBrainstorm(session.thread_id) : loadSession(session.thread_id);

  const loadSession = useCallback(async (tid: string) => {
    setIsSidebarOpen(false);
    clearProject();
    setThreadId(tid);
    setStage('loading');
    try {
      const snapshot = await getResearchSession(tid);
      setResearch(snapshot.state);
      if (snapshot.state.research_mode) setDepth(snapshot.state.research_mode);
      setStage(stageFromNext(snapshot.next, snapshot.state));
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setStage('stalled');
    }
  }, []);

  const handleNewResearch = () => {
    clearProject();
    setStage('idle');
    setIsSidebarOpen(false);
  };

  const handleRetry = () => {
    if (stage === 'brainstorm') {
      if (threadId) loadBrainstorm(threadId);
      else setError(null);
    } else if (threadId) loadSession(threadId);
    else if (research.topic) handleStart(research.topic, research.research_mode ?? depth);
    else setError(null);
  };

  // --- Rendering -----------------------------------------------------------

  const report = research.final_report || research.draft_report || '';
  const showProgress = !['idle', 'brainstorm', 'loading'].includes(stage);
  const progressStep = stage === 'working' ? workingStep : STAGE_STEP[stage] ?? 0;
  const title = stage === 'brainstorm'
    ? brainstorm[0]?.content ?? 'Brainstorm'
    : research.topic || 'New research';

  return (
    <div className="flex h-screen w-full bg-mistral-beige overflow-hidden selection:bg-mistral-orange selection:text-white font-sans text-mistral-black">
      <Sidebar
        user={user}
        sessions={sessions}
        activeThreadId={threadId}
        onSelectSession={handleSelectSession}
        onNewResearch={handleNewResearch}
        onOpenLibrary={() => setPanel(panel === 'library' ? null : 'library')}
        isLibraryOpen={panel === 'library'}
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
      />

      <div className="flex-1 flex flex-col min-w-0 bg-white">
        <header className="h-14 flex items-center justify-between gap-4 px-4 sm:px-6 border-b border-mistral-black/10 shrink-0">
          <div className="flex items-center gap-3 min-w-0">
            <button
              onClick={() => setIsSidebarOpen(true)}
              className="md:hidden p-2 -ml-2 text-mistral-black/70 hover:text-mistral-black"
              aria-label="Open menu"
            >
              <Menu className="w-5 h-5" />
            </button>
            <span className="text-sm font-medium text-mistral-black truncate">{title}</span>
            {isProcessing && (
              <span className="flex items-center gap-1.5 text-xs font-medium text-mistral-orange shrink-0">
                <span className="w-1.5 h-1.5 bg-mistral-orange animate-pulse" aria-hidden /> Working
              </span>
            )}
          </div>
          <Button
            variant="ghost"
            onClick={() => setPanel(panel === 'activity' ? null : 'activity')}
            aria-pressed={panel === 'activity'}
            className={`!px-3 !py-1.5 ${panel === 'activity' ? 'text-mistral-orange' : ''}`}
          >
            <Activity className="w-4 h-4" aria-hidden /> Activity
          </Button>
        </header>

        <main className="flex-1 overflow-y-auto custom-scrollbar">
          <div className={`mx-auto w-full px-4 sm:px-8 py-8 sm:py-10 ${stage === 'completed' ? 'max-w-4xl' : 'max-w-3xl'}`}>
            {showProgress && (
              <div className="mb-10">
                <ProgressSteps current={progressStep} done={stage === 'completed'} />
              </div>
            )}

            {error && (
              <div role="alert" className="mb-8 p-4 border border-red-200 bg-red-50 flex flex-col sm:flex-row sm:items-center gap-3 sm:justify-between">
                <div className="flex gap-3 items-start">
                  <AlertCircle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" aria-hidden />
                  <div className="space-y-1">
                    <p className="text-sm font-semibold text-red-900">Something went wrong</p>
                    <p className="text-sm text-red-800">{error}</p>
                  </div>
                </div>
                <Button variant="secondary" onClick={handleRetry} className="shrink-0">Try again</Button>
              </div>
            )}

            <AnimatePresence mode="wait">
              <motion.div
                key={stage}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.2 }}
              >
                {stage === 'idle' && (
                  <StageIdle onStartResearch={handleStart} onStartBrainstorm={handleStartBrainstorm} />
                )}
                {stage === 'brainstorm' && (
                  <StageBrainstorm
                    messages={brainstorm}
                    onSend={handleBrainstormMessage}
                    onBack={handleNewResearch}
                    isProcessing={isProcessing}
                  />
                )}
                {stage === 'loading' && <p className="text-base text-mistral-black/60">Loading this research session…</p>}
                {stage === 'working' && <StageResearching step={workingStep} activeThought={activeThought} logs={logs} />}
                {stage === 'clarification' && (
                  <StageClarification
                    questions={research.clarification_questions ?? []}
                    initialAnswers={research.user_answers ?? {}}
                    onSubmit={handleAnswers}
                    isProcessing={isProcessing}
                  />
                )}
                {stage === 'planning' && research.research_plan && (
                  <StagePlanning
                    brief={research.research_brief ?? ''}
                    plan={research.research_plan}
                    onApprove={handleApprovePlan}
                    isProcessing={isProcessing}
                  />
                )}
                {stage === 'review' && (
                  <StageReview
                    summary={research.assistance_summary ?? ''}
                    sources={research.raw_sources ?? []}
                    chat={sourceChat}
                    onAsk={handleSourceQuestion}
                    onWritePaper={handleWritePaper}
                    isProcessing={isProcessing}
                  />
                )}
                {stage === 'completed' && (
                  <StageCompleted
                    topic={research.topic ?? 'Research report'}
                    report={report}
                    sources={research.raw_sources ?? []}
                    audit={research.citation_audit_log}
                    reportRef={reportRef}
                    threadId={threadId}
                  />
                )}
                {stage === 'stalled' && threadId && !error && (
                  <StageStalled onContinue={handleContinue} isProcessing={isProcessing} />
                )}
              </motion.div>
            </AnimatePresence>
          </div>
        </main>
      </div>

      <AnimatePresence>
        {panel && (
          <motion.div
            key={panel}
            initial={{ x: 360 }}
            animate={{ x: 0 }}
            exit={{ x: 360 }}
            transition={{ type: 'tween', duration: 0.2 }}
            className="fixed right-0 top-0 h-full w-full sm:w-[360px] z-40 shadow-2xl"
          >
            {panel === 'activity' ? (
              <AgentLogsPanel logs={logs} activeThought={activeThought} isProcessing={isProcessing} onClose={() => setPanel(null)} />
            ) : (
              <LibraryPanel onClose={() => setPanel(null)} />
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
