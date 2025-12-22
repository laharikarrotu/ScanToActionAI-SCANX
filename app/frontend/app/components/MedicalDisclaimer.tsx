'use client';

interface MedicalDisclaimerProps {
  variant?: 'default' | 'compact' | 'footer';
  className?: string;
}

export default function MedicalDisclaimer({ variant = 'default', className = '' }: MedicalDisclaimerProps) {
  if (variant === 'footer') {
    return (
      <footer className={`medical-card border-t-2 border-blue-200 mt-12 p-6 ${className}`}>
        <div className="w-full mx-auto px-6 md:px-10">
          <div className="flex items-start gap-4">
            <div className="flex-shrink-0">
              <span className="text-2xl">⚠️</span>
            </div>
            <div className="flex-1">
              <h3 className="font-bold text-slate-800 mb-2">Important Medical Disclaimer</h3>
              <p className="text-sm text-slate-700 mb-3 leading-relaxed">
                HealthScan is an AI-powered healthcare assistant designed to provide informational support only. 
                <strong className="text-slate-900"> This tool is NOT a replacement for professional medical advice, diagnosis, or treatment.</strong> 
                Always seek the advice of your physician or other qualified health provider with any questions you may have regarding a medical condition.
              </p>
              <div className="grid md:grid-cols-2 gap-4 mt-4">
                <div>
                  <p className="text-xs font-semibold text-slate-600 mb-1">For Medical Emergencies:</p>
                  <p className="text-xs text-slate-600">Call 911 or your local emergency number immediately</p>
                </div>
                <div>
                  <p className="text-xs font-semibold text-slate-600 mb-1">Privacy & Security:</p>
                  <p className="text-xs text-slate-600">Your health information is encrypted and secure</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </footer>
    );
  }

  if (variant === 'compact') {
    return (
      <div className={`medical-card bg-amber-50 border-2 border-amber-200 rounded-xl p-3 ${className}`}>
        <div className="flex items-start gap-2">
          <span className="text-lg">⚠️</span>
          <p className="text-xs text-amber-800 leading-relaxed">
            <strong>Not a replacement for professional medical advice.</strong> Always consult your healthcare provider.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className={`medical-card bg-amber-50 border-2 border-amber-200 rounded-xl p-4 ${className}`}>
      <div className="flex items-start gap-3">
        <span className="text-xl">⚠️</span>
        <div>
          <p className="text-sm font-semibold text-amber-800 mb-1">Important Medical Disclaimer</p>
          <p className="text-xs text-amber-700 leading-relaxed">
            This tool is for informational purposes only and is not a replacement for professional medical advice, 
            diagnosis, or treatment. Always consult your healthcare provider before making any medical decisions.
          </p>
        </div>
      </div>
    </div>
  );
}

