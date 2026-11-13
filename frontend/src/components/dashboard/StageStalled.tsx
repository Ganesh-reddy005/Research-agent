"use client";

import React from 'react';
import { RotateCw } from 'lucide-react';
import { Button, StageHeader } from './ui';
import { agentLabel } from './agents';

const COPY = {
  stopped: {
    title: 'Research paused',
    description: 'You stopped this research. Everything finished before the stop is saved, so you can continue whenever you like.',
  },
  interrupted: {
    title: 'This research was interrupted',
    description: 'Lume saved its progress before it stopped. Continue to pick up from where it left off.',
  },
};

export default function StageStalled({ reason, resumeAt, onContinue, isProcessing }: {
  reason: 'stopped' | 'interrupted';
  resumeAt: string | null;  // the graph step that runs again on Continue
  onContinue: () => void;
  isProcessing: boolean;
}) {
  return (
    <div className="space-y-8">
      <StageHeader title={COPY[reason].title} description={COPY[reason].description} />
      {resumeAt && (
        <p className="text-base text-mistral-black/85">
          Continues from: <span className="font-medium">{agentLabel(resumeAt)}</span>
        </p>
      )}
      <Button onClick={onContinue} loading={isProcessing} className="!px-6 !py-3">
        <RotateCw className="w-4 h-4" aria-hidden /> Continue research
      </Button>
    </div>
  );
}
