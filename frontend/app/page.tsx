"use client";

import { useState, useEffect } from "react";
import Sidebar from "./components/Sidebar";
import ChatArena from "./components/ChatArena";
import { Message } from "./types";

export default function Home() {
  const [indexedFiles, setIndexedFiles] = useState<string[]>([]);
  const [isIndexLoading, setIsIndexLoading] = useState(true);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

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
    <div className="flex h-screen w-full overflow-hidden bg-white">

      {/* ── Wordmark Header Bar ──────────────────────────────────────── */}
      <div
        className="absolute top-0 left-0 right-0 z-10 flex items-center justify-between
                   px-6 h-14 border-b-4 border-black bg-white"
      >
        <div className="flex items-center gap-4">
          {/* Hamburger toggle for sidebar on narrow screens */}
          <button
            onClick={() => setIsSidebarOpen((v) => !v)}
            className="flex flex-col gap-[5px] p-1 hover:opacity-60 transition-opacity duration-100 lg:hidden"
            aria-label={isSidebarOpen ? "Close sidebar" : "Open sidebar"}
          >
            <span className="w-5 h-[2px] bg-black block" />
            <span className="w-5 h-[2px] bg-black block" />
            <span className="w-5 h-[2px] bg-black block" />
          </button>

          <span className="font-display text-lg font-black tracking-tight select-none">
            ARCHIVAL
          </span>
          <span
            className="hidden sm:inline font-mono text-label-sm uppercase tracking-widest
                       text-gray-400 border-l border-gray-200 pl-4"
          >
            Document Intelligence System
          </span>
        </div>

        <div className="flex items-center gap-2">
          <span className="font-mono text-label-sm uppercase tracking-widest text-gray-400">
            {indexedFiles.length} file{indexedFiles.length !== 1 ? "s" : ""} indexed
          </span>
          <span className="w-2 h-2 bg-black inline-block" />
        </div>
      </div>

      {/* ── Main Content: 3-col Sidebar + 9-col Chat ─────────────────── */}
      <div className="flex w-full h-full pt-14">

        {/* LEFT SIDEBAR — 3 of 12 columns */}
        <aside
          className={`
            ${isSidebarOpen ? "w-80 lg:w-[25%]" : "w-0"}
            flex-none h-full border-r-4 border-black
            overflow-hidden transition-[width] duration-100
          `}
          style={{ minWidth: isSidebarOpen ? undefined : 0 }}
        >
          <div className="w-80 lg:w-full h-full overflow-y-auto">
            <Sidebar
              indexedFiles={indexedFiles}
              isLoading={isIndexLoading}
              onFilesUploaded={loadFiles}
              onDeleteFile={handleDeleteFile}
            />
          </div>
        </aside>

        {/* RIGHT CHAT ARENA — 9 of 12 columns */}
        <main className="flex-1 h-full overflow-hidden">
          <ChatArena
            messages={messages}
            setMessages={setMessages}
            hasIndexedFiles={indexedFiles.length > 0}
          />
        </main>

      </div>
    </div>
  );
}
