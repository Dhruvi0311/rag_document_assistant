// ── Shared Type Definitions ───────────────────────────────────────────────

export interface CitationChunk {
  file_name: string;
  chunk_id: string;
  relevance_score: number;
  vector_distance?: number;
  rank_shift?: number;
  text_preview: string;
  full_text?: string;
  page_number?: number;
}

export interface AnalyticsData {
  latency_ms: number;
  token_count: number;
  dense_hits: number;
  sparse_hits: number;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: CitationChunk[];
  isStreaming?: boolean;
  isError?: boolean;
  analytics?: AnalyticsData;
}

export interface UploadResult {
  status: string;
  indexed_files: string[];
  total_chunks: number;
  rejected_files: string[];
}
