'use client';

import { useState } from 'react';
import type { UIElement, ActionStep } from '../lib/types';

interface DataVerificationProps {
  extractedData: Record<string, UIElement>;
  actionPlan: {
    task: string;
    steps: ActionStep[];
  };
  onConfirm: (verifiedData: Record<string, UIElement>, verifiedPlan: ActionPlan) => void;
  onCancel: () => void;
}

interface ActionPlan {
  task: string;
  steps: ActionStep[];
}

export default function DataVerification({
  extractedData,
  actionPlan,
  onConfirm,
  onCancel,
}: DataVerificationProps) {
  const [editedData, setEditedData] = useState<Record<string, UIElement>>(extractedData);
  const [editedSteps, setEditedSteps] = useState<ActionStep[]>(actionPlan.steps);

  const handleDataEdit = (elementId: string, field: 'label' | 'value', newValue: string) => {
    setEditedData(prev => ({
      ...prev,
      [elementId]: {
        ...prev[elementId],
        [field]: newValue,
      },
    }));
  };

  const handleStepEdit = (stepIndex: number, field: 'action' | 'target' | 'value' | 'description', newValue: string) => {
    setEditedSteps(prev => prev.map((step, idx) => 
      idx === stepIndex ? { ...step, [field]: newValue } : step
    ));
  };

  const handleConfirm = () => {
    onConfirm(editedData, {
      task: actionPlan.task,
      steps: editedSteps,
    });
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="medical-card glass-strong rounded-xl w-full max-w-[95vw] mx-auto max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 glass-strong border-b border-blue-200/50 p-6 z-10">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-slate-800 mb-2">🔍 Verify & Edit Extracted Data</h2>
              <p className="text-slate-600 text-sm">
                Review and correct any errors before the system submits the form
              </p>
            </div>
            <button
              onClick={onCancel}
              className="text-slate-500 hover:text-slate-800 text-2xl transition-colors"
            >
              ×
            </button>
          </div>
        </div>

        <div className="p-6 space-y-6">
          {/* Extracted Data Section */}
          <div>
            <h3 className="text-lg font-semibold text-slate-800 mb-4">
              Extracted Data ({Object.keys(editedData).length} fields)
            </h3>
            <div className="space-y-3">
              {Object.entries(editedData).map(([id, element]) => (
                <div key={id} className="medical-card bg-blue-50 border-blue-200 rounded-xl p-4">
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <div className="text-xs text-slate-500 mb-1">ID: {id}</div>
                      <div className="text-xs text-blue-600 mb-2 font-medium">Type: {element.type}</div>
                      
                      <div className="space-y-2">
                        <div>
                          <label className="text-xs text-slate-600 block mb-1 font-medium">Label:</label>
                          <input
                            type="text"
                            value={element.label || ''}
                            onChange={(e) => handleDataEdit(id, 'label', e.target.value)}
                            className="w-full medical-card border border-blue-200 rounded-lg px-3 py-2 text-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400 transition-all"
                          />
                        </div>
                        
                        {element.value !== null && element.value !== undefined && (
                          <div>
                            <label className="text-xs text-slate-600 block mb-1 font-medium">Value:</label>
                            <input
                              type="text"
                              value={element.value || ''}
                              onChange={(e) => handleDataEdit(id, 'value', e.target.value)}
                              className="w-full medical-card border border-blue-200 rounded-lg px-3 py-2 text-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400 transition-all"
                            />
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Action Plan Section */}
          <div>
            <h3 className="text-lg font-semibold text-slate-800 mb-4">
              Action Plan ({editedSteps.length} steps)
            </h3>
            <div className="medical-card bg-blue-50 border-blue-200 rounded-xl p-4 mb-4">
              <p className="text-sm text-slate-600 mb-1 font-medium">Task:</p>
              <p className="text-slate-800 font-semibold">{actionPlan.task}</p>
            </div>
            
            <div className="space-y-3">
              {editedSteps.map((step, idx) => (
                <div key={idx} className="medical-card bg-blue-50 border-blue-200 rounded-xl p-4">
                  <div className="flex items-start gap-3">
                    <span className="text-blue-600 font-mono text-sm mt-1 font-semibold">{step.step}.</span>
                    <div className="flex-1 space-y-2">
                      <div className="grid grid-cols-2 gap-2">
                        <div>
                          <label className="text-xs text-slate-600 block mb-1 font-medium">Action:</label>
                          <select
                            value={step.action}
                            onChange={(e) => handleStepEdit(idx, 'action', e.target.value)}
                            className="w-full medical-card border border-blue-200 rounded-lg px-3 py-2 text-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400 transition-all"
                          >
                            <option value="click">Click</option>
                            <option value="fill">Fill</option>
                            <option value="read">Read</option>
                            <option value="select">Select</option>
                            <option value="navigate">Navigate</option>
                            <option value="wait">Wait</option>
                          </select>
                        </div>
                        
                        <div>
                          <label className="text-xs text-slate-600 block mb-1 font-medium">Target:</label>
                          <input
                            type="text"
                            value={step.target}
                            onChange={(e) => handleStepEdit(idx, 'target', e.target.value)}
                            className="w-full medical-card border border-blue-200 rounded-lg px-3 py-2 text-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400 transition-all"
                          />
                        </div>
                      </div>
                      
                      {step.action === 'fill' && (
                        <div>
                          <label className="text-xs text-slate-600 block mb-1 font-medium">Value:</label>
                          <input
                            type="text"
                            value={step.value || ''}
                            onChange={(e) => handleStepEdit(idx, 'value', e.target.value)}
                            className="w-full medical-card border border-blue-200 rounded-lg px-3 py-2 text-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400 transition-all"
                          />
                        </div>
                      )}
                      
                      <div>
                        <label className="text-xs text-slate-600 block mb-1 font-medium">Description:</label>
                        <textarea
                          value={step.description || ''}
                          onChange={(e) => handleStepEdit(idx, 'description', e.target.value)}
                          className="w-full medical-card border border-blue-200 rounded-lg px-3 py-2 text-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400 transition-all"
                          rows={2}
                        />
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3 pt-4 border-t border-blue-200">
            <button
              onClick={onCancel}
              className="flex-1 medical-card bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium py-3 px-6 rounded-xl transition-colors border border-slate-300"
            >
              Cancel
            </button>
            <button
              onClick={handleConfirm}
              className="flex-1 btn-primary text-white font-medium py-3 px-6 rounded-xl transition-all"
            >
              ✓ Confirm & Execute
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

