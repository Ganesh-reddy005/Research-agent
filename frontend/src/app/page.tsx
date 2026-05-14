"use client";

import React from 'react';
import Navbar from '@/components/landing/Navbar';
import Hero from '@/components/landing/Hero';
import ValueProp from '@/components/landing/ValueProp';
import Features from '@/components/landing/Features';
import CTA from '@/components/landing/CTA';
import Footer from '@/components/landing/Footer';

export default function LandingPage(props: PageProps) {
  return (
    <div className="retro-theme">
      <div className="bg-mistral-beige min-h-screen relative overflow-hidden font-sans selection:bg-mistral-orange selection:text-white">
        <Navbar />
        <Hero />
        <ValueProp />
        <Features />
        <CTA />
        <Footer />
      </div>
    </div>
  );
}
