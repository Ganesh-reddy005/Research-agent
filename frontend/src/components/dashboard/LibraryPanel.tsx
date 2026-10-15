"use client";

import React, { useEffect, useState } from 'react';
import { Upload, FileText, Loader2, X, AlertCircle } from 'lucide-react';
import { uploadDocument, getLibrary } from '@/lib/api';
import type { LibraryDocument } from '@/lib/types';

export default function LibraryPanel({ onClose }: { onClose: () => void }) {
  const [library, setLibrary] = useState<LibraryDocument[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchLibrary = async () => {
    try {
      setLibrary(await getLibrary());
    } catch {
      setError('Could not load your library. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchLibrary();
  }, []);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (!file) return;

    setIsUploading(true);
    setError(null);
    try {
      await uploadDocument(file);
      await fetchLibrary();
    } catch (err) {
      setError(`Upload failed: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <aside className="h-full bg-white border-l border-mistral-black/10 flex flex-col" aria-label="My library">
      <div className="h-14 px-5 flex items-center justify-between border-b border-mistral-black/10 shrink-0">
        <div>
          <h2 className="text-base font-semibold text-mistral-black">My library</h2>
          <p className="text-xs text-mistral-black/60">Your PDFs, searched in every project</p>
        </div>
        <button onClick={onClose} className="p-2 text-mistral-black/60 hover:text-mistral-black" aria-label="Close library">
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="p-5 border-b border-mistral-black/10 space-y-3">
        <label className={`flex flex-col items-center justify-center gap-2 w-full h-32 border-2 border-dashed transition-colors ${
          isUploading ? 'border-mistral-orange/40 bg-mistral-beige/30' : 'border-mistral-black/15 hover:border-mistral-orange hover:bg-mistral-beige/30 cursor-pointer'
        }`}>
          {isUploading
            ? <Loader2 className="w-6 h-6 text-mistral-orange animate-spin" aria-hidden />
            : <Upload className="w-6 h-6 text-mistral-black/50" aria-hidden />}
          <span className="text-sm font-medium text-mistral-black">
            {isUploading ? 'Reading and indexing your PDF…' : 'Upload a PDF'}
          </span>
          {!isUploading && <span className="text-xs text-mistral-black/60">Papers, notes, drafts</span>}
          <input type="file" className="sr-only" accept=".pdf,application/pdf" onChange={handleFileUpload} disabled={isUploading} />
        </label>
        {error && (
          <p role="alert" className="flex gap-2 text-sm text-red-700">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" aria-hidden /> {error}
          </p>
        )}
      </div>

      <div className="flex-1 overflow-y-auto custom-scrollbar p-5">
        {isLoading ? (
          <p className="text-sm text-mistral-black/60">Loading…</p>
        ) : library.length === 0 ? (
          <p className="text-sm text-mistral-black/60 leading-relaxed">
            No documents yet. Upload papers you already rely on and Lume will search them alongside public sources.
          </p>
        ) : (
          <ul className="space-y-2">
            {library.map(doc => (
              <li key={doc.id} className="flex items-start gap-3 p-3 border border-mistral-black/10">
                <FileText className="w-4 h-4 mt-0.5 text-mistral-black/50 shrink-0" aria-hidden />
                <span className="min-w-0">
                  <span className="block text-sm font-medium text-mistral-black truncate" title={doc.filename}>{doc.filename}</span>
                  <span className="block text-xs text-mistral-black/60">
                    Added {new Date(doc.uploaded_at).toLocaleDateString()} · Ready
                  </span>
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>

      <p className="p-4 border-t border-mistral-black/10 bg-mistral-beige/50 text-xs text-mistral-black/70 leading-relaxed">
        Lume keeps the text of your PDFs in a private index only your account can search. To index them, the text is
        sent to the AI providers that power Lume.
      </p>
    </aside>
  );
}
