"use client";

import React from 'react';
import { RotateCw } from 'lucide-react';
import { Button, StageHeader } from './ui';

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

export default function StageStalled({ reason, onContinue, isProcessing }: {
  reason: 'stopped' | 'interrupted';
  onContinue: () => void;
  isProcessing: boolean;
}) {
  return (
    <div className="space-y-8">
      <StageHeader title={COPY[reason].title} description={COPY[reason].description} />
      <Button onClick={onContinue} loading={isProcessing} className="!px-6 !py-3">
        <RotateCw className="w-4 h-4" aria-hidden /> Continue research
      </Button>
    </div>
  );
}
