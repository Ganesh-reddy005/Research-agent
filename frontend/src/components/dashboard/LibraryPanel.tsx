"use client";

import React, { useState, useEffect } from 'react';
import { Upload, File, Loader2, X, CheckCircle } from 'lucide-react';
import { uploadDocument, getLibrary } from '@/lib/api';

interface LibraryPanelProps {
  onClose: () => void;
}

export default function LibraryPanel({ onClose }: LibraryPanelProps) {
  const [library, setLibrary] = useState<any[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchLibrary();
  }, []);

  const fetchLibrary = async () => {
    try {
      const docs = await getLibrary();
      setLibrary(docs);
    } catch (err) {
      console.error("Failed to fetch library", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    try {
      await uploadDocument(file);
      await fetchLibrary();
    } catch (err) {
      alert("Upload failed: " + (err as Error).message);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="h-full bg-white border-l border-mistral-black/5 flex flex-col font-sans">
      <div className="p-6 border-b border-mistral-black/5 flex items-center justify-between">
        <div>
          <h2 className="text-xs font-bold uppercase tracking-widest text-mistral-black">Private Library</h2>
          <p className="text-[10px] text-mistral-black/40 mt-1">Sovereign research corpus</p>
        </div>
        <button onClick={onClose} className="p-1 hover:text-mistral-orange transition-colors">
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="p-6 border-b border-mistral-black/5">
        <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed border-mistral-black/5 hover:border-mistral-orange/20 hover:bg-mistral-orange/5 transition-all cursor-pointer group">
          <div className="flex flex-col items-center justify-center pt-5 pb-6">
            {isUploading ? (
              <Loader2 className="w-6 h-6 text-mistral-orange animate-spin" />
            ) : (
              <Upload className="w-6 h-6 text-mistral-black/20 group-hover:text-mistral-orange transition-colors" />
            )}
            <p className="mt-2 text-[10px] font-bold uppercase tracking-widest text-mistral-black/40 group-hover:text-mistral-black transition-colors">
              {isUploading ? 'Ingesting PDF...' : 'Upload Scholar PDF'}
            </p>
          </div>
          <input 
            type="file" 
            className="hidden" 
            accept=".pdf" 
            onChange={handleFileUpload} 
            disabled={isUploading}
          />
        </label>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-3 custom-scrollbar">
        {isLoading ? (
          <div className="flex justify-center py-10">
            <Loader2 className="w-5 h-5 animate-spin text-mistral-black/10" />
          </div>
        ) : library.length === 0 ? (
          <div className="text-center py-10">
            <File className="w-8 h-8 mx-auto text-mistral-black/5 mb-3" />
            <p className="text-[10px] font-medium text-mistral-black/30 italic">No documents in your library yet.</p>
          </div>
        ) : (
          library.map((doc) => (
            <div key={doc.id} className="p-3 border border-mistral-black/5 hover:border-mistral-orange/20 hover:shadow-sm transition-all group relative">
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 bg-[#F5F2ED] flex items-center justify-center text-mistral-black/20 group-hover:bg-mistral-orange/10 group-hover:text-mistral-orange transition-colors">
                  <File className="w-4 h-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-[10px] font-bold text-mistral-black truncate pr-4">{doc.filename}</div>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-[8px] font-mono text-mistral-black/30 uppercase tracking-tighter">
                      {new Date(doc.uploaded_at).toLocaleDateString()}
                    </span>
                    <div className="flex items-center gap-1">
                       <CheckCircle className="w-2.5 h-2.5 text-green-500" />
                       <span className="text-[8px] font-bold text-green-600 uppercase tracking-widest">Indexed</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      <div className="p-4 bg-[#F5F2ED] border-t border-mistral-black/5 text-[9px] text-mistral-black/40 italic leading-relaxed">
        Uploads are encrypted and stored in your sovereign vault. They are automatically included in all research synthesis.
      </div>
    </div>
  );
}
