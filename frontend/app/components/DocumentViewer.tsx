"use client";

import { CitationChunk } from "../types";

interface DocumentViewerProps {
  citation: CitationChunk;
  onClose: () => void;
}

export default function DocumentViewer({ citation, onClose }: DocumentViewerProps) {
  // Extract file extension
  const ext = citation.file_name.split('.').pop()?.toLowerCase() || '';

  // Calculate search fragment for PDFs
  // We take the first 6-8 words to ensure a solid match without exceeding URL length limits
  const fullText = citation.full_text || citation.text_preview;
  const searchWords = fullText.split(/\s+/).slice(0, 8).join(" ");
  
  const pageParam = citation.page_number ? `page=${citation.page_number}&` : '';
  const searchHash = `#${pageParam}search=${encodeURIComponent(searchWords)}`;
  
  const fileUrl = `http://localhost:8000/api/documents/${encodeURIComponent(citation.file_name)}`;

  return (
    <div className="flex flex-col h-full bg-white animate-fade-in-up">
      {/* ── Header ────────────────────────────────────────────── */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-slate-200/80 bg-slate-50/50 flex-none">
        <div>
          <p className="font-sans text-[10px] font-bold uppercase tracking-wider text-blue-600 mb-0.5">
            Document Preview
          </p>
          <h2 className="font-sans text-sm font-bold text-slate-800">
            {citation.file_name}
          </h2>
        </div>
        <button
          onClick={onClose}
          className="p-2 rounded-full text-slate-400 hover:text-slate-700 hover:bg-slate-200/50 transition-all"
          aria-label="Close document viewer"
        >
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M1 1L13 13M13 1L1 13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </button>
      </div>

      {/* ── Viewer Body ────────────────────────────────────────── */}
      <div className="flex-1 relative bg-slate-100 overflow-hidden">
        {ext === 'pdf' ? (
          <iframe 
            src={`${fileUrl}${searchHash}`}
            className="w-full h-full border-none"
            title={`Document ${citation.file_name}`}
          />
        ) : (
          <div className="flex items-center justify-center h-full p-8 text-center flex-col gap-3">
             <div className="w-16 h-16 bg-white rounded-2xl shadow-sm flex items-center justify-center text-slate-300">
               <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                 <path d="M4 4v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6H6a2 2 0 00-2 2z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                 <path d="M14 2v6h6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
               </svg>
             </div>
             <div>
               <p className="font-sans text-xs font-bold text-slate-600">
                 Raw Text View Not Supported Yet
               </p>
               <p className="font-sans text-[10px] text-slate-400 mt-1 max-w-xs mx-auto">
                 The document split-screen is currently optimized for PDFs. For other formats, please refer to the highlighted text chunk in the chat.
               </p>
               <a 
                 href={fileUrl} 
                 target="_blank" 
                 rel="noreferrer"
                 className="inline-block mt-4 font-sans text-[10px] font-bold uppercase tracking-wider text-blue-600 bg-blue-50 border border-blue-100 px-4 py-2 rounded-full hover:bg-blue-100 transition-colors"
               >
                 Download {citation.file_name}
               </a>
             </div>
          </div>
        )}
      </div>
    </div>
  );
}
