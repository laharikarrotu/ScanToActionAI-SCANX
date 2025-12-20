'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState } from 'react';

export default function Nav() {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  
  return (
    <nav className="bg-zinc-900 border-b border-zinc-800 sticky top-0 z-50">
      <div className="max-w-4xl mx-auto px-4 py-3">
        {/* Desktop Navigation */}
        <div className="hidden md:flex gap-4">
          <Link 
            href="/" 
            className={`px-4 py-2 rounded transition-colors ${pathname === '/' ? 'bg-blue-600 text-white' : 'text-zinc-400 hover:text-white hover:bg-zinc-800'}`}
          >
            Form Scanner
          </Link>
          <Link 
            href="/interactions" 
            className={`px-4 py-2 rounded transition-colors ${pathname === '/interactions' ? 'bg-blue-600 text-white' : 'text-zinc-400 hover:text-white hover:bg-zinc-800'}`}
          >
            💊 Drug Interactions
          </Link>
          <Link 
            href="/diet" 
            className={`px-4 py-2 rounded transition-colors ${pathname === '/diet' ? 'bg-green-600 text-white' : 'text-zinc-400 hover:text-white hover:bg-zinc-800'}`}
          >
            🥗 Diet Portal
          </Link>
        </div>

        {/* Mobile Navigation */}
        <div className="md:hidden">
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="flex items-center justify-between w-full text-zinc-400 hover:text-white"
          >
            <span className="text-lg font-semibold">HealthScan</span>
            <svg
              className={`w-6 h-6 transition-transform ${mobileMenuOpen ? 'rotate-180' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          
          {mobileMenuOpen && (
            <div className="mt-3 space-y-2 animate-in fade-in slide-in-from-top-2">
              <Link 
                href="/" 
                onClick={() => setMobileMenuOpen(false)}
                className={`block px-4 py-2 rounded transition-colors ${pathname === '/' ? 'bg-blue-600 text-white' : 'text-zinc-400 hover:text-white hover:bg-zinc-800'}`}
              >
                Form Scanner
              </Link>
              <Link 
                href="/interactions" 
                onClick={() => setMobileMenuOpen(false)}
                className={`block px-4 py-2 rounded transition-colors ${pathname === '/interactions' ? 'bg-blue-600 text-white' : 'text-zinc-400 hover:text-white hover:bg-zinc-800'}`}
              >
                💊 Drug Interactions
              </Link>
              <Link 
                href="/diet" 
                onClick={() => setMobileMenuOpen(false)}
                className={`block px-4 py-2 rounded transition-colors ${pathname === '/diet' ? 'bg-green-600 text-white' : 'text-zinc-400 hover:text-white hover:bg-zinc-800'}`}
              >
                🥗 Diet Portal
              </Link>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
}

