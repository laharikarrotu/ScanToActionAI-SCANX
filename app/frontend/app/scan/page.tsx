import dynamic from 'next/dynamic';

// Lazy load ScanPage for code splitting
const ScanPage = dynamic(() => import('../components/ScanPage'), {
  loading: () => <div className="flex items-center justify-center h-screen"><div className="text-blue-600">Loading scanner...</div></div>,
});

export default function ScanPageRoute() {
  return <ScanPage />;
}

