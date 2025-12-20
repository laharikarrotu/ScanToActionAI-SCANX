'use client';

import { useHealthScan } from '../context/HealthScanContext';

export default function ProgressTracker() {
  const { currentStep, prescriptionData, interactionResult, dietData } = useHealthScan();

  const steps = [
    { id: 'scan', label: 'Scan Prescription', icon: '📄', completed: !!prescriptionData },
    { id: 'interactions', label: 'Check Interactions', icon: '💊', completed: !!interactionResult },
    { id: 'diet', label: 'Get Diet Advice', icon: '🥗', completed: !!dietData?.condition },
  ];

  const currentStepIndex = steps.findIndex(s => s.id === currentStep);

  return (
    <div className="bg-zinc-800 rounded-lg p-4 border border-zinc-700 mb-6">
      <h3 className="text-sm font-semibold text-zinc-300 mb-4">Workflow Progress</h3>
      <div className="flex items-center justify-between">
        {steps.map((step, index) => {
          const isActive = currentStep === step.id;
          const isCompleted = step.completed;
          const isPast = currentStepIndex > index;

          return (
            <div key={step.id} className="flex items-center flex-1">
              <div className="flex flex-col items-center flex-1">
                <div
                  className={`w-10 h-10 rounded-full flex items-center justify-center text-lg transition-all ${
                    isActive
                      ? 'bg-blue-600 text-white ring-2 ring-blue-400'
                      : isCompleted || isPast
                      ? 'bg-green-600 text-white'
                      : 'bg-zinc-700 text-zinc-400'
                  }`}
                >
                  {isCompleted && !isActive ? '✓' : step.icon}
                </div>
                <span
                  className={`text-xs mt-2 text-center ${
                    isActive ? 'text-blue-400 font-semibold' : isCompleted ? 'text-green-400' : 'text-zinc-500'
                  }`}
                >
                  {step.label}
                </span>
              </div>
              {index < steps.length - 1 && (
                <div
                  className={`flex-1 h-1 mx-2 ${
                    isPast || isCompleted ? 'bg-green-600' : 'bg-zinc-700'
                  }`}
                />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

