import React from 'react';
import { FileSearch, Layers, Search, Database, Cpu, Book, CheckCircle, Sparkles, ShieldCheck, Activity } from 'lucide-react';

interface AgentIconProps {
  name: string;
  className?: string;
}

export const AgentIcon = ({ name, className = "w-4 h-4" }: AgentIconProps) => {
  switch (name.toLowerCase()) {
    case 'clarification': return <FileSearch className={className} />;
    case 'planning': return <Layers className={className} />;
    case 'retriever': return <Search className={className} />;
    case 'indexer': return <Database className={className} />;
    case 'synthesis': return <Cpu className={className} />;
    case 'writer': return <Book className={className} />;
    case 'critic': return <CheckCircle className={className} />;
    case 'refinement': return <Sparkles className={className} />;
    case 'auditor': return <ShieldCheck className={className} />;
    default: return <Activity className={className} />;
  }
};

export default AgentIcon;
