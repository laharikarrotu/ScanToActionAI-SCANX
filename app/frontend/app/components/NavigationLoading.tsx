'use client';

import { useEffect, useState } from 'react';
import { usePathname } from 'next/navigation';

/**
 * Navigation Loading Component
 * 
 * Shows a loading indicator at the top of the page when navigating between routes.
 * This provides visual feedback to users that navigation is happening.
 * 
 * How it works:
 * 1. Monitors pathname changes using usePathname hook
 * 2. Shows a progress bar at the top when route changes
 * 3. Automatically hides when new page loads
 */
export default function NavigationLoading() {
  const pathname = usePathname();
  const [isLoading, setIsLoading] = useState(false);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    // When pathname changes, start loading animation
    setIsLoading(true);
    setProgress(0);

    // Simulate progress (real navigation is usually very fast)
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 90) {
          clearInterval(interval);
          return 90; // Don't go to 100% until page fully loads
        }
        return prev + 10;
      });
    }, 50);

    // Complete loading after a short delay (page has loaded)
    const timeout = setTimeout(() => {
      setProgress(100);
      setTimeout(() => {
        setIsLoading(false);
        setProgress(0);
      }, 200); // Small delay to show completion
    }, 300);

    return () => {
      clearInterval(interval);
      clearTimeout(timeout);
    };
  }, [pathname]);

  if (!isLoading) return null;

  return (
    <div className="fixed top-0 left-0 right-0 z-[100] h-1 bg-slate-200">
      <div
        className="h-full bg-gradient-to-r from-blue-500 via-cyan-500 to-blue-600 transition-all duration-300 ease-out"
        style={{ width: `${progress}%` }}
      />
    </div>
  );
}

