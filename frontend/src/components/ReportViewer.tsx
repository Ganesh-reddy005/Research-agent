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
    element.className = 'prose prose-slate max-w-none p-4';

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
    <div className="w-full max-w-4xl mx-auto mt-12 animate-in fade-in slide-in-from-bottom-8 duration-700">
      <div className="flex justify-end mb-4">
        <button 
          onClick={handleDownload}
          className="flex items-center gap-2 px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg transition-colors shadow-lg group"
        >
          <Download className="w-4 h-4 group-hover:scale-110 transition-transform" />
          Download PDF
        </button>
      </div>
      
      <div className="glass rounded-2xl p-8 md:p-12 shadow-2xl relative overflow-hidden transition-all hover:border-cyan-500/20">
        <div className="absolute top-0 right-0 w-64 h-64 bg-cyan-500/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2 pointer-events-none" />
        
        <div id="report-content" className="prose prose-invert prose-cyan max-w-none selection:bg-cyan-500/30">
          <ReactMarkdown>{report}</ReactMarkdown>
        </div>
      </div>

      {sources && sources.length > 0 && (
        <div className="mt-12">
          <h3 className="text-xl font-semibold mb-6 flex items-center text-cyan-400">
            <span className="bg-cyan-500/20 px-3 py-1 rounded-md mr-3 text-sm">References</span>
            Retrieved Sources
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {sources.map((source, idx) => (
              <SourceCard key={idx} index={idx} source={source} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
