import dynamic from 'next/dynamic';

// Lazy load DietPortal for code splitting
const DietPortal = dynamic(() => import('../components/DietPortal'), {
  loading: () => <div className="flex items-center justify-center h-screen"><div className="text-blue-600">Loading diet portal...</div></div>,
});

export default function DietPage() {
  return <DietPortal />;
}
