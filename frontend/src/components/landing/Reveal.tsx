"use client";

import React from 'react';
import { motion } from 'framer-motion';

/** Fades content up once as it scrolls into view. Renders a <div>, or an <li> inside lists. */
export default function Reveal({ children, delay = 0, className = '', as = 'div' }: {
  children: React.ReactNode;
  delay?: number;
  className?: string;
  as?: 'div' | 'li';
}) {
  const Tag = as === 'li' ? motion.li : motion.div;
  return (
    <Tag
      className={className}
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-80px' }}
      transition={{ delay, duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
    >
      {children}
    </Tag>
  );
}
