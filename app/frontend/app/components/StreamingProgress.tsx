'use client';

interface StreamingProgressProps {
  message: string;
  progress: number;
  step: string;
}

export default function StreamingProgress({ message, progress, step }: StreamingProgressProps) {
  return (
    <div className="w-full">
      <div className="bg-transparent rounded-lg p-0">
        {/* Progress Bar */}
        <div className="w-full bg-blue-100 rounded-full h-2 mb-3">
          <div
            className="bg-blue-500 h-2 rounded-full transition-all duration-300 ease-out"
            style={{ width: `${progress}%` }}
          />
        </div>
        
        {/* Progress Text */}
        <div className="flex items-center justify-between text-sm">
          <span className="text-slate-700 font-medium">{message}</span>
          <span className="text-blue-600 font-semibold">{progress}%</span>
        </div>
        
        {/* Step Indicator */}
        <div className="mt-2 text-xs text-slate-500">
          {step}
        </div>
      </div>
    </div>
  );
}

