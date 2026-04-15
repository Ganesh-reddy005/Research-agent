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
    <div className="w-full max-w-3xl mx-auto my-12 py-8 px-6 glass rounded-2xl">
      <div className="flex items-center justify-between relative">
        <div className="absolute left-0 top-1/2 -translate-y-1/2 w-full h-1 bg-gray-700 -z-10" />
        {steps.map((step, index) => {
          const isActive = index === currentIndex;
          const isCompleted = index < currentIndex || (currentStep === 'done' && index <= 3);

          return (
            <div key={step.id} className="flex flex-col items-center relative z-10">
              <motion.div
                initial={false}
                animate={{
                  backgroundColor: isCompleted ? '#06b6d4' : isActive ? '#0891b2' : '#374151',
                  borderColor: isActive || isCompleted ? '#22d3ee' : '#4b5563',
                  scale: isActive ? 1.2 : 1
                }}
                className={`w-10 h-10 rounded-full flex items-center justify-center border-2 transition-colors duration-500`}
              >
                {isCompleted ? (
                  <Check className="w-5 h-5 text-white" />
                ) : isActive ? (
                  <Loader2 className="w-5 h-5 text-white animate-spin" />
                ) : (
                  <span className="text-gray-400 font-medium">{index + 1}</span>
                )}
              </motion.div>
              <div className="mt-4 absolute top-12 whitespace-nowrap">
                <span className={`text-sm font-medium ${isActive || isCompleted ? 'text-cyan-400' : 'text-gray-500'}`}>
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
