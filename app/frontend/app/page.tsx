import dynamic from 'next/dynamic';

// Lazy load ChatAgent for better initial page load
const ChatAgent = dynamic(() => import('./components/ChatAgent'), {
  loading: () => <div className="flex items-center justify-center h-screen"><div className="text-blue-600">Loading...</div></div>,
  ssr: false // ChatAgent uses client-side features
});

export default function Home() {
  return <ChatAgent />;
}
