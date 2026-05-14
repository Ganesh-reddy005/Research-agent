"use client";

import React from 'react';
import { BookOpen, Globe, Cpu } from 'lucide-react';

export default function ValueProp() {
  return (
    <section id="how-it-works" className="py-32 px-6 bg-white border-t border-mistral-black/5">
      <div className="max-w-7xl mx-auto text-center space-y-16">
        <div className="max-w-3xl mx-auto space-y-6">
          <h2 className="text-4xl md:text-5xl font-serif text-mistral-black tracking-tight leading-tight">
            Reduce months of literature review <br /> to <span className="italic font-light">less than 5 minutes.</span>
          </h2>
          <p className="text-lg text-mistral-black/50 leading-relaxed">
            Lume is designed for professors, scientists, and students who need 100% accuracy. We only use real papers and real-time data clusters.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-12 text-left">
           {[
             { 
               title: "Real Paper Access", 
               desc: "Lume scans 200M+ real manuscripts from ArXiv, OpenAlex, and PubMed. No hallucinations, only citations.",
               icon: <BookOpen className="w-6 h-6 text-mistral-orange" />
             },
             { 
               title: "Live Data Feed", 
               desc: "Stay updated with research published this morning. Our clusters index new data in real-time.",
               icon: <Globe className="w-6 h-6 text-mistral-orange" />
             },
             { 
               title: "Multi-Agent Logic", 
               desc: "Specialized agents for planning, critiquing, and writing. A complete end-to-end autonomous pipeline.",
               icon: <Cpu className="w-6 h-6 text-mistral-orange" />
             }
           ].map((item, i) => (
             <div key={i} className="space-y-6 p-8 rounded-[2rem] bg-mistral-beige/30 border border-mistral-black/5 transition-all hover:border-mistral-orange/20">
               <div className="w-12 h-12 rounded-2xl bg-white flex items-center justify-center shadow-sm">
                 {item.icon}
               </div>
               <div className="space-y-3">
                 <h3 className="text-2xl font-serif text-mistral-black tracking-tight">{item.title}</h3>
                 <p className="text-sm text-mistral-black/60 leading-relaxed font-sans">{item.desc}</p>
               </div>
             </div>
           ))}
        </div>
      </div>
    </section>
  );
}
