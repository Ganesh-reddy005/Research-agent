"use client";

import React, { useState } from 'react';
import QueryForm from '@/components/QueryForm';
import ProgressStepper from '@/components/ProgressStepper';
import ReportViewer from '@/components/ReportViewer';
import AgentLogsViewer from '@/components/AgentLogsViewer';
import { submitResearchQuery } from '@/lib/api';

export default function Home() {
  const [isSearching, setIsSearching] = useState(false);
  const [currentStep, setCurrentStep] = useState<string | null>(null);
  const [finalReport, setFinalReport] = useState<string | null>(null);
  const [sources, setSources] = useState<any[]>([]);
  const [searchQueries, setSearchQueries] = useState<string[]>([]);
  const [draftReport, setDraftReport] = useState<string | null>(null);
  const [refinedReport, setRefinedReport] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // The old handleSearch was removed to prevent duplication.

  // When step is 'critic' or 'done', we might have the final report in our data stream
  // We need to parse backend response to update report text live if we had it, 
  // but since our stream emits full state delta, we can just fetch it or let the SSE send the final_report
  // Actually, we should capture the 'final_report' from the 'critic' step state.
  
  const handleEvent = (event: string, data: any) => {
    console.log("DEBUG FRONTEND SSE EVENT:", data);
    if (data.step) {
      setCurrentStep(data.step);
      const stepState = data.state;
      if (stepState) {
        if (stepState.search_queries) setSearchQueries(stepState.search_queries);
        if (stepState.sources) setSources(stepState.sources);
        if (stepState.draft_report) {
          setDraftReport(stepState.draft_report);
          // Also update finalReport as a preview if we don't have the final one yet
          if (!stepState.final_report) setFinalReport(stepState.draft_report);
        }
        if (stepState.final_report) {
          setRefinedReport(stepState.final_report);
          setFinalReport(stepState.final_report);
        }
      }
    }
  };

  const startSearchWrapper = async (query: string) => {
    setIsSearching(true);
    setCurrentStep('planner');
    setFinalReport(null);
    setSources([]);
    setSearchQueries([]);
    setDraftReport(null);
    setRefinedReport(null);
    setError(null);

    await submitResearchQuery(query, handleEvent, () => {
      setCurrentStep('done');
      setIsSearching(false);
    }, (err) => {
      setError(err);
      setIsSearching(false);
      setCurrentStep(null);
    });
  }

  return (
    <main className="min-h-screen py-16 px-4 sm:px-6 lg:px-8 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-slate-900 via-gray-900 to-black">
      <div className="max-w-5xl mx-auto space-y-12">
        <div className="text-center space-y-6">
          <h1 className="text-5xl md:text-6xl font-extrabold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500 pb-2">
            AI Research Assistant
          </h1>
          <p className="text-lg md:text-xl text-gray-400 max-w-2xl mx-auto font-light">
            Generate comprehensive, IEEE-style research reports in minutes using multi-agent AI and real-time data.
          </p>
        </div>

        <QueryForm onSubmit={startSearchWrapper} isLoading={isSearching} />

        {error && (
          <div className="p-4 bg-red-900/50 border border-red-500/50 rounded-lg text-red-200 text-center">
            {error}
          </div>
        )}

        {(isSearching || currentStep === 'done') && (
          <div className="mt-16 space-y-8">
            <ProgressStepper currentStep={currentStep} />
            
            <AgentLogsViewer 
              logs={{
                searchQueries,
                sources,
                draftReport,
                refinedReport
              }} 
            />
          </div>
        )}

        {finalReport && (
          <ReportViewer report={finalReport} sources={sources} />
        )}
      </div>
    </main>
  );
}
