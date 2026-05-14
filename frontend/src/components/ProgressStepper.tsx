import React from 'react';
import { motion } from 'framer-motion';
import { Check, Loader2 } from 'lucide-react';

interface ProgressStepperProps {
  currentStep: string | null;
}

const steps = [
  { id: 'planner', label: 'Planning' },
  { id: 'retriever', label: 'Retrieving Sources' },
  { id: 'writer', label: 'Drafting Report' },
  { id: 'critic', label: 'Refining' }
];

export default function ProgressStepper({ currentStep }: ProgressStepperProps) {
  if (!currentStep) return null;

  const currentIndex = steps.findIndex(s => s.id === currentStep);

  return (
    <div className="w-full max-w-4xl mx-auto my-16 py-14 px-12 bg-white border border-mistral-border/50 shadow-md rounded-[2.5rem]">
      <div className="flex items-center justify-between relative px-6">
        <div className="absolute left-0 top-1/2 -translate-y-1/2 w-full h-0.5 bg-mistral-border/30 -z-10" />
        {steps.map((step, index) => {
          const isActive = index === currentIndex;
          const isCompleted = index < currentIndex || (currentStep === 'done' && index <= 3);

          return (
            <div key={step.id} className="flex flex-col items-center relative z-10">
              <motion.div
                initial={false}
                animate={{
                  backgroundColor: isCompleted ? '#ff511c' : isActive ? '#ff511c' : '#ffffff',
                  borderColor: isCompleted || isActive ? '#ff511c' : '#e5e7eb',
                  scale: isActive ? 1.15 : 1,
                }}
                className={`w-12 h-12 border-2 rounded-2xl flex items-center justify-center transition-all duration-500 shadow-sm`}
              >
                {isCompleted ? (
                  <Check className="w-6 h-6 text-white stroke-[3px]" />
                ) : isActive ? (
                  <Loader2 className="w-6 h-6 text-white animate-spin stroke-[3px]" />
                ) : (
                  <span className="text-mistral-black/30 font-mono font-bold text-sm">{index + 1}</span>
                )}
              </motion.div>
              <div className="mt-8 absolute top-12 whitespace-nowrap">
                <span className={`text-[10px] font-bold font-sans uppercase tracking-[0.2em] ${isActive || isCompleted ? 'text-mistral-orange' : 'text-mistral-black/30'}`}>
                  {step.label}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
