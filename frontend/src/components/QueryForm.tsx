import React, { useState } from 'react';
import { Search, Loader2 } from 'lucide-react';
import { motion } from 'framer-motion';

interface QueryFormProps {
  onSubmit: (query: string) => void;
  isLoading: boolean;
}

export default function QueryForm({ onSubmit, isLoading }: QueryFormProps) {
  const [query, setQuery] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      onSubmit(query.trim());
    }
  };

  return (
    <motion.form 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full max-w-3xl mx-auto px-4"
      onSubmit={handleSubmit}
    >
      <div className="relative flex items-center group">
        <Search className="absolute left-8 w-6 h-6 text-mistral-black/20 group-focus-within:text-mistral-orange transition-colors z-10" />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Describe your research topic..."
          className="w-full pl-20 pr-44 py-7 bg-white border border-mistral-border/50 rounded-2xl focus:ring-4 focus:ring-mistral-orange/5 focus:border-mistral-orange/30 focus:outline-none text-lg transition-all shadow-md font-sans font-medium text-mistral-black placeholder:text-mistral-black/20"
          disabled={isLoading}
        />
        <button
          type="submit"
          disabled={!query.trim() || isLoading}
          className="absolute right-4 px-10 py-3.5 bg-mistral-black hover:bg-mistral-orange disabled:bg-mistral-beige disabled:text-mistral-black/20 text-white font-sans font-bold text-xs uppercase tracking-[0.2em] rounded-xl transition-all shadow-sm flex items-center gap-2 active:scale-95"
        >
          {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : (
            <>
              Start Run
              <Search className="w-4 h-4" />
            </>
          )}
        </button>
      </div>
    </motion.form>
  );
}
