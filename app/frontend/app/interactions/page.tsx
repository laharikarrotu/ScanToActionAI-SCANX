import dynamic from 'next/dynamic';

// Lazy load InteractionChecker for code splitting
const InteractionChecker = dynamic(() => import('../components/InteractionChecker'), {
  loading: () => <div className="flex items-center justify-center h-screen"><div className="text-blue-600">Loading interaction checker...</div></div>,
});

export default function InteractionsPage() {
  return <InteractionChecker />;
}

