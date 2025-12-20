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
    <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4">
      <div className="bg-zinc-900 rounded-lg border border-zinc-700 max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-zinc-900 border-b border-zinc-700 p-6 z-10">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-white mb-2">🔍 Verify & Edit Extracted Data</h2>
              <p className="text-zinc-400 text-sm">
                Review and correct any errors before the system submits the form
              </p>
            </div>
            <button
              onClick={onCancel}
              className="text-zinc-400 hover:text-white text-2xl"
            >
              ×
            </button>
          </div>
        </div>

        <div className="p-6 space-y-6">
          {/* Extracted Data Section */}
          <div>
            <h3 className="text-lg font-semibold text-white mb-4">
              Extracted Data ({Object.keys(editedData).length} fields)
            </h3>
            <div className="space-y-3">
              {Object.entries(editedData).map(([id, element]) => (
                <div key={id} className="bg-zinc-800 rounded-lg p-4 border border-zinc-700">
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <div className="text-xs text-zinc-500 mb-1">ID: {id}</div>
                      <div className="text-xs text-blue-400 mb-2">Type: {element.type}</div>
                      
                      <div className="space-y-2">
                        <div>
                          <label className="text-xs text-zinc-400 block mb-1">Label:</label>
                          <input
                            type="text"
                            value={element.label || ''}
                            onChange={(e) => handleDataEdit(id, 'label', e.target.value)}
                            className="w-full bg-zinc-900 border border-zinc-700 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
                          />
                        </div>
                        
                        {element.value !== null && element.value !== undefined && (
                          <div>
                            <label className="text-xs text-zinc-400 block mb-1">Value:</label>
                            <input
                              type="text"
                              value={element.value || ''}
                              onChange={(e) => handleDataEdit(id, 'value', e.target.value)}
                              className="w-full bg-zinc-900 border border-zinc-700 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
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
            <h3 className="text-lg font-semibold text-white mb-4">
              Action Plan ({editedSteps.length} steps)
            </h3>
            <div className="bg-zinc-800 rounded-lg p-4 border border-zinc-700 mb-4">
              <p className="text-sm text-zinc-300 mb-1">Task:</p>
              <p className="text-white font-medium">{actionPlan.task}</p>
            </div>
            
            <div className="space-y-3">
              {editedSteps.map((step, idx) => (
                <div key={idx} className="bg-zinc-800 rounded-lg p-4 border border-zinc-700">
                  <div className="flex items-start gap-3">
                    <span className="text-blue-400 font-mono text-sm mt-1">{step.step}.</span>
                    <div className="flex-1 space-y-2">
                      <div className="grid grid-cols-2 gap-2">
                        <div>
                          <label className="text-xs text-zinc-400 block mb-1">Action:</label>
                          <select
                            value={step.action}
                            onChange={(e) => handleStepEdit(idx, 'action', e.target.value)}
                            className="w-full bg-zinc-900 border border-zinc-700 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
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
                          <label className="text-xs text-zinc-400 block mb-1">Target:</label>
                          <input
                            type="text"
                            value={step.target}
                            onChange={(e) => handleStepEdit(idx, 'target', e.target.value)}
                            className="w-full bg-zinc-900 border border-zinc-700 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
                          />
                        </div>
                      </div>
                      
                      {step.action === 'fill' && (
                        <div>
                          <label className="text-xs text-zinc-400 block mb-1">Value:</label>
                          <input
                            type="text"
                            value={step.value || ''}
                            onChange={(e) => handleStepEdit(idx, 'value', e.target.value)}
                            className="w-full bg-zinc-900 border border-zinc-700 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
                          />
                        </div>
                      )}
                      
                      <div>
                        <label className="text-xs text-zinc-400 block mb-1">Description:</label>
                        <textarea
                          value={step.description || ''}
                          onChange={(e) => handleStepEdit(idx, 'description', e.target.value)}
                          className="w-full bg-zinc-900 border border-zinc-700 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
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
          <div className="flex gap-3 pt-4 border-t border-zinc-700">
            <button
              onClick={onCancel}
              className="flex-1 bg-zinc-700 hover:bg-zinc-600 text-white font-medium py-3 px-6 rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleConfirm}
              className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-6 rounded-lg transition-colors"
            >
              ✓ Confirm & Execute
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

