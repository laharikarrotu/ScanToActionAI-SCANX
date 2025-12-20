'use client';

interface StreamingProgressProps {
  message: string;
  progress: number;
  step: string;
}

export default function StreamingProgress({ message, progress, step }: StreamingProgressProps) {
  return (
    <div className="w-full max-w-md mx-auto mt-4">
      <div className="bg-blue-800/30 rounded-lg p-4 border border-blue-600/30">
        {/* Progress Bar */}
        <div className="w-full bg-blue-900/50 rounded-full h-2.5 mb-3">
          <div
            className="bg-gradient-to-r from-blue-400 to-blue-300 h-2.5 rounded-full transition-all duration-300 ease-out"
            style={{ width: `${progress}%` }}
          />
        </div>
        
        {/* Progress Text */}
        <div className="flex items-center justify-between text-sm">
          <span className="text-blue-200 font-medium">{message}</span>
          <span className="text-blue-400 font-semibold">{progress}%</span>
        </div>
        
        {/* Step Indicator */}
        <div className="mt-2 text-xs text-blue-300/70">
          Step: {step}
        </div>
      </div>
    </div>
  );
}

