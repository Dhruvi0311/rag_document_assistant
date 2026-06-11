"use client";

import { useState } from "react";
import { CitationChunk } from "../types";

interface CitationPanelProps {
  citations: CitationChunk[];
  onCitationClick?: (citation: CitationChunk) => void;
}

export default function CitationPanel({ citations, onCitationClick }: CitationPanelProps) {
  const [expanded, setExpanded] = useState<number | null>(null);

  if (!citations || citations.length === 0) return null;

  return (
    <div className="mt-4 pt-4 border-t border-slate-100 dark:border-slate-800/50 transition-colors">
      {/* Section label */}
      <p className="font-sans text-[10px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500 mb-3">
        Sources · {citations.length}
      </p>

      {/* Citation badges row */}
      <div className="flex flex-wrap gap-2">
        {citations.map((c, i) => (
          <div key={c.chunk_id} className="relative">
            <button
              onClick={() => {
                setExpanded(expanded === i ? null : i);
                if (onCitationClick) onCitationClick(c);
              }}
              className={`citation-badge ${expanded === i ? "citation-badge-active" : ""}`}
              aria-expanded={expanded === i}
              aria-controls={`citation-detail-${i}`}
            >
              {/* Score indicator bar */}
              <span className="inline-flex items-center gap-1.5">
                <span
                  className="inline-block h-[6px] rounded-full"
                  style={{
                    width: `${Math.round(c.relevance_score * 24)}px`,
                    minWidth: 3,
                    maxWidth: 24,
                    backgroundColor: expanded === i ? "white" : "#3B82F6",
                  }}
                />
                <span>{c.file_name}</span>
              </span>
            </button>
          </div>
        ))}
      </div>

      {/* Expanded citation detail panel */}
      {expanded !== null && citations[expanded] && (
        <div
          id={`citation-detail-${expanded}`}
          className="mt-3 border border-slate-200/60 dark:border-slate-700/60 bg-slate-50/50 dark:bg-slate-800/80 p-4 rounded-2xl shadow-sm backdrop-blur-sm animate-fade-in-up transition-colors"
        >
          {/* Header row */}
          <div className="flex items-center justify-between mb-3 pb-2.5 border-b border-slate-200/50 dark:border-slate-700/50 transition-colors">
            <div className="flex items-center gap-3">
              <span className="font-sans text-xs font-semibold text-slate-700 dark:text-slate-200">
                {citations[expanded].file_name}
              </span>
              <span
                className="font-sans text-[9px] font-bold uppercase tracking-wider
                           text-blue-600 bg-blue-50/80 border border-blue-100 px-2 py-0.5 rounded-md"
              >
                Score {citations[expanded].relevance_score.toFixed(4)}
              </span>
            </div>
            <button
              onClick={() => setExpanded(null)}
              className="font-sans text-xs text-slate-400 hover:text-slate-700 hover:bg-slate-100/50 w-5 h-5 flex items-center justify-center rounded-full transition-all"
              aria-label="Close citation detail"
            >
              ✕
            </button>
          </div>

          {/* Chunk ID */}
          <p className="font-sans text-[9px] font-bold uppercase tracking-wider text-slate-400 mb-2.5">
            {citations[expanded].chunk_id}
          </p>

          {/* Text excerpt */}
          <blockquote className="font-body text-body-sm text-slate-600 dark:text-slate-300 border-l-2 border-blue-400 pl-3 italic transition-colors">
            {citations[expanded].text_preview}
            {citations[expanded].text_preview.length >= 160 && (
              <span className="not-italic text-slate-400 dark:text-slate-500"> …</span>
            )}
          </blockquote>
        </div>
      )}
    </div>
  );
}
