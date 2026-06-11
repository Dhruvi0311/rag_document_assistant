"use client";

import { useState, useEffect } from "react";
import { useTheme } from "next-themes";
import Sidebar from "./components/Sidebar";
import ChatArena from "./components/ChatArena";
import DocumentViewer from "./components/DocumentViewer";
import KnowledgeGraph from "./components/KnowledgeGraph";
import { Message, CitationChunk } from "./types";

export default function Home() {
  const [indexedFiles, setIndexedFiles] = useState<string[]>([]);
  const [isIndexLoading, setIsIndexLoading] = useState(true);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [activeCitation, setActiveCitation] = useState<CitationChunk | null>(null);
  const [viewMode, setViewMode] = useState<"chat" | "graph">("chat");

  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  // Fetch the active file index on mount
  async function loadFiles() {
    setIsIndexLoading(true);
    try {
      const res = await fetch("http://localhost:8000/api/files");
      const data = await res.json();
      setIndexedFiles(data.files ?? []);
    } catch {
      setIndexedFiles([]);
    } finally {
      setIsIndexLoading(false);
    }
  }

  useEffect(() => {
    setMounted(true);
    loadFiles();
  }, []);

  async function handleDeleteFile(fileName: string) {
    try {
      await fetch(`http://localhost:8000/api/files/${encodeURIComponent(fileName)}`, {
        method: "DELETE",
      });
      setIndexedFiles((prev) => prev.filter((f) => f !== fileName));
    } catch (err) {
      console.error("Delete failed:", err);
    }
  }

  return (
    <div className="flex h-screen w-full overflow-hidden bg-slate-50 dark:bg-slate-950 transition-colors duration-300">

      {/* ── Wordmark Header Bar ──────────────────────────────────────── */}
      <div
        className="absolute top-0 left-0 right-0 z-20 flex items-center justify-between
                   px-6 h-14 border-b border-slate-200/80 dark:border-slate-800/80 bg-white/85 dark:bg-slate-900/85 backdrop-blur-md shadow-sm transition-colors duration-300"
      >
        <div className="flex items-center gap-4">
          {/* Hamburger toggle for sidebar on narrow screens */}
          <button
            onClick={() => setIsSidebarOpen((v) => !v)}
            className="flex flex-col gap-[5px] p-1 hover:opacity-60 transition-opacity duration-100 lg:hidden"
            aria-label={isSidebarOpen ? "Close sidebar" : "Open sidebar"}
          >
            <span className="w-5 h-[2px] bg-slate-700 dark:bg-slate-300 block rounded transition-colors" />
            <span className="w-5 h-[2px] bg-slate-700 dark:bg-slate-300 block rounded transition-colors" />
            <span className="w-5 h-[2px] bg-slate-700 dark:bg-slate-300 block rounded transition-colors" />
          </button>

          <span className="font-display text-lg font-black tracking-tight select-none text-slate-900 dark:text-white transition-colors">
            ARCHIVAL
          </span>
          <span
            className="hidden sm:inline font-sans text-[10px] font-semibold uppercase tracking-wider
                       text-slate-400 dark:text-slate-500 border-l border-slate-200 dark:border-slate-700 pl-4 transition-colors"
          >
            Document Intelligence System
          </span>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center bg-slate-100 dark:bg-slate-800/50 p-1 rounded-full border border-slate-200/60 dark:border-slate-700 shadow-inner transition-colors">
            <button
              onClick={() => setViewMode("chat")}
              className={`px-4 py-1.5 rounded-full font-sans text-[10px] font-bold uppercase tracking-wider transition-all duration-200 ${
                viewMode === "chat" 
                  ? "bg-white dark:bg-slate-700 text-blue-600 dark:text-blue-400 shadow-sm" 
                  : "text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-200/50 dark:hover:bg-slate-700/50"
              }`}
            >
              Chat
            </button>
            <button
              onClick={() => setViewMode("graph")}
              className={`px-4 py-1.5 rounded-full font-sans text-[10px] font-bold uppercase tracking-wider transition-all duration-200 ${
                viewMode === "graph" 
                  ? "bg-white dark:bg-slate-700 text-blue-600 dark:text-blue-400 shadow-sm" 
                  : "text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-200/50 dark:hover:bg-slate-700/50"
              }`}
            >
              Graph
            </button>
          </div>

          <div className="flex items-center gap-2 bg-slate-100/50 dark:bg-slate-800/30 px-3 py-1.5 rounded-full border border-slate-200/30 dark:border-slate-700/50 transition-colors">
            <span className="font-sans text-[11px] font-semibold tracking-wide text-slate-500 dark:text-slate-400 uppercase">
              {indexedFiles.length} file{indexedFiles.length !== 1 ? "s" : ""} indexed
            </span>
            <span className="w-2 h-2 bg-emerald-500 rounded-full inline-block animate-pulse" />
          </div>

          {mounted && (
            <button
              onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
              className="p-1.5 rounded-full bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-500 dark:text-slate-400 hover:text-blue-500 dark:hover:text-blue-400 transition-colors shadow-sm ml-2"
              title="Toggle Dark Mode"
            >
              {theme === 'dark' ? (
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
              ) : (
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                </svg>
              )}
            </button>
          )}
        </div>
      </div>

      {/* ── Main Content: 3-col Sidebar + 9-col Chat ─────────────────── */}
      <div className="flex w-full h-full pt-14">
        
        {viewMode === "graph" ? (
          <main className="w-full h-full flex-1">
            <KnowledgeGraph />
          </main>
        ) : (
          <>
            {/* LEFT SIDEBAR — 3 of 12 columns */}
            <aside
              className={`
                ${isSidebarOpen ? "w-80 lg:w-[25%]" : "w-0"}
                flex-none h-full border-r border-slate-200/80 dark:border-slate-800/80 bg-white/40 dark:bg-slate-900/40
                overflow-hidden transition-[width,background-color,border-color] duration-150 ease-in-out
              `}
              style={{ minWidth: isSidebarOpen ? undefined : 0 }}
            >
              <div className="w-80 lg:w-full h-full overflow-y-auto bg-slate-50/20 dark:bg-slate-900/20">
                <Sidebar
                  indexedFiles={indexedFiles}
                  isLoading={isIndexLoading}
                  onFilesUploaded={loadFiles}
                  onDeleteFile={handleDeleteFile}
                />
              </div>
            </aside>

            {/* RIGHT CHAT ARENA — 9 of 12 columns */}
            <main className={`flex-1 h-full overflow-hidden bg-white/20 dark:bg-slate-950/20 transition-[max-width,width,background-color] duration-300 ease-in-out ${activeCitation ? 'lg:max-w-[45%] border-r border-slate-200/80 dark:border-slate-800/80' : ''}`}>
              <ChatArena
                messages={messages}
                setMessages={setMessages}
                hasIndexedFiles={indexedFiles.length > 0}
                onCitationClick={setActiveCitation}
              />
            </main>

            {/* RIGHT SPLIT DOCUMENT VIEWER */}
            {activeCitation && (
              <aside className="flex-1 h-full overflow-hidden bg-white dark:bg-slate-900 border-l border-slate-200/80 dark:border-slate-800/80 z-10 animate-fade-in-right transition-colors">
                 <DocumentViewer citation={activeCitation} onClose={() => setActiveCitation(null)} />
              </aside>
            )}
          </>
        )}

      </div>
    </div>
  );
}
