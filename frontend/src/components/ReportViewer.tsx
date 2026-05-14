import React from 'react';
import ReactMarkdown from 'react-markdown';
import { Download } from 'lucide-react';
import SourceCard from './SourceCard';

interface ReportViewerProps {
  report: string;
  sources: any[];
}

export default function ReportViewer({ report, sources }: ReportViewerProps) {
  const handleDownload = async () => {
    const element = document.getElementById('report-content');
    if (!element) return;

    // Use a high-quality capture strategy
    const opt = {
      margin:       [0.5, 0.5, 0.5, 0.5],
      filename:     'Research_Report.pdf',
      image:        { type: 'jpeg', quality: 0.98 },
      html2canvas:  { 
        scale: 2, 
        useCORS: true,
        letterRendering: true,
        backgroundColor: '#ffffff'
      },
      jsPDF:        { unit: 'in', format: 'letter', orientation: 'portrait' }
    };

    // Temporarily apply light mode classes and remove glass styles for the PDF capture
    const originalClassName = element.className;
    const parentNode = element.parentElement;
    const originalParentStyle = parentNode ? parentNode.style.cssText : '';
    
    if (parentNode) {
      parentNode.style.background = '#ffffff';
      parentNode.style.color = '#000000';
    }
    element.className = 'prose prose-slate max-w-none p-10 font-sans';

    try {
      const html2pdfModule = await import('html2pdf.js');
      const html2pdf = html2pdfModule.default || html2pdfModule;
      await html2pdf().set(opt).from(element).save();
    } catch (err) {
      console.error("PDF download failed:", err);
    } finally {
      // Restore original styles
      element.className = originalClassName;
      if (parentNode) {
        parentNode.style.cssText = originalParentStyle;
      }
    }
  };

  return (
    <div className="w-full max-w-5xl mx-auto mt-16 animate-in fade-in slide-in-from-bottom-8 duration-1000 px-6">
      <div className="flex justify-end mb-8">
        <button 
          onClick={handleDownload}
          className="flex items-center gap-3 px-10 py-3.5 bg-mistral-black hover:bg-mistral-orange text-white rounded-xl shadow-sm transition-all active:scale-95 group font-sans font-bold text-xs uppercase tracking-[0.2em]"
        >
          <Download className="w-5 h-5 group-hover:scale-110 transition-transform text-mistral-orange/80" />
          Generate PDF
        </button>
      </div>
      
      <div className="bg-white border border-mistral-border/50 p-12 md:p-24 shadow-xl rounded-[3rem] relative overflow-hidden transition-all">
        <div id="report-content" className="prose prose-stone prose-lg max-w-none selection:bg-mistral-orange/10 font-sans">
          <ReactMarkdown 
            components={{
              h2: ({node, ...props}) => <h2 className="text-4xl text-mistral-black mt-20 mb-10 border-b border-mistral-border/50 pb-8 font-sans font-bold tracking-tight" {...props} />,
              h3: ({node, ...props}) => <h3 className="text-2xl text-mistral-black mt-12 mb-8 font-sans font-bold tracking-tight" {...props} />,
              p: ({node, ...props}) => <p className="text-mistral-black/80 leading-relaxed mb-10 text-xl font-medium" {...props} />,
            }}
          >
            {report}
          </ReactMarkdown>
        </div>
      </div>

      {sources && sources.length > 0 && (
        <div className="mt-24 space-y-12">
          <h3 className="text-4xl font-sans font-bold tracking-tight text-mistral-black flex items-center gap-6">
            <span className="bg-mistral-orange/10 border border-mistral-orange/20 px-6 py-2.5 text-[10px] font-bold text-mistral-orange rounded-full tracking-[0.2em] uppercase">References</span>
            Retrieved Sources
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {sources.map((source, idx) => (
              <SourceCard key={idx} index={idx} source={source} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
