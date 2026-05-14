import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { supabase } from '@/lib/supabaseClient';

export default function CTA() {
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? null);
    });
  }, []);

  return (
    <section className="py-48 px-6 text-center">
      <div className="max-w-4xl mx-auto space-y-12">
        <h2 className="text-5xl md:text-7xl font-serif text-mistral-black tracking-tight leading-tight">
          Stand on the <br /> <span className="italic font-light">shoulders of giants.</span>
        </h2>
        <div className="flex justify-center">
          <Link 
            href="/dashboard" 
            className="bg-mistral-black text-white text-xl py-5 px-16 rounded-xl hover:bg-mistral-orange transition-all font-bold shadow-xl shadow-black/10"
          >
            {user ? 'Go to Dashboard' : 'Try Lume Now'}
          </Link>
        </div>
      </div>
    </section>
  );
}
