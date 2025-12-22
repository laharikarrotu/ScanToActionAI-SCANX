'use client';

import { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import type { InteractionCheckResponse, InteractionWarning, PrescriptionDetail } from '../lib/types';
import ProgressTracker from './ProgressTracker';
import { useHealthScan } from '../context/HealthScanContext';
import { API_BASE_URL } from '../lib/api';
import { safeStorage } from '../lib/storage';
import MedicalDisclaimer from './MedicalDisclaimer';

export default function InteractionChecker() {
  const router = useRouter();
  const {
    prescriptionData,
    setInteractionResult,
    setCurrentStep,
    errors,
    setError,
    clearErrors,
    navigateToDiet,
  } = useHealthScan();
  
  const [images, setImages] = useState<File[]>([]);
  const [imagePreviews, setImagePreviews] = useState<string[]>([]);
  const [allergies, setAllergies] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<InteractionCheckResponse | null>(null);
  const [localError, setLocalError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // Set current step on mount
  useEffect(() => {
    setCurrentStep('interactions');
  }, [setCurrentStep]);
  
  // Show info if prescription data is available from Scanner
  useEffect(() => {
    if (prescriptionData && prescriptionData.medications.length > 0 && images.length === 0) {
      // Data available from previous step
    }
  }, [prescriptionData, images.length]);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length > 0) {
      setImages(files);
      const previews = files.map(file => {
        const reader = new FileReader();
        return new Promise<string>((resolve) => {
          reader.onloadend = () => resolve(reader.result as string);
          reader.readAsDataURL(file);
        });
      });
      Promise.all(previews).then(setImagePreviews);
      setLocalError(null);
      setResult(null);
      clearErrors();
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (images.length === 0) {
      setLocalError('Please select at least one prescription image');
      setError('interactions', 'Please select at least one prescription image');
      return;
    }

    setLoading(true);
    setLocalError(null);
    setResult(null);
    clearErrors();

    try {
      const formData = new FormData();
      // FastAPI accepts List[UploadFile] - append all files with key 'files'
      images.forEach((file) => {
        formData.append('files', file);
      });
      if (allergies.trim()) {
        formData.append('allergies', allergies);
      }

      const response = await fetch(`${API_BASE_URL}/check-prescription-interactions`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        let errorMessage = 'Failed to check interactions';
        try {
          const error = await response.json();
          errorMessage = error.detail || error.message || errorMessage;
        } catch (e) {
          errorMessage = response.statusText || errorMessage;
        }
        throw new Error(errorMessage);
      }

      const data = await response.json();
      
      // Validate response structure
      if (data.status === 'error') {
        throw new Error(data.message || 'An error occurred while checking interactions');
      }
      
      // Ensure we have the expected fields - backend provides both 'warnings' and 'interactions'
      const warnings = data.warnings || data.interactions || { major: [], moderate: [], minor: [] };
      const prescriptionDetails = data.prescription_details || data.prescriptions || [];
      
      if (!warnings || (!prescriptionDetails.length && data.medications_found === 0)) {
        throw new Error('Invalid response format from server');
      }
      
      setResult(data);
      
      // Store in context
      setInteractionResult({
        warnings: warnings,
        prescription_details: prescriptionDetails,
      });
      
      clearErrors();
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : 'Something went wrong';
      setLocalError(errorMsg);
      
      // Error recovery: Retry suggestion
      if (errorMsg.includes('Failed to fetch') || errorMsg.includes('NetworkError')) {
        setError('interactions', 'Network error. Please check your connection and try again.');
      } else {
        setError('interactions', errorMsg);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setImages([]);
    setImagePreviews([]);
    setAllergies('');
    setResult(null);
    setLocalError(null);
    clearErrors();
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <div className="h-full w-full text-slate-800 relative overflow-y-auto">
      {/* Medical Background */}
      <div className="absolute inset-0 bg-gradient-to-br from-sky-50 via-blue-50 to-cyan-50">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(2,132,199,0.05),transparent_50%)]"></div>
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_80%_20%,rgba(6,182,212,0.05),transparent_50%)]"></div>
      </div>

      <div className="relative w-full mx-auto px-6 md:px-10 py-4 md:py-6 z-10">
        <div className="mb-6 sm:mb-8 text-center">
          <div className="inline-flex items-center justify-center w-14 h-14 sm:w-16 sm:h-16 rounded-2xl bg-gradient-to-br from-blue-500 via-cyan-500 to-teal-500 mb-4 shadow-lg glow-teal medical-card">
            <span className="text-2xl sm:text-3xl">💊</span>
          </div>
          <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold mb-2 gradient-text">Drug Interaction Checker</h1>
          <p className="text-sm sm:text-base text-slate-600 font-medium px-2">HealthScan's unique feature - Check multiple prescriptions for interactions</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6" aria-label="Drug interaction checker form">
          {/* Multi-Image Upload */}
          <div className="medical-card p-4 sm:p-6">
            <h2 className="text-lg sm:text-xl font-semibold mb-4 text-slate-800">1. Upload Prescription Images</h2>
            
            {imagePreviews.length > 0 ? (
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {imagePreviews.map((preview, idx) => (
                    <div key={idx} className="relative medical-card overflow-hidden">
                      <img
                        src={preview}
                        alt={`Prescription ${idx + 1}`}
                        className="w-full h-auto"
                      />
                      <span className="absolute top-3 left-3 bg-gradient-to-r from-blue-500 to-cyan-500 text-white px-3 py-1.5 rounded-lg text-xs font-semibold shadow-lg">
                        Prescription {idx + 1}
                      </span>
                    </div>
                  ))}
                </div>
                <button
                  type="button"
                  onClick={handleReset}
                  className="text-sm text-blue-600 hover:text-blue-700 font-medium transition-colors"
                  aria-label="Change prescription images"
                >
                  Change images
                </button>
              </div>
            ) : (
              <label className="cursor-pointer block">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  multiple
                  onChange={handleFileSelect}
                  className="hidden"
                  aria-label="Upload prescription images"
                />
                <div className="border-2 border-dashed border-blue-300 rounded-xl p-8 md:p-12 text-center hover:border-blue-400 hover:bg-blue-50/50 transition-all medical-card">
                  <div className="text-4xl mb-3">📋</div>
                  <p className="text-slate-700 font-medium">Click to upload prescription images</p>
                  <p className="text-sm text-slate-500 mt-2">You can select multiple prescriptions</p>
                </div>
              </label>
            )}
          </div>

          {/* Allergies Input */}
          <div className="medical-card p-4 sm:p-6">
            <h2 className="text-lg sm:text-xl font-semibold mb-4 text-slate-800">2. Known Allergies (Optional)</h2>
            <input
              type="text"
              value={allergies}
              onChange={(e) => setAllergies(e.target.value)}
              placeholder="e.g., Penicillin, Aspirin, Ibuprofen (comma-separated)"
              className="w-full medical-card border border-blue-200 rounded-xl px-4 py-3 text-base text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400 transition-all min-h-[44px]"
              aria-label="Enter known allergies"
            />
            <p className="text-xs text-slate-500 mt-2">This helps us check for drug-allergy interactions</p>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading || images.length === 0}
            className="w-full btn-primary disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold py-3 sm:py-4 px-6 rounded-xl transition-all flex items-center justify-center gap-2 min-h-[44px]"
            aria-label={loading ? "Checking interactions" : `Check ${images.length} prescription${images.length > 1 ? 's' : ''}`}
          >
            {loading ? (
              <>
                <div className="spinner w-5 h-5 border-2 border-white border-t-transparent"></div>
                <span>Analyzing Interactions...</span>
              </>
            ) : (
              <>
                <span>🔍</span>
                <span>Check {images.length} Prescription{images.length > 1 ? 's' : ''}</span>
              </>
            )}
          </button>

          {(localError || errors.interactions) && (
            <div className="medical-card bg-red-50 border-2 border-red-200 rounded-xl p-4">
              <div className="flex items-start gap-3">
                <span className="text-2xl">⚠️</span>
                <div className="flex-1">
                  <p className="text-red-800 font-semibold mb-1">Error</p>
                  <p className="text-red-700 text-sm">{localError || errors.interactions}</p>
                  {localError?.includes('Network') && (
                    <button
                      onClick={handleSubmit}
                      className="mt-3 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-medium transition-colors"
                      aria-label="Retry checking interactions"
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
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-slate-800">Interaction Check Results</h2>
              {!result.has_interactions && (
                <span className="px-4 py-2 bg-gradient-to-r from-emerald-500 to-teal-500 text-white rounded-full text-sm font-semibold shadow-lg glow-green">
                  ✓ Safe
                </span>
              )}
            </div>
            
            <div className="space-y-4">
              <div className="medical-card bg-blue-50 border-blue-200 p-4 rounded-xl">
                <p className="text-sm text-slate-600 mb-2 font-medium">Medications Found:</p>
                <p className="text-blue-700 font-bold text-lg">{result.medications_found}</p>
              </div>

              {result.has_interactions ? (
                <div className="space-y-4">
                  {result.interactions.major.length > 0 && (
                    <div className="medical-card bg-red-50 border-2 border-red-300 rounded-xl p-5">
                      <div className="flex items-center gap-2 mb-4">
                        <span className="text-2xl">🚨</span>
                        <h3 className="text-red-700 font-bold text-lg">Major Interactions ({result.interactions.major.length})</h3>
                      </div>
                      <div className="bg-white/80 rounded-lg p-3 mb-3 border border-red-200">
                        <p className="text-xs text-red-600 font-semibold uppercase tracking-wide mb-2">⚠️ URGENT: Consult Your Doctor Immediately</p>
                        <p className="text-sm text-slate-600">These interactions require immediate medical attention before taking these medications together.</p>
                      </div>
                      {result.interactions.major.map((interaction: InteractionWarning, idx: number) => (
                        <div key={idx} className="mb-4 p-4 bg-white rounded-lg border-l-4 border-red-500 shadow-sm">
                          <p className="font-bold text-slate-800 mb-2">{interaction.medication1} + {interaction.medication2}</p>
                          <p className="text-sm text-slate-700 mb-2">{interaction.description}</p>
                          <div className="mt-3 p-2 bg-blue-50 rounded border border-blue-200">
                            <p className="text-sm text-blue-800 font-medium">💡 Recommendation: {interaction.recommendation}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {result.interactions.moderate.length > 0 && (
                    <div className="medical-card bg-yellow-50 border-2 border-yellow-300 rounded-xl p-5">
                      <div className="flex items-center gap-2 mb-4">
                        <span className="text-2xl">⚡</span>
                        <h3 className="text-yellow-700 font-bold text-lg">Moderate Interactions ({result.interactions.moderate.length})</h3>
                      </div>
                      <p className="text-sm text-slate-600 mb-3">Monitor closely and discuss with your healthcare provider.</p>
                      {result.interactions.moderate.map((interaction: InteractionWarning, idx: number) => (
                        <div key={idx} className="mb-4 p-4 bg-white rounded-lg border-l-4 border-yellow-500 shadow-sm">
                          <p className="font-bold text-slate-800 mb-2">{interaction.medication1} + {interaction.medication2}</p>
                          <p className="text-sm text-slate-700 mb-2">{interaction.description}</p>
                          <div className="mt-3 p-2 bg-blue-50 rounded border border-blue-200">
                            <p className="text-sm text-blue-800 font-medium">💡 Recommendation: {interaction.recommendation}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {result.interactions.minor.length > 0 && (
                    <div className="medical-card bg-blue-50 border-2 border-blue-300 rounded-xl p-5">
                      <div className="flex items-center gap-2 mb-4">
                        <span className="text-2xl">ℹ️</span>
                        <h3 className="text-blue-700 font-bold text-lg">Minor Interactions ({result.interactions.minor.length})</h3>
                      </div>
                      <p className="text-sm text-slate-600 mb-3">Generally safe, but monitor for any unusual symptoms.</p>
                      {result.interactions.minor.map((interaction: InteractionWarning, idx: number) => (
                        <div key={idx} className="mb-3 p-4 bg-white rounded-lg border-l-4 border-blue-500 shadow-sm">
                          <p className="font-semibold text-slate-800 mb-1">{interaction.medication1} + {interaction.medication2}</p>
                          <p className="text-sm text-slate-700">{interaction.description}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ) : (
                <div className="medical-card bg-emerald-50 border-2 border-emerald-300 rounded-xl p-6 text-center">
                  <div className="text-5xl mb-4">✅</div>
                  <p className="text-emerald-700 font-bold text-lg mb-2">No interactions detected!</p>
                  <p className="text-sm text-slate-600">Your medications appear safe to take together. However, always consult your doctor or pharmacist for final medical advice.</p>
                </div>
              )}

              {/* Medical Disclaimer */}
              <div className="medical-card bg-amber-50 border-2 border-amber-200 rounded-xl p-4 mt-6">
                <div className="flex items-start gap-3">
                  <span className="text-xl">⚠️</span>
                  <div>
                    <p className="text-sm font-semibold text-amber-800 mb-1">Important Medical Disclaimer</p>
                    <p className="text-xs text-amber-700">This tool is for informational purposes only and is not a replacement for professional medical advice. Always consult your healthcare provider before making any changes to your medications.</p>
                  </div>
                </div>
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  onClick={handleReset}
                  className="flex-1 medical-card bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold py-3 px-4 rounded-xl transition-colors border border-slate-300"
                  aria-label="Check another set of prescriptions"
                >
                  Check Another Set
                </button>
                {result && result.warnings && (
                  <button
                    onClick={() => {
                      const medNames = result.prescription_details?.map((p: PrescriptionDetail) => p.medication_name).filter(Boolean).join(', ') || '';
                      if (medNames) {
                        safeStorage.setItem('current_medications', medNames);
                      }
                      navigateToDiet();
                    }}
                    className="flex-1 btn-primary text-white font-semibold py-3 px-4 rounded-xl transition-all min-h-[44px]"
                    aria-label="Get diet advice based on medications"
                  >
                    🥗 Get Diet Advice
                  </button>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Footer Medical Disclaimer */}
        <MedicalDisclaimer variant="footer" className="mt-12" />
      </div>
    </div>
  );
}

