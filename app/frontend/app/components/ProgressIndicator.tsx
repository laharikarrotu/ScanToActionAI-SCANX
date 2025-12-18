'use client';

interface ProgressIndicatorProps {
  steps: string[];
  currentStep: number;
}

export default function ProgressIndicator({ steps, currentStep }: ProgressIndicatorProps) {
  return (
    <div className="w-full">
      <div className="flex items-center justify-between mb-2">
        {steps.map((step, idx) => (
          <div key={idx} className="flex-1 flex items-center">
            <div className={`flex items-center justify-center w-8 h-8 rounded-full border-2 ${
              idx < currentStep 
                ? 'bg-green-600 border-green-600 text-white' 
                : idx === currentStep
                ? 'bg-blue-600 border-blue-600 text-white animate-pulse'
                : 'bg-zinc-800 border-zinc-600 text-zinc-400'
            }`}>
              {idx < currentStep ? '✓' : idx + 1}
            </div>
            {idx < steps.length - 1 && (
              <div className={`flex-1 h-1 mx-2 ${
                idx < currentStep ? 'bg-green-600' : 'bg-zinc-700'
              }`} />
            )}
          </div>
        ))}
      </div>
      <div className="text-center text-sm text-zinc-400">
        {steps[currentStep]}
      </div>
    </div>
  );
}

