'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState } from 'react';
import NavLink from './NavLink';

export default function Nav() {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  
  const navLinks = [
    { href: '/', label: 'Chat Assistant', icon: '💬' },
    { href: '/scan', label: 'Scan Prescription', icon: '📋' },
    { href: '/interactions', label: 'Drug Interactions', icon: '💊' },
    { href: '/diet', label: 'Diet Portal', icon: '🥗' },
  ];
  
  return (
    <nav className="bg-white border-b border-slate-200 shadow-sm sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-3 group">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center shadow-md group-hover:shadow-lg transition-shadow">
              <span className="text-xl">🏥</span>
            </div>
            <div>
              <h1 className="text-lg font-bold text-slate-900">HealthScan</h1>
              <p className="text-xs text-slate-500 hidden sm:block">AI Healthcare Assistant</p>
            </div>
          </Link>

          {/* Desktop Navigation - Using NavLink with loading states */}
          <div className="hidden md:flex items-center gap-1">
            {navLinks.map((link) => (
              <NavLink
                key={link.href}
                href={link.href}
                label={link.label}
                icon={link.icon}
                onClick={() => setMobileMenuOpen(false)}
              />
            ))}
        </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 rounded-lg text-slate-700 hover:bg-slate-100 transition-colors"
            aria-label="Toggle menu"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              {mobileMenuOpen ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              )}
            </svg>
          </button>
        </div>
          
        {/* Mobile Navigation - Using NavLink with loading states */}
          {mobileMenuOpen && (
          <div className="md:hidden border-t border-slate-200 py-2">
            {navLinks.map((link) => (
              <NavLink
                key={link.href}
                href={link.href}
                label={link.label}
                icon={link.icon}
                onClick={() => setMobileMenuOpen(false)}
              />
            ))}
            </div>
          )}
      </div>
    </nav>
  );
}
