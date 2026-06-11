"use client";

import { useRef, useState, useCallback, DragEvent, ChangeEvent } from "react";
import { UploadResult } from "../types";

interface SidebarProps {
  indexedFiles: string[];
  isLoading: boolean;
  onFilesUploaded: () => void;
  onDeleteFile: (name: string) => void;
}

const ACCEPTED_MIME_TYPES = [
  "application/pdf",
  "text/plain",
  "text/csv",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "image/png",
  "image/jpeg",
];

const ACCEPTED_EXTENSIONS = ".pdf,.txt,.csv,.docx,.png,.jpg,.jpeg";

// Derive a one-word type label from a file name
function getFileTypeLabel(name: string): string {
  const ext = name.split(".").pop()?.toLowerCase() ?? "";
  const map: Record<string, string> = {
    pdf: "PDF",
    txt: "TXT",
    csv: "CSV",
    docx: "DOCX",
    png: "IMG",
    jpg: "IMG",
    jpeg: "IMG",
  };
  return map[ext] ?? ext.toUpperCase();
}

export default function Sidebar({
  indexedFiles,
  isLoading,
  onFilesUploaded,
  onDeleteFile,
}: SidebarProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [deletingFile, setDeletingFile] = useState<string | null>(null);

  const uploadFiles = useCallback(async (files: FileList | File[]) => {
    const fileArray = Array.from(files);
    if (fileArray.length === 0) return;

    setIsUploading(true);
    setUploadResult(null);
    setUploadError(null);

    const form = new FormData();
    fileArray.forEach((f) => form.append("files", f));

    try {
      const res = await fetch("http://localhost:8000/api/upload", {
        method: "POST",
        body: form,
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail ?? `Server error ${res.status}`);
      }

      const data: UploadResult = await res.json();
      setUploadResult(data);
      onFilesUploaded();
    } catch (err: unknown) {
      setUploadError(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      setIsUploading(false);
    }
  }, [onFilesUploaded]);

  // ── Drag & Drop handlers ──────────────────────────────────────────────
  function handleDragOver(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setIsDragging(true);
  }

  function handleDragLeave(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setIsDragging(false);
  }

  function handleDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files?.length) {
      uploadFiles(e.dataTransfer.files);
    }
  }

  function handleFileInputChange(e: ChangeEvent<HTMLInputElement>) {
    if (e.target.files?.length) {
      uploadFiles(e.target.files);
      // Reset input so the same file can be re-uploaded
      e.target.value = "";
    }
  }

  async function handleDelete(name: string) {
    setDeletingFile(name);
    await onDeleteFile(name);
    setDeletingFile(null);
  }

  return (
    <div className="flex flex-col h-full bg-white/10 dark:bg-slate-900/10 backdrop-blur-md transition-colors">

      {/* ── Section header ────────────────────────────────────────────── */}
      <div className="px-5 py-4 border-b border-slate-200/80 dark:border-slate-800/80 bg-white/40 dark:bg-slate-900/40 transition-colors">
        <p className="font-sans text-[11px] font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
          Document Index
        </p>
      </div>

      {/* ── Drag-and-drop upload zone ──────────────────────────────────── */}
      <div
        role="button"
        tabIndex={0}
        aria-label="Upload files by clicking or dragging"
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        onKeyDown={(e) => e.key === "Enter" && fileInputRef.current?.click()}
        className={`
          relative mx-4 my-4 p-6 border-2 border-dashed cursor-pointer rounded-2xl
          flex flex-col items-center justify-center gap-3
          transition-all duration-150 select-none
          ${isDragging
            ? "bg-blue-50 dark:bg-blue-900/30 border-blue-400 dark:border-blue-500 text-blue-800 dark:text-blue-300"
            : "bg-blue-50/15 dark:bg-blue-900/10 text-slate-700 dark:text-slate-300 border-blue-200/50 dark:border-blue-800/50 hover:bg-blue-50/30 dark:hover:bg-blue-900/20 hover:border-blue-300 dark:hover:border-blue-700"
          }
          ${isUploading ? "pointer-events-none opacity-60" : ""}
        `}
        style={{ minHeight: 140 }}
      >
        {/* Soft inset frame line */}
        <div
          className={`
            absolute inset-[6px] border pointer-events-none rounded-xl transition-colors
            ${isDragging ? "border-blue-300/40 dark:border-blue-500/40" : "border-slate-200/20 dark:border-slate-700/20"}
          `}
          style={{ borderStyle: "solid" }}
        />

        {isUploading ? (
          <>
            <UploadSpinner inverted={isDragging} />
            <p className="font-sans text-xs font-bold uppercase tracking-wider z-10 text-blue-600">
              Indexing…
            </p>
          </>
        ) : (
          <>
            <UploadIcon inverted={isDragging} />
            <div className="text-center z-10">
              <p className="font-sans text-xs font-bold uppercase tracking-wider">
                {isDragging ? "Release to index" : "Drop files here"}
              </p>
              <p className="font-sans text-[9px] font-semibold uppercase tracking-wider text-slate-400 mt-1.5">
                PDF · CSV · TXT · DOCX · IMG
              </p>
            </div>
          </>
        )}

        <input
          ref={fileInputRef}
          type="file"
          accept={ACCEPTED_EXTENSIONS}
          multiple
          className="sr-only"
          onChange={handleFileInputChange}
          tabIndex={-1}
        />
      </div>

      {/* ── Upload feedback ─────────────────────────────────────────────── */}
      {uploadResult && (
        <div className="mx-4 mb-4 border border-emerald-100 bg-emerald-50/50 text-emerald-800 p-4 rounded-2xl animate-fade-in-up shadow-sm">
          <p className="font-sans text-[10px] font-bold uppercase tracking-wider text-emerald-600 mb-1.5">
            Success
          </p>
          <p className="font-sans text-xs font-semibold">
            {uploadResult.total_chunks} chunks · {uploadResult.indexed_files.length} file
            {uploadResult.indexed_files.length !== 1 ? "s" : ""}
          </p>
          {uploadResult.rejected_files.length > 0 && (
            <p className="font-sans text-[9px] tracking-wide text-emerald-600 mt-1">
              Skipped: {uploadResult.rejected_files.join(", ")}
            </p>
          )}
        </div>
      )}

      {uploadError && (
        <div className="mx-4 mb-4 border border-rose-100 bg-rose-50/50 text-rose-800 p-4 rounded-2xl animate-fade-in-up shadow-sm">
          <p className="font-sans text-[10px] font-bold uppercase tracking-wider text-rose-600 mb-1.5">Error</p>
          <p className="font-sans text-xs text-rose-700">{uploadError}</p>
        </div>
      )}

      {/* ── Active Index list ──────────────────────────────────────────── */}
      <div className="border-t border-slate-200/80 dark:border-slate-800/80 flex-1 overflow-y-auto bg-slate-50/10 dark:bg-slate-900/50 transition-colors">
        <div className="px-5 py-3 border-b border-slate-100 dark:border-slate-800/50 transition-colors">
          <p className="font-sans text-[10px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">
            Active Index ({indexedFiles.length})
          </p>
        </div>

        {isLoading ? (
          <div className="p-4 space-y-3">
            {[1, 2, 3].map((n) => (
              <div key={n} className="skeleton h-12 w-full" />
            ))}
          </div>
        ) : indexedFiles.length === 0 ? (
          <div className="px-5 py-8 text-center">
            <p className="font-sans text-xs font-bold uppercase tracking-wider text-slate-400">
              No documents indexed
            </p>
            <p className="font-sans text-xs text-slate-400 mt-1.5">
              Upload files above to begin.
            </p>
          </div>
        ) : (
          <ul className="flex flex-col gap-1.5 px-4 py-3">
            {indexedFiles.map((name) => (
              <li
                key={name}
                className="group flex items-center justify-between
                           px-4 py-3 bg-white/80 dark:bg-slate-800/80 border border-slate-100/50 dark:border-slate-700/50 rounded-2xl shadow-sm
                           hover:bg-white dark:hover:bg-slate-800 hover:border-blue-100/50 dark:hover:border-blue-900/50 hover:shadow transition-all duration-150"
              >
                <div className="flex items-center gap-3 min-w-0 flex-1">
                  {/* Type badge */}
                  <span
                    className="flex-none font-sans text-[9px] font-bold uppercase tracking-wider
                               px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-700/50 text-slate-600 dark:text-slate-400 border border-slate-200/20 dark:border-slate-600/20"
                  >
                    {getFileTypeLabel(name)}
                  </span>
                  {/* File name */}
                  <span className="font-sans text-xs font-semibold text-slate-700 dark:text-slate-300 truncate">
                    {name}
                  </span>
                </div>

                {/* Delete button */}
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDelete(name);
                  }}
                  disabled={deletingFile === name}
                  className="flex-none ml-2 opacity-0 group-hover:opacity-100
                             transition-opacity duration-150 p-1.5 rounded-lg
                             text-slate-400 hover:text-rose-500 hover:bg-rose-50/50 focus-visible:opacity-100"
                  aria-label={`Remove ${name} from index`}
                  title="Remove from index"
                >
                  {deletingFile === name ? (
                    <span className="font-sans text-[10px] text-slate-500 font-bold">…</span>
                  ) : (
                    <svg width="10" height="10" viewBox="0 0 12 12" fill="none">
                      <path d="M1 1L11 11M11 1L1 11" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" />
                    </svg>
                  )}
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* ── Bottom system status bar ───────────────────────────────────── */}
      <div className="border-t border-slate-200/80 dark:border-slate-800/80 px-5 py-3.5 bg-white/40 dark:bg-slate-900/40 transition-colors">
        <div className="flex items-center justify-between">
          <span className="font-sans text-[10px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">
            Llama-3-8B · BGE Reranker
          </span>
          <div className="flex items-center gap-1.5">
            <span className="font-sans text-[9px] font-bold uppercase tracking-wider text-slate-400">online</span>
            <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse shadow-sm shadow-emerald-500/50" aria-label="System online" />
          </div>
        </div>
      </div>

    </div>
  );
}

// ── Inline Icons ──────────────────────────────────────────────────────────
function UploadIcon({ inverted }: { inverted: boolean }) {
  const color = inverted ? "#1E40AF" : "currentColor";
  return (
    <svg
      width="28" height="28" viewBox="0 0 28 28" fill="none"
      className="z-10 flex-none text-slate-500 dark:text-slate-400"
      aria-hidden="true"
    >
      <path
        d="M14 19V7M14 7L9 12M14 7L19 12"
        stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
      />
      <path
        d="M5 22H23"
        stroke={color} strokeWidth="2" strokeLinecap="round"
      />
    </svg>
  );
}

function UploadSpinner({ inverted }: { inverted: boolean }) {
  const color = inverted ? "#1E40AF" : "#3B82F6";
  return (
    <svg
      className="z-10 animate-spin"
      width="24" height="24" viewBox="0 0 24 24" fill="none"
      aria-hidden="true"
    >
      <rect
        x="11" y="1" width="2" height="7"
        fill={color}
        opacity="1"
      />
      <rect
        x="11" y="16" width="2" height="7"
        fill={color}
        opacity="0.3"
      />
      <rect
        x="16.95" y="3.05" width="2" height="7"
        fill={color}
        opacity="0.7"
        transform="rotate(45 17.95 6.55)"
      />
      <rect
        x="1" y="11" width="7" height="2"
        fill={color}
        opacity="0.15"
      />
      <rect
        x="16" y="11" width="7" height="2"
        fill={color}
        opacity="0.5"
      />
    </svg>
  );
}
