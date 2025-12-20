'use client';

import { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { analyzeAndExecute } from '../lib/api';
import ProgressTracker from './ProgressTracker';
import { useHealthScan } from '../context/HealthScanContext';

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
  const [result, setResult] = useState<any>(null);
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

      const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${API_BASE_URL}/check-prescription-interactions`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Failed to check interactions');
      }

      const data = await response.json();
      setResult(data);
      
      // Store in context
      setInteractionResult({
        warnings: data.warnings || { major: [], moderate: [], minor: [] },
        prescription_details: data.prescription_details || [],
      });
      
      clearErrors();
    } catch (err: any) {
      const errorMsg = err.message || 'Something went wrong';
      setLocalError(errorMsg);
      
      // Error recovery: Retry suggestion
      if (err.message?.includes('Failed to fetch') || err.message?.includes('NetworkError')) {
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
    <div className="min-h-screen bg-gradient-to-br from-blue-900 to-blue-950 text-white p-4">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8 text-center">
          <h1 className="text-4xl font-bold mb-2">💊 Drug Interaction Checker</h1>
          <p className="text-blue-300">HealthScan's unique feature - Check multiple prescriptions for interactions</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Multi-Image Upload */}
          <div className="bg-zinc-800 rounded-lg p-6 border border-zinc-700">
            <h2 className="text-xl font-semibold mb-4">1. Upload Prescription Images</h2>
            
            {imagePreviews.length > 0 ? (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  {imagePreviews.map((preview, idx) => (
                    <div key={idx} className="relative">
                      <img
                        src={preview}
                        alt={`Prescription ${idx + 1}`}
                        className="w-full h-auto rounded-lg border border-zinc-700"
                      />
                      <span className="absolute top-2 left-2 bg-blue-600 px-2 py-1 rounded text-xs">
                        Prescription {idx + 1}
                      </span>
                    </div>
                  ))}
                </div>
                <button
                  type="button"
                  onClick={handleReset}
                  className="text-sm text-blue-400 hover:text-white"
                >
                  Change images
                </button>
              </div>
            ) : (
              <label className="cursor-pointer">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  multiple
                  onChange={handleFileSelect}
                  className="hidden"
                />
                <div className="border-2 border-dashed border-zinc-600 rounded-lg p-8 text-center hover:border-blue-500 transition-colors">
                  <p className="text-zinc-400">Click to upload prescription images</p>
                  <p className="text-sm text-zinc-500 mt-2">You can select multiple prescriptions</p>
                </div>
              </label>
            )}
          </div>

          {/* Allergies Input */}
          <div className="bg-zinc-800 rounded-lg p-6 border border-zinc-700">
            <h2 className="text-xl font-semibold mb-4">2. Known Allergies (Optional)</h2>
            <input
              type="text"
              value={allergies}
              onChange={(e) => setAllergies(e.target.value)}
              placeholder="e.g., Penicillin, Aspirin, Ibuprofen (comma-separated)"
              className="w-full bg-zinc-900 border border-zinc-700 rounded-lg p-4 text-white placeholder-zinc-500 focus:outline-none focus:border-blue-500"
            />
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading || images.length === 0}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-zinc-700 disabled:cursor-not-allowed text-white font-semibold py-4 px-6 rounded-lg transition-colors flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Checking Interactions...
              </>
            ) : (
              `Check ${images.length} Prescription${images.length > 1 ? 's' : ''}`
            )}
          </button>

          {(localError || errors.interactions) && (
            <div className="bg-red-900/50 border border-red-700 rounded-lg p-4 text-red-200">
              <p>{localError || errors.interactions}</p>
              {localError?.includes('Network') && (
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
              <h2 className="text-xl font-semibold">Interaction Check Results</h2>
              {!result.has_interactions && (
                <span className="px-3 py-1 bg-green-900/30 text-green-400 rounded-full text-sm font-medium">
                  ✓ Safe
                </span>
              )}
            </div>
            
            <div className="space-y-4">
              <div className="bg-zinc-900 p-4 rounded">
                <p className="text-sm text-zinc-400 mb-2">Medications Found:</p>
                <p className="text-blue-400 font-semibold">{result.medications_found}</p>
              </div>

              {result.has_interactions ? (
                <div className="space-y-4">
                  {result.interactions.major.length > 0 && (
                    <div className="bg-red-900/30 border border-red-700 rounded-lg p-4">
                      <h3 className="text-red-400 font-semibold mb-2">⚠️ Major Interactions ({result.interactions.major.length})</h3>
                      {result.interactions.major.map((interaction: any, idx: number) => (
                        <div key={idx} className="mb-3 p-3 bg-red-900/20 rounded">
                          <p className="font-semibold">{interaction.medication1} + {interaction.medication2}</p>
                          <p className="text-sm mt-1">{interaction.description}</p>
                          <p className="text-sm text-red-300 mt-2">💡 {interaction.recommendation}</p>
                        </div>
                      ))}
                    </div>
                  )}

                  {result.interactions.moderate.length > 0 && (
                    <div className="bg-yellow-900/30 border border-yellow-700 rounded-lg p-4">
                      <h3 className="text-yellow-400 font-semibold mb-2">⚡ Moderate Interactions ({result.interactions.moderate.length})</h3>
                      {result.interactions.moderate.map((interaction: any, idx: number) => (
                        <div key={idx} className="mb-3 p-3 bg-yellow-900/20 rounded">
                          <p className="font-semibold">{interaction.medication1} + {interaction.medication2}</p>
                          <p className="text-sm mt-1">{interaction.description}</p>
                          <p className="text-sm text-yellow-300 mt-2">💡 {interaction.recommendation}</p>
                        </div>
                      ))}
                    </div>
                  )}

                  {result.interactions.minor.length > 0 && (
                    <div className="bg-blue-900/30 border border-blue-700 rounded-lg p-4">
                      <h3 className="text-blue-400 font-semibold mb-2">ℹ️ Minor Interactions ({result.interactions.minor.length})</h3>
                      {result.interactions.minor.map((interaction: any, idx: number) => (
                        <div key={idx} className="mb-3 p-3 bg-blue-900/20 rounded">
                          <p className="font-semibold">{interaction.medication1} + {interaction.medication2}</p>
                          <p className="text-sm mt-1">{interaction.description}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ) : (
                <div className="bg-green-900/30 border border-green-700 rounded-lg p-4">
                  <p className="text-green-400 font-semibold">✅ No interactions detected!</p>
                  <p className="text-sm text-zinc-400 mt-2">Always consult your doctor or pharmacist for medical advice.</p>
                </div>
              )}

              <div className="flex gap-3 pt-4">
                <button
                  onClick={handleReset}
                  className="flex-1 bg-zinc-700 hover:bg-zinc-600 text-white font-medium py-2 px-4 rounded-lg transition-colors"
                >
                  Check Another Set
                </button>
                {result && result.warnings && (
                  <button
                    onClick={() => {
                      // Extract medication names from result
                      const medNames = result.prescription_details?.map((p: any) => p.medication_name).filter(Boolean).join(', ') || '';
                      if (medNames) {
                        localStorage.setItem('current_medications', medNames);
                      }
                      router.push('/diet');
                    }}
                    className="flex-1 bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-lg transition-colors"
                  >
                    🥗 Get Diet Advice
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

