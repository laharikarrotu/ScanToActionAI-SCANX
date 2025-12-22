'use client';

import { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { analyzeAndExecute, extractPrescription, executeVerifiedPlan } from '../lib/api';
import type { AnalyzeResponse, ActionStep, UIElement, Medication, ExtractPrescriptionResponse, PrescriptionInfo } from '../lib/types';
import ProgressIndicator from './ProgressIndicator';
import ProgressTracker from './ProgressTracker';
import DataVerification from './DataVerification';
import { useHealthScan } from '../context/HealthScanContext';
import { safeStorage } from '../lib/storage';

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
  const [showVerification, setShowVerification] = useState(false);
  const [verificationData, setVerificationData] = useState<{ data: Record<string, UIElement>, plan: { task: string; steps: ActionStep[] }, uiSchema: Record<string, unknown> } | null>(null);
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
        let prescriptionInfo: PrescriptionInfo | undefined;
        if ('prescription_info' in prescriptionResponse) {
          prescriptionInfo = (prescriptionResponse as ExtractPrescriptionResponse).prescription_info;
        } else if ('medication_name' in prescriptionResponse) {
          prescriptionInfo = prescriptionResponse as PrescriptionInfo;
        }
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
        
        // HITL: Request verification step for medical forms
        const needsVerification = intent.toLowerCase().includes('form') || 
                                  intent.toLowerCase().includes('fill') ||
                                  intent.toLowerCase().includes('submit');
        
        const response = await analyzeAndExecute(image, intent, undefined, needsVerification);
        
        // Check if verification is required (HITL)
        if (response.status === 'verification_required') {
          setVerificationData({
            data: (response.extracted_data || {}) as Record<string, UIElement>,
            plan: (response.plan || { task: '', steps: [] }) as { task: string; steps: ActionStep[] },
            uiSchema: (response.ui_schema || {}) as Record<string, unknown>
          });
          setShowVerification(true);
          setLoading(false);
          return;
        }
        
        setProgressStep(2); // Planning
        setProgressStep(3); // Executing
        setResult(response);
        setProgressStep(4); // Complete
      }
    } catch (err: unknown) {
      setProgressStep(0);
      setProgressMessage('');
      setProgressPercent(0);
      // Better error messages
      const errorMsg = err instanceof Error ? err.message : 'Something went wrong. Please try again.';
      setLocalError(errorMsg);
      
      if (errorMsg.includes('Failed to fetch') || errorMsg.includes('NetworkError')) {
        setError('scan', `Cannot connect to server. Make sure the backend is running on ${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}`);
      } else if (errorMsg.includes('401') || errorMsg.includes('403')) {
        setError('scan', 'Authentication failed. Please check your API keys.');
      } else if (errorMsg.includes('429')) {
        setError('scan', 'Rate limit exceeded. Please try again in a moment.');
      } else if (errorMsg.includes('Stream ended unexpectedly')) {
        setError('scan', 'Connection interrupted. Please try again.');
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
    setShowVerification(false);
    setVerificationData(null);
    clearErrors();
    if (fileInputRef.current) fileInputRef.current.value = '';
    if (cameraInputRef.current) cameraInputRef.current.value = '';
  };

  const handleVerificationConfirm = async (verifiedData: Record<string, UIElement>, verifiedPlan: { task: string; steps: ActionStep[] }) => {
    if (!verificationData || !image) return;
    
    setLoading(true);
    setShowVerification(false);
    setProgressStep(3); // Executing verified plan
    
    try {
      const startUrl = (verificationData.uiSchema as { url_hint?: string }).url_hint || 'https://example.com';
      
      // Convert UIElement objects to plain objects for JSON serialization
      const verifiedDataPlain: Record<string, Record<string, unknown>> = {};
      for (const [key, value] of Object.entries(verifiedData.data)) {
        verifiedDataPlain[key] = {
          id: value.id,
          type: value.type,
          label: value.label,
          value: value.value,
          position: value.position
        };
      }
      
      const response = await executeVerifiedPlan(
        verifiedPlan,
        verifiedDataPlain,
        verificationData.uiSchema,
        startUrl
      );
      
      setResult(response);
      setProgressStep(4); // Complete
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : 'Execution failed';
      setLocalError(errorMsg);
      setError('scan', errorMsg);
      setProgressStep(0);
    } finally {
      setLoading(false);
    }
  };

  const handleVerificationCancel = () => {
    setShowVerification(false);
    setVerificationData(null);
    setLoading(false);
  };

  // Set current step on mount
  useEffect(() => {
    setCurrentStep('scan');
  }, [setCurrentStep]);

  return (
    <>
      {showVerification && verificationData && (
        <DataVerification
          extractedData={verificationData.data}
          actionPlan={verificationData.plan}
          onConfirm={handleVerificationConfirm}
          onCancel={handleVerificationCancel}
        />
      )}
      <div className="h-full w-full text-slate-800 relative overflow-y-auto">
        {/* Medical Background */}
        <div className="absolute inset-0 bg-gradient-to-br from-sky-50 via-blue-50 to-cyan-50">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(2,132,199,0.05),transparent_50%)]"></div>
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_80%_20%,rgba(6,182,212,0.05),transparent_50%)]"></div>
        </div>

        <div className="relative w-full mx-auto px-6 md:px-10 py-4 md:py-6 z-10">
          <div className="mb-6 sm:mb-8 text-center">
            <div className="inline-flex items-center justify-center w-14 h-14 sm:w-16 sm:h-16 rounded-2xl bg-gradient-to-br from-blue-500 via-cyan-500 to-teal-500 mb-4 shadow-lg glow-teal medical-card">
              <span className="text-2xl sm:text-3xl">📋</span>
            </div>
            <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold mb-2 gradient-text">HealthScan</h1>
            <p className="text-sm sm:text-base text-slate-600 font-medium px-2">Your AI healthcare assistant - scan forms, prescriptions, and documents</p>
          </div>
        
        {/* Progress Tracker */}
        <ProgressTracker />

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Image Upload Section */}
          <div className="medical-card p-4 sm:p-6">
            <h2 className="text-lg sm:text-xl font-semibold mb-4 text-slate-800">1. Upload or Capture Image</h2>
            
            {imagePreview ? (
              <div className="space-y-4">
                <img
                  src={imagePreview}
                  alt="Preview"
                  className="max-w-full h-auto rounded-xl border-2 border-blue-200 shadow-md"
                />
                <button
                  type="button"
                  onClick={handleReset}
                  className="text-sm text-blue-600 hover:text-blue-700 font-medium transition-colors"
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
                  <div className="border-2 border-dashed border-blue-300 rounded-xl p-8 text-center hover:border-blue-400 hover:bg-blue-50/50 transition-all medical-card">
                    <p className="text-slate-700 font-medium">Click to upload</p>
                    <p className="text-sm text-slate-500 mt-2">or drag and drop</p>
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
                  <div className="border-2 border-dashed border-blue-300 rounded-xl p-8 text-center hover:border-blue-400 hover:bg-blue-50/50 transition-all medical-card">
                    <p className="text-slate-700 font-medium">📷 Use Camera</p>
                    <p className="text-sm text-slate-500 mt-2">Mobile only</p>
                  </div>
                </label>
              </div>
            )}
          </div>

          {/* Intent Input */}
          <div className="medical-card p-4 sm:p-6">
            <h2 className="text-lg sm:text-xl font-semibold mb-4 text-slate-800">2. What do you need help with?</h2>
            <textarea
              value={intent}
              onChange={(e) => setIntent(e.target.value)}
              placeholder="Leave empty for FAST prescription extraction ⚡ OR enter: Fill form, Book appointment, Extract data..."
              className="w-full medical-card border border-blue-200 rounded-xl px-4 py-3 text-base text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400 transition-all min-h-[100px]"
              rows={3}
            />
            <p className="text-sm text-slate-600 mt-2">
              💡 <strong>Tip:</strong> Leave empty for instant prescription extraction (like ChatGPT) | Or enter intent for form filling
            </p>
          </div>

          {/* Progress Indicator */}
          {loading && (
            <div className="medical-card p-4 sm:p-6">
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
            className="w-full btn-primary disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold py-3 sm:py-4 px-6 rounded-xl transition-all flex items-center justify-center gap-2 min-h-[44px]"
          >
            {loading ? (
              <>
                <div className="spinner w-5 h-5 border-2 border-white border-t-transparent"></div>
                Processing...
              </>
            ) : (
              'Scan & Help'
            )}
          </button>

          {(localError || errors.scan) && (
            <div className="medical-card bg-red-50 border-2 border-red-200 rounded-xl p-4">
              <div className="flex items-start gap-3">
                <span className="text-2xl">⚠️</span>
                <div className="flex-1">
                  <p className="text-red-800 font-semibold mb-1">Error</p>
                  <p className="text-red-700 text-sm">{localError || errors.scan}</p>
                  {(localError || errors.scan)?.includes('Network') && (
                    <button
                      onClick={handleSubmit}
                      className="mt-3 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-medium transition-colors"
                    >
                      🔄 Retry
                    </button>
                  )}
                </div>
              </div>
            </div>
          )}
        </form>

        {/* Results */}
        {result && (
          <div className="mt-8 medical-card p-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-slate-800">Results</h2>
              <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                result.status === 'success' ? 'bg-emerald-100 text-emerald-700 border border-emerald-300' :
                result.status === 'partial' ? 'bg-amber-100 text-amber-700 border border-amber-300' :
                result.status === 'error' ? 'bg-red-100 text-red-700 border border-red-300' :
                'bg-blue-100 text-blue-700 border border-blue-300'
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
                <div className="medical-card bg-blue-50 border-blue-200 rounded-xl p-4">
                  <p className="text-blue-700">{result.message}</p>
                </div>
              )}
              
              {result.plan && result.plan.steps && (
                <div className="medical-card bg-blue-50 border-blue-200 rounded-xl p-4">
                  <h3 className="text-sm font-semibold text-slate-700 mb-3">Action Plan</h3>
                  <div className="space-y-2">
                    {result.plan.steps.map((step: ActionStep, idx: number) => (
                      <div key={idx} className="flex items-start gap-3 p-2 medical-card bg-white rounded-lg">
                        <span className="text-blue-600 font-mono text-xs mt-1">{step.step}.</span>
                        <div className="flex-1">
                          <p className="text-sm text-slate-800">
                            <span className="font-semibold capitalize">{step.action}</span>
                            {step.target && <span className="text-slate-600"> on {step.target}</span>}
                            {step.value && <span className="text-slate-500">: {step.value}</span>}
                          </p>
                          {step.description && (
                            <p className="text-xs text-slate-500 mt-1">{step.description}</p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {result.execution && (
                <div className="medical-card bg-blue-50 border-blue-200 rounded-xl p-4">
                  <h3 className="text-sm font-semibold text-slate-700 mb-3">Execution Log</h3>
                  <div className="space-y-1 max-h-60 overflow-y-auto">
                    {result.execution.logs && result.execution.logs.map((log: string, idx: number) => (
                      <div key={idx} className="text-xs font-mono text-slate-600 py-1">
                        {log.startsWith('✓') && <span className="text-emerald-600">{log}</span>}
                        {log.startsWith('✗') && <span className="text-red-600">{log}</span>}
                        {log.startsWith('⚠') && <span className="text-amber-600">{log}</span>}
                        {!log.startsWith('✓') && !log.startsWith('✗') && !log.startsWith('⚠') && log}
                      </div>
                    ))}
                  </div>
                  {result.execution.final_url && (
                    <div className="mt-3 pt-3 border-t border-blue-200">
                      <p className="text-xs text-slate-600">Final URL:</p>
                      <a href={result.execution.final_url} target="_blank" rel="noopener noreferrer" className="text-xs text-blue-600 hover:underline break-all">
                        {result.execution.final_url}
                      </a>
                    </div>
                  )}
                </div>
              )}

              {result.structured_data && result.structured_data.medications && (
                <div className="medical-card bg-blue-50 border-blue-200 rounded-xl p-4">
                  <h3 className="text-sm font-semibold text-slate-700 mb-3">📋 Extracted Prescription Data</h3>
                  <div className="space-y-3">
                    {Array.isArray(result.structured_data.medications) ? (
                      result.structured_data.medications.map((med: Medication, idx: number) => (
                        <div key={idx} className="medical-card bg-white rounded-xl p-3">
                          <div className="font-semibold text-slate-800 mb-2">{med.medication_name || 'Unknown Medication'}</div>
                          <div className="grid grid-cols-2 gap-2 text-xs">
                            {med.dosage && <div><span className="text-slate-600">Dosage:</span> <span className="text-slate-800 font-medium">{med.dosage}</span></div>}
                            {med.frequency && <div><span className="text-slate-600">Frequency:</span> <span className="text-slate-800 font-medium">{med.frequency}</span></div>}
                            {med.quantity && <div><span className="text-slate-600">Quantity:</span> <span className="text-slate-800 font-medium">{med.quantity}</span></div>}
                            {med.refills && <div><span className="text-slate-600">Refills:</span> <span className="text-slate-800 font-medium">{med.refills}</span></div>}
                          </div>
                          {med.instructions && (
                            <div className="mt-2 text-xs">
                              <span className="text-slate-600">Instructions:</span>
                              <span className="text-slate-800 ml-2">{med.instructions}</span>
                            </div>
                          )}
                        </div>
                      ))
                    ) : (
                      <div className="medical-card bg-white rounded-xl p-3">
                        <div className="font-semibold text-slate-800 mb-2">{(result.structured_data.medications as Medication).medication_name || 'Medication'}</div>
                        <div className="grid grid-cols-2 gap-2 text-xs">
                          {(result.structured_data.medications as Medication).dosage && <div><span className="text-slate-600">Dosage:</span> <span className="text-slate-800 font-medium">{(result.structured_data.medications as Medication).dosage}</span></div>}
                          {(result.structured_data.medications as Medication).frequency && <div><span className="text-slate-600">Frequency:</span> <span className="text-slate-800 font-medium">{(result.structured_data.medications as Medication).frequency}</span></div>}
                        </div>
                      </div>
                    )}
                    {result.structured_data.prescriber && (
                      <div className="text-xs text-slate-600">
                        Prescriber: <span className="text-slate-800 font-medium">{result.structured_data.prescriber}</span>
                      </div>
                    )}
                    {result.structured_data.date && (
                      <div className="text-xs text-slate-600">
                        Date: <span className="text-slate-800 font-medium">{result.structured_data.date}</span>
                      </div>
                    )}
                  </div>
                  
                  {/* Quick Actions - Integration Buttons */}
                  <div className="mt-4 pt-4 border-t border-blue-200 flex gap-2 flex-wrap">
                    <button
                      onClick={() => {
                        if (!result.structured_data?.medications) return;
                        // Store medications in localStorage (safely)
                        const medications: Medication[] = Array.isArray(result.structured_data.medications) 
                          ? result.structured_data.medications 
                          : [result.structured_data.medications as Medication];
                        safeStorage.setItem('extracted_medications', JSON.stringify(medications));
                        safeStorage.setItem('prescription_image', imagePreview || '');
                        router.push('/interactions');
                      }}
                      className="px-4 py-2 btn-primary text-white text-sm rounded-xl transition-all"
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
                          safeStorage.setItem('current_medications', medNames);
                          router.push('/diet');
                        }}
                        className="px-4 py-2 btn-primary text-white text-sm rounded-xl transition-all min-h-[44px]"
                      >
                        🥗 Get Diet Recommendations
                      </button>
                    )}
                  </div>
                </div>
              )}

              {result.extracted_data && Object.keys(result.extracted_data).length > 0 && (
                <details className="medical-card bg-blue-50 border-blue-200 rounded-xl">
                  <summary className="p-4 cursor-pointer text-sm font-semibold text-slate-700">
                    Raw Extracted Data ({Object.keys(result.extracted_data).length})
                  </summary>
                  <div className="p-4 pt-0 space-y-2 max-h-60 overflow-y-auto">
                    {Object.entries(result.extracted_data).slice(0, 10).map(([key, value]: [string, UIElement]) => (
                      <div key={key} className="text-xs p-2 medical-card bg-white rounded-lg">
                        <span className="text-blue-600 font-mono">{value.type}</span>
                        {value.label && <span className="text-slate-700 ml-2">{value.label}</span>}
                        {value.value && <span className="text-slate-500 ml-2">→ {value.value}</span>}
                      </div>
                    ))}
                  </div>
                </details>
              )}

              {result.ui_schema && result.ui_schema.elements && (
                <details className="medical-card bg-blue-50 border-blue-200 rounded-xl">
                  <summary className="p-4 cursor-pointer text-sm font-semibold text-slate-700">
                    Detected UI Elements ({result.ui_schema.elements.length})
                  </summary>
                  <div className="p-4 pt-0 space-y-2 max-h-60 overflow-y-auto">
                    {result.ui_schema.elements.slice(0, 10).map((elem: UIElement, idx: number) => (
                      <div key={idx} className="text-xs p-2 medical-card bg-white rounded-lg">
                        <span className="text-blue-600 font-mono">{elem.type}</span>
                        {elem.label && <span className="text-slate-700 ml-2">{elem.label}</span>}
                      </div>
                    ))}
                    {result.ui_schema.elements.length > 10 && (
                      <p className="text-xs text-slate-500">... and {result.ui_schema.elements.length - 10} more</p>
                    )}
                  </div>
                </details>
              )}

              <div className="flex gap-3 pt-2">
                <button
                  onClick={handleReset}
                  className="flex-1 medical-card bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium py-2 px-4 rounded-xl transition-colors border border-slate-300"
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
                    className="flex-1 btn-primary text-white font-medium py-2 px-4 rounded-xl transition-all"
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
    </>
  );
}

