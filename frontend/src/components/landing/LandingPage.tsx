"use client";

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { MotionConfig } from 'framer-motion';
import { useSupabaseUser } from '@/lib/useSupabaseUser';
import Navbar from './Navbar';
import Hero from './Hero';
import Problem from './Problem';
import HowItWorks from './HowItWorks';
import Experiments from './Experiments';
import Verification from './Verification';
import FAQ from './FAQ';
import CTA from './CTA';
import Footer from './Footer';
import AuthModal from './AuthModal';

export default function LandingPage({ className = '' }: { className?: string }) {
  const { user } = useSupabaseUser();
  const router = useRouter();
  const [isAuthOpen, setIsAuthOpen] = useState(false);

  // The dashboard sends signed-out visitors here with ?signin=1
  useEffect(() => {
    if (new URLSearchParams(window.location.search).get('signin') === '1') setIsAuthOpen(true);
  }, []);

  // Signed-out visitors sign in first; the dashboard's API calls need a session.
  const start = () => (user ? router.push('/dashboard') : setIsAuthOpen(true));

  return (
    <MotionConfig reducedMotion="user">
      <div className={`retro-theme ${className}`}>
        <div className="bg-mistral-beige min-h-screen relative overflow-x-hidden font-sans selection:bg-mistral-orange selection:text-white">
          <Navbar user={user} onSignIn={() => setIsAuthOpen(true)} />
          <main>
            <Hero signedIn={!!user} onStart={start} />
            <Problem />
            <HowItWorks />
            <Experiments />
            <Verification />
            <FAQ />
            <CTA signedIn={!!user} onStart={start} />
          </main>
          <Footer />
        </div>
        <AuthModal isOpen={isAuthOpen} onClose={() => setIsAuthOpen(false)} />
      </div>
    </MotionConfig>
  );
}
