'use client';

interface EmptyStateProps {
  type: 'prescription' | 'interactions' | 'diet' | 'chat';
  message?: string;
  actionLabel?: string;
  onAction?: () => void;
}

export default function EmptyState({ type, message, actionLabel, onAction }: EmptyStateProps) {
  const configs = {
    prescription: {
      icon: '📋',
      title: 'No Prescription Uploaded',
      defaultMessage: 'Upload a prescription image to get started with HealthScan',
      defaultAction: 'Upload Prescription',
      gradient: 'from-blue-500 to-cyan-500',
    },
    interactions: {
      icon: '💊',
      title: 'No Prescriptions to Check',
      defaultMessage: 'Upload multiple prescription images to check for drug interactions',
      defaultAction: 'Upload Prescriptions',
      gradient: 'from-blue-500 to-teal-500',
    },
    diet: {
      icon: '🥗',
      title: 'Get Personalized Diet Recommendations',
      defaultMessage: 'Enter your medical condition to receive personalized diet advice',
      defaultAction: 'Get Started',
      gradient: 'from-emerald-500 to-teal-500',
    },
    chat: {
      icon: '💬',
      title: 'Start a Conversation',
      defaultMessage: 'Ask me anything about your medications, interactions, or diet',
      defaultAction: 'Ask a Question',
      gradient: 'from-blue-500 to-purple-500',
    },
  };

  const config = configs[type];

  return (
    <div className="medical-card p-8 md:p-12 text-center">
      <div className={`inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-gradient-to-br ${config.gradient} mb-6 shadow-lg`}>
        <span className="text-4xl">{config.icon}</span>
      </div>
      <h3 className="text-xl font-bold text-slate-800 mb-3">{config.title}</h3>
      <p className="text-slate-600 mb-6 w-full mx-auto">
        {message || config.defaultMessage}
      </p>
      {onAction && (
        <button
          onClick={onAction}
          className={`px-6 py-3 bg-gradient-to-r ${config.gradient} text-white font-semibold rounded-xl shadow-lg hover:shadow-xl transition-all`}
          aria-label={actionLabel || config.defaultAction}
        >
          {actionLabel || config.defaultAction}
        </button>
      )}
    </div>
  );
}

