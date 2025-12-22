'use client';

interface MedicalErrorProps {
  message: string;
  severity?: 'error' | 'warning' | 'info';
  onRetry?: () => void;
  retryLabel?: string;
}

export default function MedicalError({ message, severity = 'error', onRetry, retryLabel = 'Retry' }: MedicalErrorProps) {
  const configs = {
    error: {
      icon: '⚠️',
      bgColor: 'bg-red-50',
      borderColor: 'border-red-300',
      textColor: 'text-red-800',
      title: 'Error',
      suggestions: [
        'Check your internet connection',
        'Verify the image is clear and readable',
        'Try uploading a different image format (JPG, PNG)',
      ],
    },
    warning: {
      icon: '⚡',
      bgColor: 'bg-amber-50',
      borderColor: 'border-amber-300',
      textColor: 'text-amber-800',
      title: 'Warning',
      suggestions: [
        'Please review the information carefully',
        'Consult your healthcare provider if unsure',
      ],
    },
    info: {
      icon: 'ℹ️',
      bgColor: 'bg-blue-50',
      borderColor: 'border-blue-300',
      textColor: 'text-blue-800',
      title: 'Information',
      suggestions: [],
    },
  };

  const config = configs[severity];

  return (
    <div className={`medical-card ${config.bgColor} border-2 ${config.borderColor} rounded-xl p-5`}>
      <div className="flex items-start gap-3">
        <span className="text-2xl">{config.icon}</span>
        <div className="flex-1">
          <p className={`font-bold ${config.textColor} mb-2`}>{config.title}</p>
          <p className={`text-sm ${config.textColor.replace('800', '700')} mb-3`}>{message}</p>
          
          {config.suggestions.length > 0 && (
            <div className="mt-3 space-y-1">
              <p className={`text-xs font-semibold ${config.textColor} mb-2`}>Suggestions:</p>
              <ul className="list-disc list-inside space-y-1">
                {config.suggestions.map((suggestion, idx) => (
                  <li key={idx} className={`text-xs ${config.textColor.replace('800', '600')}`}>
                    {suggestion}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {onRetry && (
            <button
              onClick={onRetry}
              className={`mt-4 px-4 py-2 bg-gradient-to-r ${severity === 'error' ? 'from-red-500 to-red-600' : 'from-blue-500 to-blue-600'} text-white rounded-lg text-sm font-semibold hover:shadow-lg transition-all`}
              aria-label={retryLabel}
            >
              🔄 {retryLabel}
            </button>
          )}

          {severity === 'error' && (
            <div className="mt-4 pt-3 border-t border-red-200">
              <p className="text-xs text-red-600">
                <strong>Need help?</strong> If this problem persists, please contact support or consult your healthcare provider.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

