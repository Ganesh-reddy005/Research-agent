"use client";

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Loader2, Sparkles, Mail } from 'lucide-react';
import { supabase } from '@/lib/supabaseClient';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function AuthModal({ isOpen, onClose }: AuthModalProps) {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleMagicLink = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const { error } = await supabase.auth.signInWithOtp({
        email,
        options: {
          emailRedirectTo: window.location.origin + '/dashboard',
        },
      });
      if (error) throw error;
      setSent(true);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleOAuth = async () => {
    try {
      await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: window.location.origin + '/dashboard',
        },
      });
    } catch (err: any) {
      setError(err.message);
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="absolute inset-0 bg-mistral-black/20 backdrop-blur-sm"
          />
          <motion.div 
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 10 }}
            className="relative w-full max-w-md bg-white border border-mistral-black/10 shadow-xl overflow-hidden flex flex-col"
          >
            <div className="flex justify-between items-center p-6 border-b border-mistral-black/5 bg-mistral-beige/30">
              <div className="flex items-center gap-3 text-mistral-black font-mono text-lg font-black uppercase tracking-tighter">
                <img src="/logo.png" alt="Lume Logo" className="w-6 h-6 object-contain" />
                <span>Lume.ai</span>
              </div>
              <button onClick={onClose} className="text-mistral-black/40 hover:text-mistral-black transition-colors">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-8 space-y-8">
              <div className="space-y-2 text-center">
                <h2 className="text-2xl font-serif text-mistral-black font-bold tracking-tight">Access the Engine</h2>
                <p className="text-sm font-sans text-mistral-black/50">Sign in to start autonomous synthesis.</p>
              </div>

              {sent ? (
                <div className="p-6 bg-[#F5F2ED] border border-mistral-orange/20 text-center space-y-4">
                  <Mail className="w-8 h-8 text-mistral-orange mx-auto" />
                  <div>
                    <div className="font-bold text-mistral-black text-sm uppercase tracking-widest font-mono mb-1">Check your inbox</div>
                    <div className="text-sm text-mistral-black/60 font-sans">We sent a secure magic link to <b>{email}</b>.</div>
                  </div>
                </div>
              ) : (
                <>
                  <div className="space-y-4">
                    <button 
                      onClick={handleOAuth}
                      className="w-full flex items-center justify-center gap-3 py-3.5 border border-mistral-black/10 bg-white hover:bg-[#F5F2ED] transition-all text-sm font-bold font-sans text-mistral-black shadow-sm"
                    >
                      <img src="https://www.svgrepo.com/show/475656/google-color.svg" alt="Google" className="w-5 h-5" />
                      Continue with Google
                    </button>
                  </div>

                  <div className="flex items-center gap-4 py-2">
                    <div className="flex-1 h-px bg-mistral-black/5" />
                    <div className="text-[9px] font-bold font-mono text-mistral-black/30 uppercase tracking-widest">Or secure email</div>
                    <div className="flex-1 h-px bg-mistral-black/5" />
                  </div>

                  <form onSubmit={handleMagicLink} className="space-y-4">
                    <div className="space-y-2">
                      <label className="text-[10px] font-bold font-mono text-mistral-black/50 uppercase tracking-widest">Email Address</label>
                      <input 
                        type="email" 
                        required
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="academic@university.edu"
                        className="w-full px-4 py-3 border border-mistral-black/10 bg-white font-sans text-mistral-black placeholder:text-mistral-black/20 focus:outline-none focus:border-mistral-orange/30 transition-all"
                      />
                    </div>
                    {error && <div className="text-xs text-red-500 font-sans">{error}</div>}
                    <button 
                      type="submit" 
                      disabled={loading}
                      className="w-full py-3 bg-mistral-black text-white font-bold font-sans text-sm hover:bg-mistral-orange transition-all flex justify-center items-center"
                    >
                      {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Receive Magic Link"}
                    </button>
                  </form>
                </>
              )}
            </div>
            <div className="p-4 border-t border-mistral-black/5 bg-mistral-beige/30 text-center">
              <span className="text-[9px] font-mono text-mistral-black/40 uppercase tracking-widest">
                Protected by the Lume Integrity Protocol.
              </span>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
