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
    <div className="medical-card p-4 mb-6">
      <h3 className="text-sm font-semibold text-slate-700 mb-4">Workflow Progress</h3>
      <div className="flex items-center justify-between">
        {steps.map((step, index) => {
          const isActive = currentStep === step.id;
          const isCompleted = step.completed;
          const isPast = currentStepIndex > index;

          return (
            <div key={step.id} className="flex items-center flex-1">
              <div className="flex flex-col items-center flex-1">
                <div
                  className={`w-10 h-10 rounded-full flex items-center justify-center text-lg transition-all shadow-md ${
                    isActive
                      ? 'bg-gradient-to-br from-blue-500 to-cyan-500 text-white ring-2 ring-blue-400 glow'
                      : isCompleted || isPast
                      ? 'bg-gradient-to-br from-emerald-500 to-teal-500 text-white'
                      : 'bg-slate-200 text-slate-500'
                  }`}
                >
                  {isCompleted && !isActive ? '✓' : step.icon}
                </div>
                <span
                  className={`text-xs mt-2 text-center font-medium ${
                    isActive ? 'text-blue-600 font-semibold' : isCompleted ? 'text-emerald-600' : 'text-slate-500'
                  }`}
                >
                  {step.label}
                </span>
              </div>
              {index < steps.length - 1 && (
                <div
                  className={`flex-1 h-1 mx-2 rounded-full ${
                    isPast || isCompleted ? 'bg-gradient-to-r from-emerald-500 to-teal-500' : 'bg-slate-200'
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

