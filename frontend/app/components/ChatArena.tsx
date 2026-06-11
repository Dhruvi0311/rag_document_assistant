"use client";

import {
  useRef,
  useState,
  useEffect,
  useCallback,
  KeyboardEvent,
  FormEvent,
} from "react";
import { Message, CitationChunk } from "../types";
import CitationPanel from "./CitationPanel";
import AnalyticsDashboard from "./AnalyticsDashboard";

const API_BASE = "http://localhost:8000";

interface ChatArenaProps {
  messages: Message[];
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
  hasIndexedFiles: boolean;
  onCitationClick?: (citation: CitationChunk) => void;
}

// ── SSE event payload shapes from the backend ────────────────────────────
interface SSECitationEvent  { type: "citation"; chunks: CitationChunk[] }
interface SSETokenEvent     { type: "token";    text: string }
interface SSEDoneEvent      { type: "done" }
interface SSEErrorEvent     { type: "error";    message: string }
interface SSEAnalyticsEvent { type: "analytics"; data: any }
type SSEEvent = SSECitationEvent | SSETokenEvent | SSEDoneEvent | SSEErrorEvent | SSEAnalyticsEvent;

function generateId() {
  return Math.random().toString(36).slice(2, 10);
}

export default function ChatArena({
  messages,
  setMessages,
  hasIndexedFiles,
  onCitationClick,
}: ChatArenaProps) {
  const [inputValue, setInputValue] = useState("");
  const [isResponding, setIsResponding] = useState(false);
  const [isCrossEncoderEnabled, setIsCrossEncoderEnabled] = useState(true);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  // Auto-scroll to bottom whenever messages change
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Auto-resize textarea
  function handleInputChange(e: React.ChangeEvent<HTMLTextAreaElement>) {
    setInputValue(e.target.value);
    e.target.style.height = "auto";
    e.target.style.height = `${Math.min(e.target.scrollHeight, 160)}px`;
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!isResponding && inputValue.trim()) {
        submitQuery(inputValue.trim());
      }
    }
  }

  function handleFormSubmit(e: FormEvent) {
    e.preventDefault();
    if (!isResponding && inputValue.trim()) {
      submitQuery(inputValue.trim());
    }
  }

  function handleStop() {
    abortRef.current?.abort();
    setIsResponding(false);
    // Mark the currently streaming message as complete
    setMessages((prev) =>
      prev.map((m) =>
        m.isStreaming ? { ...m, isStreaming: false } : m
      )
    );
  }

  const submitQuery = useCallback(
    async (query: string) => {
      if (isResponding) return;

      setInputValue("");
      if (inputRef.current) {
        inputRef.current.style.height = "auto";
      }
      setIsResponding(true);

      // Add user message
      const userMsg: Message = {
        id: generateId(),
        role: "user",
        content: query,
      };

      // Add placeholder assistant message
      const assistantId = generateId();
      const assistantMsg: Message = {
        id: assistantId,
        role: "assistant",
        content: "",
        isStreaming: true,
      };

      setMessages((prev) => [...prev, userMsg, assistantMsg]);

      // Build history payload from current messages (before adding the new ones)
      const historyPayload = messages.map((m) => ({
        role: m.role,
        content: m.content,
      }));

      try {
        const controller = new AbortController();
        abortRef.current = controller;

        const res = await fetch(`${API_BASE}/api/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            query,
            history: historyPayload,
            top_k: 5,
            rerank_threshold: isCrossEncoderEnabled ? 0.25 : 0.0,
          }),
          signal: controller.signal,
        });

        if (!res.ok) {
          throw new Error(`API error: ${res.status}`);
        }

        const reader = res.body!.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        // ── SSE parsing loop ──────────────────────────────────────────
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          // Keep potentially incomplete last line in buffer
          buffer = lines.pop() ?? "";

          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            const payload = line.slice(6).trim();
            if (!payload) continue;

            let event: SSEEvent;
            try {
              event = JSON.parse(payload);
            } catch {
              continue;
            }

            if (event.type === "citation") {
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantId
                    ? { ...m, citations: event.chunks }
                    : m
                )
              );
            } else if (event.type === "analytics") {
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantId
                    ? { ...m, analytics: event.data }
                    : m
                )
              );
            } else if (event.type === "token") {
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantId
                    ? { ...m, content: m.content + event.text }
                    : m
                )
              );
            } else if (event.type === "done") {
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantId
                    ? { ...m, isStreaming: false }
                    : m
                )
              );
              setIsResponding(false);
            } else if (event.type === "error") {
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantId
                    ? {
                        ...m,
                        content: event.message,
                        isStreaming: false,
                        isError: true,
                      }
                    : m
                )
              );
              setIsResponding(false);
            }
          }
        }
      } catch (err: unknown) {
        if ((err as Error).name === "AbortError") return;
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? {
                  ...m,
                  content: "Connection error. Is the backend running on port 8000?",
                  isStreaming: false,
                  isError: true,
                }
              : m
          )
        );
        setIsResponding(false);
      }
    },
    [isResponding, messages, setMessages, isCrossEncoderEnabled]
  );

  const isEmpty = messages.length === 0;

  return (
    <div className="flex flex-col h-full bg-[#F4F7FB]/40 dark:bg-slate-900/40 transition-colors">

      {/* ── Message stream ─────────────────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto flex flex-col">

        {/* Empty state */}
        {isEmpty && (
          <div className="flex-1 flex flex-col items-center justify-center px-8 py-16 text-center geometric-pattern relative">
            {/* Blur spots to soften the geometric lines */}
            <div className="absolute top-1/4 left-1/4 w-72 h-72 rounded-full bg-blue-400/5 filter blur-3xl pointer-events-none" />
            <div className="absolute bottom-1/4 right-1/4 w-80 h-80 rounded-full bg-indigo-400/5 filter blur-3xl pointer-events-none" />

            <div className="max-w-xl w-full z-10 bg-white/70 dark:bg-slate-800/80 border border-white/60 dark:border-slate-700/60 p-8 rounded-3xl shadow-xl backdrop-blur-md transition-colors">
              {/* Decorative soft line */}
              <div className="w-[2px] h-10 bg-slate-200 dark:bg-slate-700 mx-auto mb-5 rounded-full" />

              <h1 className="font-display text-display-xl font-black tracking-tighter text-slate-800 dark:text-slate-100 mb-3 transition-colors">
                Query the<br />
                <em className="font-normal text-slate-500 dark:text-slate-400">Archive</em>
              </h1>

              <p className="font-sans text-xs font-semibold text-gray-500 dark:text-slate-400 mb-6 max-w-sm mx-auto tracking-wide uppercase transition-colors">
                {hasIndexedFiles
                  ? "Your documents are indexed and ready. Ask anything."
                  : "Upload documents using the panel on the left to begin."}
              </p>

              {/* Moved main chat input container inside the central card */}
              <form
                onSubmit={handleFormSubmit}
                className="mt-6 text-left w-full"
              >
                <div className="flex items-center gap-3 relative bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-700/80 rounded-[32px] p-2 pr-3 shadow-sm hover:border-slate-300 dark:hover:border-slate-600 focus-within:border-blue-400 focus-within:ring-4 focus-within:ring-blue-500/5 transition-all">
                  <textarea
                    ref={inputRef}
                    value={inputValue}
                    onChange={handleInputChange}
                    onKeyDown={handleKeyDown}
                    placeholder={
                      hasIndexedFiles
                        ? "Ask a question about your documents…"
                        : "Upload documents to begin…"
                    }
                    disabled={isResponding || !hasIndexedFiles}
                    rows={1}
                    className="w-full bg-transparent resize-none overflow-hidden pl-4 pr-12 py-2.5 outline-none font-sans text-sm text-slate-800 dark:text-slate-200 placeholder:text-slate-400"
                    style={{ lineHeight: "1.5", maxHeight: "120px" }}
                    aria-label="Chat input"
                  />
                  
                  {/* Circular Send / Stop button inside input field */}
                  <div className="absolute right-3.5 bottom-2.5">
                    {isResponding ? (
                      <button
                        type="button"
                        onClick={handleStop}
                        className="flex items-center justify-center w-9 h-9 rounded-full bg-rose-500 hover:bg-rose-600 text-white shadow-sm transition-all duration-150"
                        aria-label="Stop generating"
                      >
                        <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                          <rect x="2" y="2" width="8" height="8" fill="currentColor" rx="1" />
                        </svg>
                      </button>
                    ) : (
                      <button
                        type="submit"
                        disabled={!inputValue.trim() || !hasIndexedFiles}
                        className="flex items-center justify-center w-9 h-9 rounded-full bg-slate-900 dark:bg-slate-700 text-white shadow hover:bg-slate-800 dark:hover:bg-slate-600 disabled:opacity-30 disabled:pointer-events-none transition-all duration-150"
                        aria-label="Send message"
                      >
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                          <path d="M22 2L11 13M22 2L15 22L11 13M11 13L2 9L22 2" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                      </button>
                    )}
                  </div>
                </div>
                
                <div className="flex justify-between items-center px-4 mt-2">
                  <span className="font-sans text-[10px] font-semibold tracking-wider text-slate-400">
                    Enter to send · Shift+Enter for newline
                  </span>
                  {inputValue.length > 0 && (
                    <span className="font-sans text-[10px] font-bold text-slate-400">
                      {inputValue.length}
                    </span>
                  )}
                </div>
              </form>

              {/* Capability labels & Toggle Switch unified row under input */}
              <div className="flex flex-wrap justify-center items-center gap-2 mt-6">
                {[
                  "Hybrid Retrieval",
                  "Query Rewriting",
                  "Source Citations",
                ].map((label) => (
                  <span
                    key={label}
                    className="font-sans text-[10px] font-bold uppercase tracking-wider
                               text-gray-500 dark:text-gray-400 bg-slate-50 dark:bg-slate-800 border border-gray-300 dark:border-gray-600 px-3 py-1.5 rounded-full transition-colors"
                  >
                    {label}
                  </span>
                ))}

                {/* Unified Cross-Encoder switch styled as a pill option */}
                <div className="flex items-center gap-2 bg-slate-50 dark:bg-slate-800 border border-gray-300 dark:border-gray-600 px-3 py-1.5 rounded-full transition-colors">
                  <span className="font-sans text-[10px] font-bold uppercase tracking-wider text-gray-500 dark:text-gray-400">
                    Cross-Encoder
                  </span>
                  <button
                    type="button"
                    onClick={() => setIsCrossEncoderEnabled(!isCrossEncoderEnabled)}
                    className={`
                      relative w-7 h-4 rounded-full p-0.5 transition-colors duration-200 ease-in-out focus:outline-none
                      ${isCrossEncoderEnabled ? "bg-slate-900 dark:bg-blue-500" : "bg-slate-200 dark:bg-slate-600"}
                    `}
                    aria-label="Toggle Cross-Encoder Reranking"
                  >
                    <span
                      className={`
                        block w-3 h-3 rounded-full bg-white shadow-sm transform transition-transform duration-200 ease-in-out
                        ${isCrossEncoderEnabled ? "translate-x-3" : "translate-x-0"}
                      `}
                    />
                  </button>
                </div>
              </div>

            </div>
          </div>
        )}

        {/* Messages */}
        {!isEmpty && (
          <div className="max-w-3xl mx-auto px-6 py-8 space-y-0">
            {messages.map((msg, idx) => (
              <MessageBlock
                key={msg.id}
                message={msg}
                isLast={idx === messages.length - 1}
                onCitationClick={onCitationClick}
              />
            ))}
            <div ref={bottomRef} className="h-4" />
          </div>
        )}
      </div>

      {/* ── Bottom Input area (active only when messages exist) ────────────────────────── */}
      {!isEmpty && (
        <div className="border-t border-slate-200/50 dark:border-slate-800/50 bg-[#F4F7FB]/40 dark:bg-slate-900/40 py-6 px-4 transition-colors">
          <form
            onSubmit={handleFormSubmit}
            className="max-w-3xl mx-auto bg-white dark:bg-slate-800 border border-slate-200/60 dark:border-slate-700/60 shadow-xl rounded-3xl p-4 md:p-5 transition-all hover:shadow-2xl hover:border-slate-300 dark:hover:border-slate-600"
          >
            {/* Header row for form: Toggle and option description */}
            <div className="flex justify-between items-center mb-3 px-1">
              <span className="font-sans text-[10px] font-bold uppercase tracking-wider text-slate-400">
                Query Options
              </span>
              
              {/* Cross-Encoder Toggle switch when message list is active */}
              <div className="flex items-center gap-2">
                <span className="font-sans text-[10px] font-bold uppercase tracking-wider text-slate-500">
                  Cross-Encoder Reranking
                </span>
                <button
                  type="button"
                  onClick={() => setIsCrossEncoderEnabled(!isCrossEncoderEnabled)}
                  className={`
                    relative w-8 h-4.5 rounded-full p-0.5 transition-colors duration-200 ease-in-out focus:outline-none
                    ${isCrossEncoderEnabled ? "bg-slate-900 dark:bg-blue-500" : "bg-slate-200 dark:bg-slate-600"}
                  `}
                  aria-label="Toggle Cross-Encoder Reranking"
                >
                  <span
                    className={`
                      block w-3.5 h-3.5 rounded-full bg-white shadow-sm transform transition-transform duration-200 ease-in-out
                      ${isCrossEncoderEnabled ? "translate-x-3.5" : "translate-x-0"}
                    `}
                  />
                </button>
              </div>
            </div>

            <div className="flex items-center gap-3 relative bg-slate-50/50 dark:bg-slate-900/50 border border-slate-200/80 dark:border-slate-700 rounded-[32px] p-2 pr-3 shadow-inner hover:border-slate-300 dark:hover:border-slate-500 focus-within:border-blue-400 focus-within:ring-4 focus-within:ring-blue-500/5 transition-all">
              <textarea
                ref={inputRef}
                value={inputValue}
                onChange={handleInputChange}
                onKeyDown={handleKeyDown}
                placeholder={
                  hasIndexedFiles
                    ? "Ask a question about your documents…"
                    : "Upload documents to begin…"
                }
                disabled={isResponding || !hasIndexedFiles}
                rows={1}
                className="w-full bg-transparent resize-none overflow-hidden pl-4 pr-12 py-2.5 outline-none font-sans text-sm text-slate-800 dark:text-slate-200 placeholder:text-slate-400"
                style={{ lineHeight: "1.5", maxHeight: "160px" }}
                aria-label="Chat input"
              />
              
              {/* Circular Send / Stop button inside input field */}
              <div className="absolute right-3.5 bottom-2.5">
                {isResponding ? (
                  <button
                    type="button"
                    onClick={handleStop}
                    className="flex items-center justify-center w-9 h-9 rounded-full bg-rose-500 hover:bg-rose-600 text-white shadow-sm transition-all duration-150"
                    aria-label="Stop generating"
                  >
                    <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                      <rect x="2" y="2" width="8" height="8" fill="currentColor" rx="1" />
                    </svg>
                  </button>
                ) : (
                  <button
                    type="submit"
                    disabled={!inputValue.trim() || !hasIndexedFiles}
                    className="flex items-center justify-center w-9 h-9 rounded-full bg-slate-900 dark:bg-slate-700 text-white shadow hover:bg-slate-800 dark:hover:bg-slate-600 disabled:opacity-30 disabled:pointer-events-none transition-all duration-150"
                    aria-label="Send message"
                  >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                      <path d="M22 2L11 13M22 2L15 22L11 13M11 13L2 9L22 2" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  </button>
                )}
              </div>
            </div>
            
            <div className="flex justify-between items-center px-4 mt-2.5">
              <span className="font-sans text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                Enter to send · Shift+Enter for newline
              </span>
              {inputValue.length > 0 && (
                <span className="font-sans text-[10px] font-bold text-slate-400">
                  {inputValue.length}
                </span>
              )}
            </div>
          </form>
        </div>
      )}

    </div>
  );
}

// ── Individual message block ──────────────────────────────────────────────
function MessageBlock({
  message,
  isLast,
  onCitationClick,
}: {
  message: Message;
  isLast: boolean;
  onCitationClick?: (citation: CitationChunk) => void;
}) {
  const isUser = message.role === "user";

  return (
    <div
      className={`animate-fade-in-up ${isLast ? "" : ""}`}
    >
      {isUser ? (
        // ── User message: Playfair Display serif, right-aligned, soft border ────
        <div className="py-8 border-b border-slate-100 dark:border-slate-800/50 transition-colors">
          <div className="flex flex-col items-end gap-3">
            <span className="font-sans text-[10px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">
              You
            </span>
            <p
              className="font-display text-display-lg font-black tracking-tighter
                         text-slate-900 dark:text-white text-right max-w-2xl transition-colors"
            >
              {message.content}
            </p>
          </div>
        </div>
      ) : (
        // ── Assistant message: Source Serif 4 body text, soft borders ─────────────────
        <div className={`py-8 transition-colors ${isLast ? "" : "border-b border-slate-100 dark:border-slate-800/50"}`}>
          {/* Role label */}
          <div className="flex items-center gap-3 mb-5">
            <span className="font-sans text-[10px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">
              Archival
            </span>
            {message.isStreaming && (
              <span
                className="font-sans text-[9px] font-bold uppercase tracking-wider
                           text-blue-600 bg-blue-50 border border-blue-100 px-2 py-0.5 rounded-full animate-pulse"
              >
                Generating
              </span>
            )}
            {message.isError && (
              <span
                className="font-sans text-[9px] font-bold uppercase tracking-wider
                           bg-rose-500 text-white px-2 py-0.5 rounded-full"
              >
                Error
              </span>
            )}
          </div>

          {/* Response body */}
          {message.content ? (
            <div
              className={`
                font-body text-body-lg leading-relaxed text-slate-800 dark:text-slate-200 transition-colors
                ${message.isStreaming ? "cursor-blink" : ""}
                ${message.isError ? "text-rose-500 italic" : ""}
              `}
            >
              <FormattedResponse text={message.content} />
            </div>
          ) : (
            // Loading skeleton while waiting for first token
            message.isStreaming && (
              <div className="space-y-3">
                <div className="skeleton h-5 w-full" />
                <div className="skeleton h-5 w-4/5" />
                <div className="skeleton h-5 w-3/5" />
              </div>
            )
          )}

          {/* Citation panel */}
          {message.citations && message.citations.length > 0 && (
            <CitationPanel citations={message.citations} onCitationClick={onCitationClick} />
          )}

          {/* Analytics Dashboard */}
          {!message.isStreaming && message.analytics && (
            <AnalyticsDashboard analytics={message.analytics} topCitation={message.citations?.[0]} />
          )}
        </div>
      )}
    </div>
  );
}

// ── Minimal text formatter (handles bold and newlines) ────────────────────
function FormattedResponse({ text }: { text: string }) {
  // Split into paragraphs on double newlines
  const paragraphs = text.split(/\n\n+/);

  return (
    <>
      {paragraphs.map((para, pi) => {
        const lines = para.split("\n");
        return (
          <p key={pi} className={pi > 0 ? "mt-4" : ""}>
            {lines.map((line, li) => (
              <span key={li}>
                {li > 0 && <br />}
                <InlineBold text={line} />
              </span>
            ))}
          </p>
        );
      })}
    </>
  );
}

// Renders **bold** markdown syntax inline
function InlineBold({ text }: { text: string }) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return (
    <>
      {parts.map((part, i) =>
        part.startsWith("**") && part.endsWith("**") ? (
          <strong key={i} className="font-semibold text-slate-900 dark:text-white">
            {part.slice(2, -2)}
          </strong>
        ) : (
          <span key={i}>{part}</span>
        )
      )}
    </>
  );
}
