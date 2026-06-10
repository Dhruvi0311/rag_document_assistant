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
    <div className="flex flex-col h-full bg-white">

      {/* ── Section header ────────────────────────────────────────────── */}
      <div className="px-5 py-4 border-b-4 border-black">
        <p className="font-mono text-label-lg uppercase tracking-widest text-black">
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
          relative mx-4 my-4 p-6 border-2 cursor-pointer
          flex flex-col items-center justify-center gap-3
          transition-colors duration-100 select-none
          ${isDragging
            ? "bg-black text-white border-black"
            : "bg-white text-black border-black hover:bg-black hover:text-white"
          }
          ${isUploading ? "pointer-events-none opacity-60" : ""}
        `}
        style={{ minHeight: 140 }}
      >
        {/* Dashed inset line — architectural detail */}
        <div
          className={`
            absolute inset-[6px] border pointer-events-none
            ${isDragging ? "border-white" : "border-gray-200 group-hover:border-white"}
          `}
          style={{ borderStyle: "dashed" }}
        />

        {isUploading ? (
          <>
            <UploadSpinner inverted={isDragging} />
            <p className="font-mono text-label-lg uppercase tracking-widest z-10">
              Indexing…
            </p>
          </>
        ) : (
          <>
            <UploadIcon inverted={isDragging} />
            <div className="text-center z-10">
              <p className="font-mono text-label-lg uppercase tracking-widest">
                {isDragging ? "Release to index" : "Drop files here"}
              </p>
              <p className="font-mono text-label-sm uppercase tracking-widest opacity-50 mt-1">
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
        <div className="mx-4 mb-4 border-2 border-black bg-black text-white p-3 animate-fade-in-up">
          <p className="font-mono text-label-sm uppercase tracking-widest opacity-70 mb-1">
            Indexed
          </p>
          <p className="font-mono text-label-lg uppercase tracking-widest">
            {uploadResult.total_chunks} chunks · {uploadResult.indexed_files.length} file
            {uploadResult.indexed_files.length !== 1 ? "s" : ""}
          </p>
          {uploadResult.rejected_files.length > 0 && (
            <p className="font-mono text-label-sm uppercase tracking-widest opacity-60 mt-1">
              Skipped: {uploadResult.rejected_files.join(", ")}
            </p>
          )}
        </div>
      )}

      {uploadError && (
        <div className="mx-4 mb-4 border-2 border-black bg-white text-black p-3 animate-fade-in-up">
          <p className="font-mono text-label-sm uppercase tracking-widest opacity-50 mb-1">Error</p>
          <p className="font-body text-body-sm text-gray-800">{uploadError}</p>
        </div>
      )}

      {/* ── Active Index list ──────────────────────────────────────────── */}
      <div className="border-t-4 border-black flex-1 overflow-y-auto">
        <div className="px-5 py-3 border-b border-gray-200">
          <p className="font-mono text-label-sm uppercase tracking-widest text-gray-400">
            Active Index ({indexedFiles.length})
          </p>
        </div>

        {isLoading ? (
          <div className="p-4 space-y-3">
            {[1, 2, 3].map((n) => (
              <div key={n} className="skeleton h-10 w-full" />
            ))}
          </div>
        ) : indexedFiles.length === 0 ? (
          <div className="px-5 py-8 text-center">
            <p className="font-mono text-label-sm uppercase tracking-widest text-gray-400">
              No documents indexed
            </p>
            <p className="font-body text-body-sm text-gray-400 mt-2">
              Upload files above to begin.
            </p>
          </div>
        ) : (
          <ul>
            {indexedFiles.map((name) => (
              <li
                key={name}
                className="group flex items-center justify-between
                           px-4 py-3 border-b-4 border-black bg-white
                           hover:bg-black hover:text-white transition-colors duration-100"
              >
                <div className="flex items-center gap-3 min-w-0 flex-1">
                  {/* Type badge */}
                  <span
                    className="flex-none font-mono text-label-sm uppercase tracking-widest
                               px-1.5 py-0.5 border border-current opacity-60"
                  >
                    {getFileTypeLabel(name)}
                  </span>
                  {/* File name */}
                  <span className="font-mono text-label-lg uppercase tracking-wider truncate">
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
                             transition-opacity duration-100 p-1
                             hover:bg-white hover:text-black focus-visible:opacity-100"
                  aria-label={`Remove ${name} from index`}
                  title="Remove from index"
                >
                  {deletingFile === name ? (
                    <span className="font-mono text-label-sm">…</span>
                  ) : (
                    <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                      <path d="M1 1L11 11M11 1L1 11" stroke="currentColor" strokeWidth="2" />
                    </svg>
                  )}
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* ── Bottom system status bar ───────────────────────────────────── */}
      <div className="border-t-4 border-black px-5 py-3">
        <div className="flex items-center justify-between">
          <span className="font-mono text-label-sm uppercase tracking-widest text-gray-400">
            Llama-3-8B · BGE Reranker
          </span>
          <span className="w-2 h-2 bg-black" aria-label="System online" />
        </div>
      </div>

    </div>
  );
}

// ── Inline Icons ──────────────────────────────────────────────────────────
function UploadIcon({ inverted }: { inverted: boolean }) {
  const color = inverted ? "white" : "black";
  return (
    <svg
      width="28" height="28" viewBox="0 0 28 28" fill="none"
      className="z-10 flex-none"
      aria-hidden="true"
    >
      <path
        d="M14 20V8M14 8L9 13M14 8L19 13"
        stroke={color} strokeWidth="2" strokeLinecap="square" strokeLinejoin="miter"
      />
      <path
        d="M5 22H23"
        stroke={color} strokeWidth="2" strokeLinecap="square"
      />
    </svg>
  );
}

function UploadSpinner({ inverted }: { inverted: boolean }) {
  return (
    <svg
      className="z-10 animate-spin"
      width="24" height="24" viewBox="0 0 24 24" fill="none"
      aria-hidden="true"
    >
      <rect
        x="11" y="1" width="2" height="7"
        fill={inverted ? "white" : "black"}
        opacity="1"
      />
      <rect
        x="11" y="16" width="2" height="7"
        fill={inverted ? "white" : "black"}
        opacity="0.3"
      />
      <rect
        x="16.95" y="3.05" width="2" height="7"
        fill={inverted ? "white" : "black"}
        opacity="0.7"
        transform="rotate(45 17.95 6.55)"
      />
      <rect
        x="1" y="11" width="7" height="2"
        fill={inverted ? "white" : "black"}
        opacity="0.15"
      />
      <rect
        x="16" y="11" width="7" height="2"
        fill={inverted ? "white" : "black"}
        opacity="0.5"
      />
    </svg>
  );
}
