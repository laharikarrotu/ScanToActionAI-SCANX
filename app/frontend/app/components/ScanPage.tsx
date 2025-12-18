'use client';

import { useState, useRef } from 'react';
import { analyzeAndExecute } from '../lib/api';
import ProgressIndicator from './ProgressIndicator';

export default function ScanPage() {
  const [image, setImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [intent, setIntent] = useState('');
  const [loading, setLoading] = useState(false);
  const [progressStep, setProgressStep] = useState(0);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
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
      setError(null);
      setResult(null);
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
      setError(null);
      setResult(null);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!image || !intent.trim()) {
      setError('Please select an image and enter your intent');
      return;
    }

    // Validate image size (max 10MB)
    if (image.size > 10 * 1024 * 1024) {
      setError('Image is too large. Please use an image smaller than 10MB.');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);
    setProgressStep(1); // Analyzing image

    try {
      const response = await analyzeAndExecute(image, intent);
      setProgressStep(2); // Planning
      
      // Check for API errors in response
      if (response.status === 'error') {
        setError(response.message || 'Failed to process request');
        setProgressStep(0);
        return;
      }
      
      setProgressStep(3); // Executing
      setResult(response);
      setProgressStep(4); // Complete
    } catch (err: any) {
      setProgressStep(0);
      // Better error messages
      if (err.message?.includes('Failed to fetch') || err.message?.includes('NetworkError')) {
        setError('Cannot connect to server. Make sure the backend is running on http://localhost:8000');
      } else if (err.message?.includes('401') || err.message?.includes('403')) {
        setError('Authentication failed. Please check your API keys.');
      } else if (err.message?.includes('429')) {
        setError('Rate limit exceeded. Please try again in a moment.');
      } else {
        setError(err.message || 'Something went wrong. Please try again.');
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
    setError(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
    if (cameraInputRef.current) cameraInputRef.current.value = '';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 to-blue-950 text-white p-4">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8 text-center">
          <h1 className="text-4xl font-bold mb-2">HealthScan</h1>
          <p className="text-blue-300">Your AI healthcare assistant - scan forms, prescriptions, and documents</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Image Upload Section */}
          <div className="bg-zinc-800 rounded-lg p-6 border border-zinc-700">
            <h2 className="text-xl font-semibold mb-4">1. Upload or Capture Image</h2>
            
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
          <div className="bg-zinc-800 rounded-lg p-6 border border-zinc-700">
            <h2 className="text-xl font-semibold mb-4">2. What do you need help with?</h2>
            <textarea
              value={intent}
              onChange={(e) => setIntent(e.target.value)}
              placeholder="e.g., Fill out this patient intake form, Book an appointment for next week, Help me understand this prescription, Extract my insurance information"
              className="w-full bg-zinc-900 border border-zinc-700 rounded-lg p-4 text-white placeholder-zinc-500 focus:outline-none focus:border-blue-500"
              rows={3}
            />
            <p className="text-sm text-zinc-500 mt-2">
              Examples: Fill medical forms • Book appointments • Read prescriptions • Extract insurance info
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

          {error && (
            <div className="bg-red-900/50 border border-red-700 rounded-lg p-4 text-red-200">
              {error}
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
                    {result.plan.steps.map((step: any, idx: number) => (
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

              {result.ui_schema && result.ui_schema.elements && (
                <details className="bg-zinc-900/50 rounded-lg border border-zinc-700">
                  <summary className="p-4 cursor-pointer text-sm font-semibold text-zinc-300">
                    Detected UI Elements ({result.ui_schema.elements.length})
                  </summary>
                  <div className="p-4 pt-0 space-y-2 max-h-60 overflow-y-auto">
                    {result.ui_schema.elements.slice(0, 10).map((elem: any, idx: number) => (
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
                    onClick={() => window.open(`/api/screenshot/${result.execution.screenshot_path}`, '_blank')}
                    className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors"
                  >
                    View Screenshot
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

