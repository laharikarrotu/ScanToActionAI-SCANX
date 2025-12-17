'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

export default function Nav() {
  const pathname = usePathname();
  
  return (
    <nav className="bg-zinc-900 border-b border-zinc-800">
      <div className="max-w-4xl mx-auto px-4 py-3 flex gap-4">
        <Link 
          href="/" 
          className={`px-4 py-2 rounded ${pathname === '/' ? 'bg-blue-600 text-white' : 'text-zinc-400 hover:text-white'}`}
        >
          Form Scanner
        </Link>
        <Link 
          href="/interactions" 
          className={`px-4 py-2 rounded ${pathname === '/interactions' ? 'bg-blue-600 text-white' : 'text-zinc-400 hover:text-white'}`}
        >
          💊 Drug Interactions
        </Link>
        <Link 
          href="/diet" 
          className={`px-4 py-2 rounded ${pathname === '/diet' ? 'bg-green-600 text-white' : 'text-zinc-400 hover:text-white'}`}
        >
          🥗 Diet Portal
        </Link>
      </div>
    </nav>
  );
}

