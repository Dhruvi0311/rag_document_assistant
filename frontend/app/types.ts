// ── Shared Type Definitions ───────────────────────────────────────────────

export interface CitationChunk {
  file_name: string;
  chunk_id: string;
  relevance_score: number;
  text_preview: string;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: CitationChunk[];
  isStreaming?: boolean;
  isError?: boolean;
}

export interface UploadResult {
  status: string;
  indexed_files: string[];
  total_chunks: number;
  rejected_files: string[];
}
