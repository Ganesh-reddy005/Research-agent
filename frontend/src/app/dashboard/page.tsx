"use client";

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Dashboard from '@/components/Dashboard';
import { useSupabaseUser } from '@/lib/useSupabaseUser';

export default function DashboardPage() {
  const { user, loading } = useSupabaseUser();
  const router = useRouter();

  // Every dashboard API call needs a session; send signed-out visitors to sign in
  useEffect(() => {
    if (!loading && !user) router.replace('/?signin=1');
  }, [loading, user, router]);

  if (!user) {
    return (
      <div className="h-screen flex items-center justify-center bg-mistral-beige text-sm text-mistral-black/60">
        {loading ? 'Loading your workspace…' : 'Redirecting to sign in…'}
      </div>
    );
  }
  return <Dashboard user={user} />;
}
