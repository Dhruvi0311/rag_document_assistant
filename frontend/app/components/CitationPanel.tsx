"use client";

import { useState } from "react";
import { CitationChunk } from "../types";

interface CitationPanelProps {
  citations: CitationChunk[];
}

export default function CitationPanel({ citations }: CitationPanelProps) {
  const [expanded, setExpanded] = useState<number | null>(null);

  if (!citations || citations.length === 0) return null;

  return (
    <div className="mt-4 pt-4 border-t border-gray-200">
      {/* Section label */}
      <p className="font-mono text-label-sm uppercase tracking-widest text-gray-400 mb-3">
        Sources · {citations.length}
      </p>

      {/* Citation badges row */}
      <div className="flex flex-wrap gap-2">
        {citations.map((c, i) => (
          <div key={c.chunk_id} className="relative">
            <button
              onClick={() => setExpanded(expanded === i ? null : i)}
              className={`citation-badge ${expanded === i ? "citation-badge-active" : ""}`}
              aria-expanded={expanded === i}
              aria-controls={`citation-detail-${i}`}
            >
              {/* Score indicator bar */}
              <span className="inline-flex items-center gap-1.5">
                <span
                  className="inline-block h-[8px]"
                  style={{
                    width: `${Math.round(c.relevance_score * 24)}px`,
                    minWidth: 3,
                    maxWidth: 24,
                    backgroundColor: expanded === i ? "white" : "black",
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
          className="mt-3 border-2 border-black bg-gray-100 p-4 animate-fade-in-up"
        >
          {/* Header row */}
          <div className="flex items-center justify-between mb-3 pb-2 border-b border-gray-200">
            <div className="flex items-center gap-3">
              <span className="font-mono text-label-sm uppercase tracking-widest text-gray-600">
                {citations[expanded].file_name}
              </span>
              <span
                className="font-mono text-label-sm uppercase tracking-widest
                           text-gray-400 border border-gray-200 px-1.5 py-0.5"
              >
                Score {citations[expanded].relevance_score.toFixed(4)}
              </span>
            </div>
            <button
              onClick={() => setExpanded(null)}
              className="font-mono text-label-lg text-gray-400 hover:text-black
                         transition-colors duration-100"
              aria-label="Close citation detail"
            >
              ✕
            </button>
          </div>

          {/* Chunk ID */}
          <p className="font-mono text-label-sm uppercase tracking-widest text-gray-400 mb-2">
            {citations[expanded].chunk_id}
          </p>

          {/* Text excerpt */}
          <blockquote className="font-body text-body-sm text-gray-800 border-l-4 border-black pl-3 italic">
            {citations[expanded].text_preview}
            {citations[expanded].text_preview.length >= 160 && (
              <span className="not-italic text-gray-400"> …</span>
            )}
          </blockquote>
        </div>
      )}
    </div>
  );
}
