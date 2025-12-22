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
            <div className={`flex items-center justify-center w-8 h-8 rounded-full border-2 transition-all ${
              idx < currentStep 
                ? 'bg-gradient-to-br from-emerald-500 to-teal-500 border-emerald-600 text-white shadow-md' 
                : idx === currentStep
                ? 'bg-gradient-to-br from-blue-500 to-cyan-500 border-blue-600 text-white animate-pulse shadow-lg glow'
                : 'bg-slate-200 border-slate-300 text-slate-500'
            }`}>
              {idx < currentStep ? '✓' : idx + 1}
            </div>
            {idx < steps.length - 1 && (
              <div className={`flex-1 h-1 mx-2 rounded-full ${
                idx < currentStep ? 'bg-gradient-to-r from-emerald-500 to-teal-500' : 'bg-slate-200'
              }`} />
            )}
          </div>
        ))}
      </div>
      <div className="text-center text-sm text-slate-600 font-medium">
        {steps[currentStep]}
      </div>
    </div>
  );
}

