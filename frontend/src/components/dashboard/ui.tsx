import React from 'react';
import { Loader2 } from 'lucide-react';

// Dashboard type scale: nothing below text-xs (12px); secondary text at least 60% black.

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'secondary' | 'ghost';
  loading?: boolean;
};

export function Button({ variant = 'primary', loading = false, className = '', children, disabled, ...rest }: ButtonProps) {
  const styles = {
    primary: 'bg-mistral-black text-white hover:bg-mistral-orange',
    secondary: 'bg-white text-mistral-black border border-mistral-black/15 hover:border-mistral-black/40',
    ghost: 'text-mistral-black/70 hover:text-mistral-black hover:bg-mistral-black/5',
  }[variant];
  return (
    <button
      {...rest}
      disabled={disabled || loading}
      className={`inline-flex items-center justify-center gap-2 px-5 py-2.5 text-sm font-semibold transition-colors disabled:opacity-40 disabled:cursor-not-allowed focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-mistral-orange ${styles} ${className}`}
    >
      {loading && <Loader2 className="w-4 h-4 animate-spin" aria-hidden />}
      {children}
    </button>
  );
}

export function StageHeader({ title, description, children }: {
  title: React.ReactNode;
  description?: React.ReactNode;
  children?: React.ReactNode;
}) {
  return (
    <header className="space-y-3 pb-8 border-b border-mistral-black/10">
      <h1 className="font-serif text-3xl sm:text-4xl text-mistral-black tracking-tight leading-tight">{title}</h1>
      {description && <p className="text-base text-mistral-black/65 leading-relaxed max-w-2xl">{description}</p>}
      {children}
    </header>
  );
}

export function SectionLabel({ children }: { children: React.ReactNode }) {
  return <h2 className="text-sm font-semibold text-mistral-black/70">{children}</h2>;
}

export const inputClass =
  'w-full bg-white border border-mistral-black/15 px-4 py-3 text-base text-mistral-black placeholder:text-mistral-black/40 focus:outline-none focus:border-mistral-orange focus:ring-2 focus:ring-mistral-orange/15 transition-colors';
