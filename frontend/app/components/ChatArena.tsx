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

const API_BASE = "http://localhost:8000";

interface ChatArenaProps {
  messages: Message[];
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
  hasIndexedFiles: boolean;
}

// ── SSE event payload shapes from the backend ────────────────────────────
interface SSECitationEvent  { type: "citation"; chunks: CitationChunk[] }
interface SSETokenEvent     { type: "token";    text: string }
interface SSEDoneEvent      { type: "done" }
interface SSEErrorEvent     { type: "error";    message: string }
type SSEEvent = SSECitationEvent | SSETokenEvent | SSEDoneEvent | SSEErrorEvent;

function generateId() {
  return Math.random().toString(36).slice(2, 10);
}

export default function ChatArena({
  messages,
  setMessages,
  hasIndexedFiles,
}: ChatArenaProps) {
  const [inputValue, setInputValue] = useState("");
  const [isResponding, setIsResponding] = useState(false);
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
    e.target.style.height = `${Math.min(e.target.scrollHeight, 200)}px`;
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
            rerank_threshold: 0.25,
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
    [isResponding, messages, setMessages]
  );

  const isEmpty = messages.length === 0;

  return (
    <div className="flex flex-col h-full bg-white">

      {/* ── Message stream ─────────────────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto">

        {/* Empty state */}
        {isEmpty && (
          <div className="flex flex-col items-center justify-center h-full px-8 py-16 text-center">
            <div className="max-w-xl">
              {/* Decorative vertical rule */}
              <div className="w-[1px] h-16 bg-black mx-auto mb-8" />

              <h1 className="font-display text-display-xl font-black tracking-tighter mb-6">
                Query the<br />
                <em className="font-normal">Archive</em>
              </h1>

              <p className="font-body text-body-md text-gray-600 mb-8 max-w-sm mx-auto">
                {hasIndexedFiles
                  ? "Your documents are indexed and ready. Ask anything."
                  : "Upload documents using the panel on the left to begin."}
              </p>

              {/* Horizontal rule */}
              <div className="border-t border-gray-200 w-32 mx-auto mb-6" />

              {/* Capability labels */}
              <div className="flex flex-wrap justify-center gap-3">
                {[
                  "Hybrid Retrieval",
                  "Cross-Encoder Reranking",
                  "Query Rewriting",
                  "Source Citations",
                ].map((label) => (
                  <span
                    key={label}
                    className="font-mono text-label-sm uppercase tracking-widest
                               text-gray-400 border border-gray-200 px-3 py-1"
                  >
                    {label}
                  </span>
                ))}
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
              />
            ))}
            <div ref={bottomRef} className="h-4" />
          </div>
        )}
      </div>

      {/* ── Input area ────────────────────────────────────────────────── */}
      <div className="border-t-4 border-black bg-white">
        <form
          onSubmit={handleFormSubmit}
          className="max-w-3xl mx-auto px-6 py-5"
        >
          <div className="flex items-end gap-4">
            {/* Textarea with underline only */}
            <div className="flex-1">
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
                className="input-underline resize-none overflow-hidden"
                style={{ lineHeight: "1.6" }}
                aria-label="Chat input"
              />
              <div className="flex justify-between items-center mt-2">
                <span className="font-mono text-label-sm uppercase tracking-widest text-gray-400">
                  Enter to send · Shift+Enter for newline
                </span>
                {inputValue.length > 0 && (
                  <span className="font-mono text-label-sm text-gray-400">
                    {inputValue.length}
                  </span>
                )}
              </div>
            </div>

            {/* Send / Stop button */}
            {isResponding ? (
              <button
                type="button"
                onClick={handleStop}
                className="flex-none btn-primary py-2.5 px-5"
              >
                Stop
              </button>
            ) : (
              <button
                type="submit"
                disabled={!inputValue.trim() || !hasIndexedFiles}
                className="flex-none btn-primary py-2.5 px-5"
              >
                Send
              </button>
            )}
          </div>
        </form>
      </div>

    </div>
  );
}

// ── Individual message block ──────────────────────────────────────────────
function MessageBlock({
  message,
  isLast,
}: {
  message: Message;
  isLast: boolean;
}) {
  const isUser = message.role === "user";

  return (
    <div
      className={`animate-fade-in-up ${isLast ? "" : ""}`}
    >
      {isUser ? (
        // ── User message: oversized Playfair Display, right-aligned ────
        <div className="py-8 border-b-4 border-black">
          <div className="flex flex-col items-end gap-3">
            <span className="font-mono text-label-sm uppercase tracking-widest text-gray-400">
              You
            </span>
            <p
              className="font-display text-display-lg font-black tracking-tighter
                         text-black text-right max-w-2xl"
            >
              {message.content}
            </p>
          </div>
        </div>
      ) : (
        // ── Assistant message: Source Serif 4 body text ─────────────────
        <div className={`py-8 ${isLast ? "" : "border-b border-gray-200"}`}>
          {/* Role label */}
          <div className="flex items-center gap-3 mb-5">
            <span className="font-mono text-label-sm uppercase tracking-widest text-gray-400">
              Archival
            </span>
            {message.isStreaming && (
              <span
                className="font-mono text-label-sm uppercase tracking-widest
                           text-gray-400 border border-gray-200 px-1.5 py-0.5 animate-pulse"
              >
                Generating
              </span>
            )}
            {message.isError && (
              <span
                className="font-mono text-label-sm uppercase tracking-widest
                           bg-black text-white px-1.5 py-0.5"
              >
                Error
              </span>
            )}
          </div>

          {/* Response body */}
          {message.content ? (
            <div
              className={`
                font-body text-body-lg leading-relaxed text-black
                ${message.isStreaming ? "cursor-blink" : ""}
                ${message.isError ? "text-gray-600 italic" : ""}
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
          {!message.isStreaming && message.citations && message.citations.length > 0 && (
            <CitationPanel citations={message.citations} />
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
          <strong key={i} className="font-semibold">
            {part.slice(2, -2)}
          </strong>
        ) : (
          <span key={i}>{part}</span>
        )
      )}
    </>
  );
}
