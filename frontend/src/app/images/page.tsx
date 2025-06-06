'use client';

import TimeLapse from '@/components/TimeLapse';
import Navigation from '@/components/Navigation';

export default function ImagesPage() {
  return (
    <main className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <header className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900">SelfHydro Tomato Monitor</h1>
          <p className="text-gray-600">Track your plant&apos;s growth and environmental conditions</p>
        </header>

        <Navigation />
        
        <div className="rounded-xl bg-white p-3">
          <TimeLapse />
        </div>
      </div>
    </main>
  );
} 