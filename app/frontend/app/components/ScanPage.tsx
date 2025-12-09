'use client';

import { useState, useRef } from 'react';
import { analyzeAndExecute } from '../lib/api';

export default function ScanPage() {
  const [image, setImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [intent, setIntent] = useState('');
  const [loading, setLoading] = useState(false);
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

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await analyzeAndExecute(image, intent);
      setResult(response);
    } catch (err: any) {
      setError(err.message || 'Something went wrong');
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
    <div className="min-h-screen bg-gradient-to-br from-zinc-900 to-black text-white p-4">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8 text-center">
          <h1 className="text-4xl font-bold mb-2">SCANX</h1>
          <p className="text-zinc-400">Scan any interface and turn it into actions</p>
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
            <h2 className="text-xl font-semibold mb-4">2. What do you want to do?</h2>
            <textarea
              value={intent}
              onChange={(e) => setIntent(e.target.value)}
              placeholder="e.g., Book this hotel for 2 nights starting Friday"
              className="w-full bg-zinc-900 border border-zinc-700 rounded-lg p-4 text-white placeholder-zinc-500 focus:outline-none focus:border-green-500"
              rows={3}
            />
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading || !image || !intent.trim()}
            className="w-full bg-green-500 hover:bg-green-600 disabled:bg-zinc-700 disabled:cursor-not-allowed text-white font-semibold py-4 px-6 rounded-lg transition-colors"
          >
            {loading ? 'Processing...' : 'Scan & Execute'}
          </button>

          {error && (
            <div className="bg-red-900/50 border border-red-700 rounded-lg p-4 text-red-200">
              {error}
            </div>
          )}
        </form>

        {/* Results */}
        {result && (
          <div className="mt-8 bg-zinc-800 rounded-lg p-6 border border-zinc-700">
            <h2 className="text-xl font-semibold mb-4">Results</h2>
            <div className="space-y-4">
              <div>
                <p className="text-sm text-zinc-400 mb-2">Status:</p>
                <p className="text-green-400 font-semibold">{result.status}</p>
              </div>
              
              {result.plan && (
                <div>
                  <p className="text-sm text-zinc-400 mb-2">Plan:</p>
                  <pre className="bg-zinc-900 p-4 rounded text-xs overflow-x-auto">
                    {JSON.stringify(result.plan, null, 2)}
                  </pre>
                </div>
              )}

              {result.execution && (
                <div>
                  <p className="text-sm text-zinc-400 mb-2">Execution:</p>
                  <pre className="bg-zinc-900 p-4 rounded text-xs overflow-x-auto">
                    {JSON.stringify(result.execution, null, 2)}
                  </pre>
                </div>
              )}

              <button
                onClick={handleReset}
                className="mt-4 text-sm text-zinc-400 hover:text-white"
              >
                Start over
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

