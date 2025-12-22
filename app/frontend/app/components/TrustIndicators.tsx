'use client';

export default function TrustIndicators() {
  return (
    <div className="bg-blue-50/50 rounded-xl p-3 border border-blue-100">
      <div className="flex flex-wrap items-center justify-center gap-4 md:gap-6 text-xs">
        <div className="flex items-center gap-2 px-3 py-1.5 bg-white rounded-lg border border-blue-100 shadow-sm">
          <span className="text-base">🔒</span>
          <span className="font-semibold text-slate-700">Encrypted & Secure</span>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 bg-white rounded-lg border border-blue-100 shadow-sm">
          <span className="text-base">🛡️</span>
          <span className="font-semibold text-slate-700">HIPAA Compliant</span>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 bg-white rounded-lg border border-blue-100 shadow-sm">
          <span className="text-base">✅</span>
          <span className="font-semibold text-slate-700">Privacy Protected</span>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 bg-white rounded-lg border border-blue-100 shadow-sm">
          <span className="text-base">⚕️</span>
          <span className="font-semibold text-slate-700">Medical Grade Security</span>
        </div>
      </div>
    </div>
  );
}

