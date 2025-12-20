'use client';

import { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { analyzeAndExecute, extractPrescription } from '../lib/api';
import type { AnalyzeResponse, ActionStep, UIElement, Medication } from '../lib/types';
import ProgressIndicator from './ProgressIndicator';
import ProgressTracker from './ProgressTracker';
import { useHealthScan } from '../context/HealthScanContext';

export default function ScanPage() {
  const router = useRouter();
  const {
    prescriptionData,
    setPrescriptionData,
    setCurrentStep,
    errors,
    setError,
    clearErrors,
    navigateToInteractions,
    navigateToDiet,
  } = useHealthScan();
  const [image, setImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [intent, setIntent] = useState('');
  const [loading, setLoading] = useState(false);
  const [progressStep, setProgressStep] = useState(0);
  const [progressMessage, setProgressMessage] = useState<string>('');
  const [progressPercent, setProgressPercent] = useState<number>(0);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [localError, setLocalError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const cameraInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setImage(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result as string);
      };
      reader.readAsDataURL(file);
      setLocalError(null);
      setResult(null);
      clearErrors();
    }
  };

  const handleCameraCapture = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setImage(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result as string);
      };
      reader.readAsDataURL(file);
      setLocalError(null);
      setResult(null);
      clearErrors();
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!image) {
      setLocalError('Please upload an image');
      setError('scan', 'Please upload an image');
      return;
    }

    // Validate image size (max 10MB)
    if (image.size > 10 * 1024 * 1024) {
      setLocalError('Image is too large. Please use an image smaller than 10MB.');
      setError('scan', 'Image is too large. Please use an image smaller than 10MB.');
      return;
    }

    setLoading(true);
    setLocalError(null);
    clearErrors();
    setResult(null);
    setProgressStep(0);

    try {
      // FAST MODE: Auto-detect prescription requests for instant extraction
      const intentLower = intent.toLowerCase().trim();
      const isPrescriptionRequest = !intent.trim() || 
        intentLower.includes('prescription') || 
        intentLower.includes('medication') ||
        intentLower.includes('extract') ||
        intentLower.includes('read prescription') ||
        intentLower.includes('what medications') ||
        intentLower.includes('show me medications');
      
      if (isPrescriptionRequest) {
        // ⚡ FAST MODE: Direct extraction like ChatGPT with streaming
        setProgressStep(1); // Extracting
        setProgressMessage('Starting extraction...');
        setProgressPercent(0);
        
        const prescriptionResponse = await extractPrescription(
          image,
          (progress) => {
            // Real-time progress updates
            setProgressMessage(progress.message);
            setProgressPercent(progress.progress);
            
            // Update step based on progress
            if (progress.step === 'validating') {
              setProgressStep(1);
            } else if (progress.step === 'ocr') {
              setProgressStep(2);
            } else if (progress.step === 'analyzing') {
              setProgressStep(3);
            } else if (progress.step === 'complete') {
              setProgressStep(4);
            }
          }
        );
        setProgressStep(4); // Complete
        
        // Store in context - check response structure
        const prescriptionInfo = (prescriptionResponse as any).prescription_info || prescriptionResponse;
        const extractedData = {
          medications: prescriptionInfo?.medication_name ? [{
            medication_name: prescriptionInfo.medication_name,
            dosage: prescriptionInfo.dosage,
            frequency: prescriptionInfo.frequency,
            quantity: prescriptionInfo.quantity,
            refills: prescriptionInfo.refills,
            instructions: prescriptionInfo.instructions,
          }] : [],
          prescriber: prescriptionInfo?.prescriber,
          date: prescriptionInfo?.date,
          imagePreview: imagePreview || undefined,
        };
        
        setPrescriptionData(extractedData);
        setCurrentStep('scan');
        clearErrors();
        
        setResult({
          status: 'success',
          structured_data: {
            medications: extractedData.medications,
            prescriber: extractedData.prescriber,
            date: extractedData.date
          },
          message: 'Prescription extracted successfully'
        });
      } else {
        // FULL MODE: For forms and complex documents
        if (!intent.trim()) {
          const errorMsg = 'Please enter your intent (e.g., "Fill this form", "Extract data", or leave empty for prescription)';
          setLocalError(errorMsg);
          setError('scan', errorMsg);
          setLoading(false);
          return;
        }
        setProgressStep(1); // Analyzing image
        const response = await analyzeAndExecute(image, intent);
        setProgressStep(2); // Planning
        setProgressStep(3); // Executing
        setResult(response);
        setProgressStep(4); // Complete
      }
    } catch (err: unknown) {
      setProgressStep(0);
      // Better error messages
      const errorMsg = err instanceof Error ? err.message : 'Something went wrong. Please try again.';
      setLocalError(errorMsg);
      
      if (errorMsg.includes('Failed to fetch') || errorMsg.includes('NetworkError')) {
        setError('scan', 'Cannot connect to server. Make sure the backend is running on http://localhost:8000');
      } else if (errorMsg.includes('401') || errorMsg.includes('403')) {
        setError('scan', 'Authentication failed. Please check your API keys.');
      } else if (errorMsg.includes('429')) {
        setError('scan', 'Rate limit exceeded. Please try again in a moment.');
      } else {
        setError('scan', errorMsg);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setImage(null);
    setImagePreview(null);
    setIntent('');
    setResult(null);
    setLocalError(null);
    setProgressMessage('');
    setProgressPercent(0);
    setProgressStep(0);
    clearErrors();
    if (fileInputRef.current) fileInputRef.current.value = '';
    if (cameraInputRef.current) cameraInputRef.current.value = '';
  };

  // Set current step on mount
  useEffect(() => {
    setCurrentStep('scan');
  }, [setCurrentStep]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 to-blue-950 text-white p-4 pb-8">
      <div className="max-w-4xl mx-auto">
        <div className="mb-6 md:mb-8 text-center">
          <h1 className="text-3xl md:text-4xl font-bold mb-2">HealthScan</h1>
          <p className="text-sm md:text-base text-blue-300 px-2">Your AI healthcare assistant - scan forms, prescriptions, and documents</p>
        </div>
        
        {/* Progress Tracker */}
        <ProgressTracker />

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Image Upload Section */}
          <div className="bg-zinc-800 rounded-lg p-4 md:p-6 border border-zinc-700">
            <h2 className="text-lg md:text-xl font-semibold mb-4">1. Upload or Capture Image</h2>
            
            {imagePreview ? (
              <div className="space-y-4">
                <img
                  src={imagePreview}
                  alt="Preview"
                  className="max-w-full h-auto rounded-lg border border-zinc-700"
                />
                <button
                  type="button"
                  onClick={handleReset}
                  className="text-sm text-zinc-400 hover:text-white"
                >
                  Change image
                </button>
              </div>
            ) : (
              <div className="flex flex-col sm:flex-row gap-4">
                <label className="flex-1 cursor-pointer">
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    onChange={handleFileSelect}
                    className="hidden"
                  />
                  <div className="border-2 border-dashed border-zinc-600 rounded-lg p-8 text-center hover:border-green-500 transition-colors">
                    <p className="text-zinc-400">Click to upload</p>
                    <p className="text-sm text-zinc-500 mt-2">or drag and drop</p>
                  </div>
                </label>
                
                <label className="flex-1 cursor-pointer">
                  <input
                    ref={cameraInputRef}
                    type="file"
                    accept="image/*"
                    capture="environment"
                    onChange={handleCameraCapture}
                    className="hidden"
                  />
                  <div className="border-2 border-dashed border-zinc-600 rounded-lg p-8 text-center hover:border-green-500 transition-colors">
                    <p className="text-zinc-400">📷 Use Camera</p>
                    <p className="text-sm text-zinc-500 mt-2">Mobile only</p>
                  </div>
                </label>
              </div>
            )}
          </div>

          {/* Intent Input */}
          <div className="bg-zinc-800 rounded-lg p-4 md:p-6 border border-zinc-700">
            <h2 className="text-lg md:text-xl font-semibold mb-4">2. What do you need help with?</h2>
            <textarea
              value={intent}
              onChange={(e) => setIntent(e.target.value)}
              placeholder="Leave empty for FAST prescription extraction ⚡ OR enter: Fill form, Book appointment, Extract data..."
              className="w-full bg-zinc-900 border border-zinc-700 rounded-lg p-4 text-white placeholder-zinc-500 focus:outline-none focus:border-blue-500"
              rows={3}
            />
            <p className="text-sm text-zinc-500 mt-2">
              💡 <strong>Tip:</strong> Leave empty for instant prescription extraction (like ChatGPT) | Or enter intent for form filling
            </p>
          </div>

          {/* Progress Indicator */}
          {loading && (
            <div className="bg-zinc-800 rounded-lg p-6 border border-zinc-700">
              <ProgressIndicator 
                steps={['Analyzing Image', 'Planning Actions', 'Executing', 'Complete']}
                currentStep={progressStep}
              />
            </div>
          )}

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading || !image || !intent.trim()}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-zinc-700 disabled:cursor-not-allowed text-white font-semibold py-4 px-6 rounded-lg transition-colors flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Processing...
              </>
            ) : (
              'Scan & Help'
            )}
          </button>

          {(localError || errors.scan) && (
            <div className="bg-red-900/50 border border-red-700 rounded-lg p-4 text-red-200">
              <p>{localError || errors.scan}</p>
              {(localError || errors.scan)?.includes('Network') && (
                <button
                  onClick={handleSubmit}
                  className="mt-2 px-4 py-2 bg-red-700 hover:bg-red-800 rounded text-sm"
                >
                  🔄 Retry
                </button>
              )}
            </div>
          )}
        </form>

        {/* Results */}
        {result && (
          <div className="mt-8 bg-zinc-800 rounded-lg p-6 border border-zinc-700 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold">Results</h2>
              <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                result.status === 'success' ? 'bg-green-900/30 text-green-400' :
                result.status === 'partial' ? 'bg-yellow-900/30 text-yellow-400' :
                result.status === 'error' ? 'bg-red-900/30 text-red-400' :
                'bg-blue-900/30 text-blue-400'
              }`}>
                {result.status === 'success' && '✓ Success'}
                {result.status === 'partial' && '⚠ Partial'}
                {result.status === 'error' && '✗ Error'}
                {result.status === 'plan_only' && '📋 Plan Only'}
                {result.status === 'no_elements' && '🔍 No Elements'}
              </div>
            </div>
            
            <div className="space-y-4">
              {result.message && (
                <div className="bg-zinc-900/50 rounded-lg p-4 border border-zinc-700">
                  <p className="text-blue-300">{result.message}</p>
                </div>
              )}
              
              {result.plan && result.plan.steps && (
                <div className="bg-zinc-900/50 rounded-lg p-4 border border-zinc-700">
                  <h3 className="text-sm font-semibold text-zinc-300 mb-3">Action Plan</h3>
                  <div className="space-y-2">
                    {result.plan.steps.map((step: ActionStep, idx: number) => (
                      <div key={idx} className="flex items-start gap-3 p-2 bg-zinc-800 rounded">
                        <span className="text-blue-400 font-mono text-xs mt-1">{step.step}.</span>
                        <div className="flex-1">
                          <p className="text-sm text-white">
                            <span className="font-semibold capitalize">{step.action}</span>
                            {step.target && <span className="text-zinc-400"> on {step.target}</span>}
                            {step.value && <span className="text-zinc-500">: {step.value}</span>}
                          </p>
                          {step.description && (
                            <p className="text-xs text-zinc-500 mt-1">{step.description}</p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {result.execution && (
                <div className="bg-zinc-900/50 rounded-lg p-4 border border-zinc-700">
                  <h3 className="text-sm font-semibold text-zinc-300 mb-3">Execution Log</h3>
                  <div className="space-y-1 max-h-60 overflow-y-auto">
                    {result.execution.logs && result.execution.logs.map((log: string, idx: number) => (
                      <div key={idx} className="text-xs font-mono text-zinc-400 py-1">
                        {log.startsWith('✓') && <span className="text-green-400">{log}</span>}
                        {log.startsWith('✗') && <span className="text-red-400">{log}</span>}
                        {log.startsWith('⚠') && <span className="text-yellow-400">{log}</span>}
                        {!log.startsWith('✓') && !log.startsWith('✗') && !log.startsWith('⚠') && log}
                      </div>
                    ))}
                  </div>
                  {result.execution.final_url && (
                    <div className="mt-3 pt-3 border-t border-zinc-700">
                      <p className="text-xs text-zinc-400">Final URL:</p>
                      <a href={result.execution.final_url} target="_blank" rel="noopener noreferrer" className="text-xs text-blue-400 hover:underline break-all">
                        {result.execution.final_url}
                      </a>
                    </div>
                  )}
                </div>
              )}

              {result.structured_data && result.structured_data.medications && (
                <div className="bg-zinc-900/50 rounded-lg p-4 border border-zinc-700">
                  <h3 className="text-sm font-semibold text-zinc-300 mb-3">📋 Extracted Prescription Data</h3>
                  <div className="space-y-3">
                    {Array.isArray(result.structured_data.medications) ? (
                      result.structured_data.medications.map((med: Medication, idx: number) => (
                        <div key={idx} className="bg-zinc-800 rounded-lg p-3 border border-zinc-700">
                          <div className="font-semibold text-white mb-2">{med.medication_name || 'Unknown Medication'}</div>
                          <div className="grid grid-cols-2 gap-2 text-xs">
                            {med.dosage && <div><span className="text-zinc-400">Dosage:</span> <span className="text-white">{med.dosage}</span></div>}
                            {med.frequency && <div><span className="text-zinc-400">Frequency:</span> <span className="text-white">{med.frequency}</span></div>}
                            {med.quantity && <div><span className="text-zinc-400">Quantity:</span> <span className="text-white">{med.quantity}</span></div>}
                            {med.refills && <div><span className="text-zinc-400">Refills:</span> <span className="text-white">{med.refills}</span></div>}
                          </div>
                          {med.instructions && (
                            <div className="mt-2 text-xs">
                              <span className="text-zinc-400">Instructions:</span>
                              <span className="text-white ml-2">{med.instructions}</span>
                            </div>
                          )}
                        </div>
                      ))
                    ) : (
                      <div className="bg-zinc-800 rounded-lg p-3 border border-zinc-700">
                        <div className="font-semibold text-white mb-2">{(result.structured_data.medications as Medication).medication_name || 'Medication'}</div>
                        <div className="grid grid-cols-2 gap-2 text-xs">
                          {(result.structured_data.medications as Medication).dosage && <div><span className="text-zinc-400">Dosage:</span> <span className="text-white">{(result.structured_data.medications as Medication).dosage}</span></div>}
                          {(result.structured_data.medications as Medication).frequency && <div><span className="text-zinc-400">Frequency:</span> <span className="text-white">{(result.structured_data.medications as Medication).frequency}</span></div>}
                        </div>
                      </div>
                    )}
                    {result.structured_data.prescriber && (
                      <div className="text-xs text-zinc-400">
                        Prescriber: <span className="text-white">{result.structured_data.prescriber}</span>
                      </div>
                    )}
                    {result.structured_data.date && (
                      <div className="text-xs text-zinc-400">
                        Date: <span className="text-white">{result.structured_data.date}</span>
                      </div>
                    )}
                  </div>
                  
                  {/* Quick Actions - Integration Buttons */}
                  <div className="mt-4 pt-4 border-t border-zinc-700 flex gap-2 flex-wrap">
                    <button
                      onClick={() => {
                        if (!result.structured_data?.medications) return;
                        // Store medications in localStorage
                        const medications: Medication[] = Array.isArray(result.structured_data.medications) 
                          ? result.structured_data.medications 
                          : [result.structured_data.medications as Medication];
                        localStorage.setItem('extracted_medications', JSON.stringify(medications));
                        localStorage.setItem('prescription_image', imagePreview || '');
                        router.push('/interactions');
                      }}
                      className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-colors"
                    >
                      💊 Check Drug Interactions
                    </button>
                    {result.structured_data.medications && (
                      <button
                        onClick={() => {
                          if (!result.structured_data?.medications) return;
                          // Store medications for diet portal
                          const medications: Medication[] = Array.isArray(result.structured_data.medications) 
                            ? result.structured_data.medications 
                            : [result.structured_data.medications as Medication];
                          const medNames = medications.map((m: Medication) => m.medication_name).join(', ');
                          localStorage.setItem('current_medications', medNames);
                          router.push('/diet');
                        }}
                        className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white text-sm rounded-lg transition-colors"
                      >
                        🥗 Get Diet Recommendations
                      </button>
                    )}
                  </div>
                </div>
              )}

              {result.extracted_data && Object.keys(result.extracted_data).length > 0 && (
                <details className="bg-zinc-900/50 rounded-lg border border-zinc-700">
                  <summary className="p-4 cursor-pointer text-sm font-semibold text-zinc-300">
                    Raw Extracted Data ({Object.keys(result.extracted_data).length})
                  </summary>
                  <div className="p-4 pt-0 space-y-2 max-h-60 overflow-y-auto">
                    {Object.entries(result.extracted_data).slice(0, 10).map(([key, value]: [string, any]) => (
                      <div key={key} className="text-xs p-2 bg-zinc-800 rounded">
                        <span className="text-blue-400 font-mono">{value.type}</span>
                        {value.label && <span className="text-zinc-300 ml-2">{value.label}</span>}
                        {value.value && <span className="text-zinc-500 ml-2">→ {value.value}</span>}
                      </div>
                    ))}
                  </div>
                </details>
              )}

              {result.ui_schema && result.ui_schema.elements && (
                <details className="bg-zinc-900/50 rounded-lg border border-zinc-700">
                  <summary className="p-4 cursor-pointer text-sm font-semibold text-zinc-300">
                    Detected UI Elements ({result.ui_schema.elements.length})
                  </summary>
                  <div className="p-4 pt-0 space-y-2 max-h-60 overflow-y-auto">
                    {result.ui_schema.elements.slice(0, 10).map((elem: UIElement, idx: number) => (
                      <div key={idx} className="text-xs p-2 bg-zinc-800 rounded">
                        <span className="text-blue-400 font-mono">{elem.type}</span>
                        {elem.label && <span className="text-zinc-300 ml-2">{elem.label}</span>}
                      </div>
                    ))}
                    {result.ui_schema.elements.length > 10 && (
                      <p className="text-xs text-zinc-500">... and {result.ui_schema.elements.length - 10} more</p>
                    )}
                  </div>
                </details>
              )}

              <div className="flex gap-3 pt-2">
                <button
                  onClick={handleReset}
                  className="flex-1 bg-zinc-700 hover:bg-zinc-600 text-white font-medium py-2 px-4 rounded-lg transition-colors"
                >
                  Start Over
                </button>
                {result.execution?.screenshot_path && (
                  <button
                    onClick={() => {
                      // Screenshot is stored on backend, show path info
                      if (result.execution?.screenshot_path) {
                        alert(`Screenshot saved at: ${result.execution.screenshot_path}\n(Backend endpoint not implemented yet)`);
                      }
                    }}
                    className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors"
                  >
                    View Screenshot Info
                  </button>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

