"use client";

import React from 'react';
import { RotateCw } from 'lucide-react';
import { Button, StageHeader } from './ui';

export default function StageStalled({ onContinue, isProcessing }: { onContinue: () => void; isProcessing: boolean }) {
  return (
    <div className="space-y-8">
      <StageHeader
        title="This research was interrupted"
        description="Lume saved its progress before it stopped. Continue to pick up from where it left off."
      />
      <Button onClick={onContinue} loading={isProcessing} className="!px-6 !py-3">
        <RotateCw className="w-4 h-4" aria-hidden /> Continue research
      </Button>
    </div>
  );
}
