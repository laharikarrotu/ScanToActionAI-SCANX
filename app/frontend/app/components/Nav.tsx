'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState } from 'react';

export default function Nav() {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  
  return (
    <nav className="glass-strong border-b border-blue-200/50 sticky top-0 z-50 backdrop-blur-xl bg-white/95">
      <div className="max-w-7xl mx-auto px-4 md:px-6 py-3 md:py-4">
        {/* Desktop Navigation - Medical Theme */}
        <div className="hidden md:flex items-center gap-2">
          <Link 
            href="/" 
            className={`px-4 py-2.5 rounded-xl transition-all font-semibold text-sm medical-card ${
              pathname === '/' 
                ? 'bg-gradient-to-r from-blue-500 to-cyan-500 text-white shadow-lg glow' 
                : 'text-slate-700 hover:text-blue-600 hover:bg-blue-50 border-blue-100'
            }`}
          >
            💬 Chat Assistant
          </Link>
          <Link 
            href="/interactions" 
            className={`px-4 py-2.5 rounded-xl transition-all font-semibold text-sm medical-card ${
              pathname === '/interactions' 
                ? 'bg-gradient-to-r from-blue-500 to-teal-500 text-white shadow-lg glow-teal' 
                : 'text-slate-700 hover:text-blue-600 hover:bg-blue-50 border-blue-100'
            }`}
          >
            💊 Drug Interactions
          </Link>
          <Link 
            href="/diet" 
            className={`px-4 py-2.5 rounded-xl transition-all font-semibold text-sm medical-card ${
              pathname === '/diet' 
                ? 'bg-gradient-to-r from-emerald-500 to-teal-500 text-white shadow-lg glow-green' 
                : 'text-slate-700 hover:text-emerald-600 hover:bg-emerald-50 border-emerald-100'
            }`}
          >
            🥗 Diet Portal
          </Link>
        </div>

        {/* Mobile Navigation - Medical Theme */}
        <div className="md:hidden">
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="flex items-center justify-between w-full text-slate-800 hover:text-blue-600 transition-colors"
          >
            <span className="text-lg font-bold gradient-text">HealthScan</span>
            <svg
              className={`w-6 h-6 transition-transform duration-300 ${mobileMenuOpen ? 'rotate-180' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          
          {mobileMenuOpen && (
            <div className="mt-3 space-y-2 slide-up">
              <Link 
                href="/" 
                onClick={() => setMobileMenuOpen(false)}
                className={`block px-4 py-3 rounded-xl transition-all font-semibold medical-card ${
                  pathname === '/' 
                    ? 'bg-gradient-to-r from-blue-500 to-cyan-500 text-white shadow-lg' 
                    : 'text-slate-700 hover:text-blue-600 hover:bg-blue-50 border-blue-100'
                }`}
              >
                💬 Chat Assistant
              </Link>
              <Link 
                href="/interactions" 
                onClick={() => setMobileMenuOpen(false)}
                className={`block px-4 py-3 rounded-xl transition-all font-semibold medical-card ${
                  pathname === '/interactions' 
                    ? 'bg-gradient-to-r from-blue-500 to-teal-500 text-white shadow-lg' 
                    : 'text-slate-700 hover:text-blue-600 hover:bg-blue-50 border-blue-100'
                }`}
              >
                💊 Drug Interactions
              </Link>
              <Link 
                href="/diet" 
                onClick={() => setMobileMenuOpen(false)}
                className={`block px-4 py-3 rounded-xl transition-all font-semibold medical-card ${
                  pathname === '/diet' 
                    ? 'bg-gradient-to-r from-emerald-500 to-teal-500 text-white shadow-lg' 
                    : 'text-slate-700 hover:text-emerald-600 hover:bg-emerald-50 border-emerald-100'
                }`}
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

