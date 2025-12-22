'use client';

interface MedicalLoadingProps {
  message?: string;
  variant?: 'default' | 'prescription' | 'interactions' | 'diet';
}

export default function MedicalLoading({ message, variant = 'default' }: MedicalLoadingProps) {
  const messages = {
    default: 'Processing...',
    prescription: 'Analyzing prescription...',
    interactions: 'Checking for drug interactions...',
    diet: 'Generating diet recommendations...',
  };

  const displayMessage = message || messages[variant];

  return (
    <div className="medical-card bg-white rounded-2xl p-6 shadow-lg">
      <div className="flex items-center gap-4">
        <div className="relative">
          <div className="spinner w-10 h-10 border-3 border-blue-500 border-t-transparent"></div>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-lg">⚕️</span>
          </div>
        </div>
        <div className="flex-1">
          <p className="font-semibold text-slate-800 mb-1">{displayMessage}</p>
          <p className="text-xs text-slate-500">Please wait while we process your request securely</p>
        </div>
      </div>
      <div className="mt-4 flex gap-1">
        <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0s' }}></div>
        <div className="w-2 h-2 bg-cyan-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
        <div className="w-2 h-2 bg-teal-500 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
      </div>
    </div>
  );
}

