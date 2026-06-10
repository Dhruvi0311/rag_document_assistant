"""
main.py — FastAPI RAG Pipeline Server
Exposes two endpoints:
  POST /api/upload  — ingest files into ChromaDB + BM25 index
  POST /api/chat    — hybrid search + rerank + streaming LLM response
"""

import os
import sys
import json
import asyncio
import tempfile
import shutil
from typing import List, Optional, AsyncGenerator

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# ── LangChain / HuggingFace ────────────────────────────────────────────────
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

# ── Internal RAG modules (adjust sys.path if running from project root) ────
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from document_loader import DocumentLoader
from document_chunker import DocumentChunker
from vector_store import VectorStoreManager
from sparse_store import SparseStoreManager
from reranker import RerankerManager
from query_rewriter import QueryRewriter

# ── App bootstrap ──────────────────────────────────────────────────────────
load_dotenv()
app = FastAPI(title="RAG Document Assistant API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Pydantic request schemas ───────────────────────────────────────────────
class ChatMessage(BaseModel):
    role: str          # "user" | "assistant"
    content: str

class ChatRequest(BaseModel):
    query: str
    history: List[ChatMessage] = []
    top_k: int = 5
    rerank_threshold: float = 0.25

# ── Singleton service layer (initialized at startup) ───────────────────────
class RAGServices:
    llm: ChatHuggingFace = None
    vdb: VectorStoreManager = None
    sparse_db: SparseStoreManager = None
    reranker: RerankerManager = None
    rewriter: QueryRewriter = None

services = RAGServices()


@app.on_event("startup")
async def startup():
    """Initializes all heavyweight ML services once at startup."""
    print("🚀  Booting RAG services...")

    hf_token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACEHUB_ACCESS_TOKEN")
    if not hf_token:
        raise RuntimeError("HF_TOKEN not found in environment. Check your .env file.")

    os.environ["HUGGINGFACEHUB_ACCESS_TOKEN"] = hf_token
    os.environ["HF_TOKEN"] = hf_token

    # LLM
    base_llm = HuggingFaceEndpoint(
        repo_id="meta-llama/Meta-Llama-3-8B-Instruct",
        max_new_tokens=512,
        temperature=0.7,
        huggingfacehub_api_token=hf_token,
        task="text-generation",
    )
    services.llm = ChatHuggingFace(llm=base_llm)
    print("  ✓  LLM endpoint ready")

    # Vector store
    services.vdb = VectorStoreManager(db_path="chroma_db", distance_metric="cosine")
    print("  ✓  ChromaDB ready")

    # Sparse store
    services.sparse_db = SparseStoreManager(storage_path="chroma_db/bm25_index.pkl")
    print("  ✓  BM25 sparse index ready")

    # Cross-encoder reranker
    services.reranker = RerankerManager(model_name="BAAI/bge-reranker-base")
    print("  ✓  Cross-encoder reranker ready")

    # Query rewriter
    services.rewriter = QueryRewriter(llm=services.llm)
    print("  ✓  Query rewriter ready")

    print("✅  All services online.\n")


# ── /api/upload ────────────────────────────────────────────────────────────
ALLOWED_EXTENSIONS = {".pdf", ".csv", ".txt", ".docx", ".png", ".jpg", ".jpeg"}

@app.post("/api/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    """
    Accepts one or more files, saves them to a temp directory,
    runs the full ingestion pipeline, and upserts to both indices.
    Returns a summary of what was indexed.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided.")

    tmp_dir = tempfile.mkdtemp()
    saved_paths: List[str] = []
    rejected: List[str] = []

    try:
        # Save uploads to temp dir, reject unsupported types
        for upload in files:
            _, ext = os.path.splitext(upload.filename or "")
            if ext.lower() not in ALLOWED_EXTENSIONS:
                rejected.append(upload.filename)
                continue
            dest = os.path.join(tmp_dir, upload.filename)
            with open(dest, "wb") as f:
                shutil.copyfileobj(upload.file, f)
            saved_paths.append(dest)

        if not saved_paths:
            raise HTTPException(
                status_code=422,
                detail=f"No supported files. Rejected: {rejected}. "
                       f"Supported types: {', '.join(ALLOWED_EXTENSIONS)}",
            )

        # Ingestion pipeline
        loader = DocumentLoader(target_dir=tmp_dir)
        raw_docs = loader.load_batch(saved_paths)

        chunker = DocumentChunker(chunk_size=1000, chunk_overlap=200)
        chunks = chunker.chunk_documents(raw_docs)

        if not chunks:
            raise HTTPException(status_code=422, detail="Files parsed but produced no text chunks.")

        # Dual indexing
        services.vdb.upsert_chunks(chunks)
        services.sparse_db.index_chunks(chunks)

        indexed_files = list({c["metadata"]["file_name"] for c in chunks})

        return {
            "status": "success",
            "indexed_files": indexed_files,
            "total_chunks": len(chunks),
            "rejected_files": rejected,
        }

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


# ── /api/files ─────────────────────────────────────────────────────────────
@app.get("/api/files")
async def list_indexed_files():
    """Returns the list of file names currently in the vector index."""
    files = services.vdb.get_all_indexed_filenames()
    return {"files": files}


@app.delete("/api/files/{file_name}")
async def delete_file(file_name: str):
    """Removes all chunks for a given file from the vector index."""
    services.vdb.delete_file_from_index(file_name)
    return {"status": "deleted", "file_name": file_name}


# ── /api/chat ──────────────────────────────────────────────────────────────
async def token_stream(
    query: str,
    history: List[ChatMessage],
    top_k: int,
    rerank_threshold: float,
) -> AsyncGenerator[str, None]:
    """
    Core RAG streaming generator.
    Yields Server-Sent Event (SSE) lines so the frontend can consume
    token-by-token via EventSource / ReadableStream.

    SSE payload types:
      data: {"type": "citation", "chunks": [...]}
      data: {"type": "token",    "text":  "..."}
      data: {"type": "done"}
      data: {"type": "error",    "message": "..."}
    """
    DISTANCE_THRESHOLD = 0.75

    def sse(payload: dict) -> str:
        return f"data: {json.dumps(payload)}\n\n"

    try:
        # 1. Rewrite query using conversation history
        lc_history = []
        for m in history:
            if m.role == "user":
                lc_history.append(HumanMessage(content=m.content))
            else:
                lc_history.append(AIMessage(content=m.content))

        optimized_query = services.rewriter.condense_query(query, lc_history)

        # 2. Hybrid retrieval
        dense_hits = services.vdb.search_similar_chunks(optimized_query, top_k=top_k)
        sparse_hits = services.sparse_db.search_keywords(optimized_query, top_k=top_k)

        # Distance-gate dense hits
        dense_hits = [h for h in dense_hits if h.get("distance") is not None and h["distance"] <= DISTANCE_THRESHOLD]

        if not dense_hits and not sparse_hits:
            yield sse({"type": "error", "message": "No relevant context found in the indexed documents."})
            return

        # 3. RRF fusion + cross-encoder reranking
        fused = services.reranker.reciprocal_rank_fusion(dense_hits, sparse_hits)
        gated = services.reranker.rerank_and_gate_chunks(optimized_query, fused, threshold=rerank_threshold)

        if not gated:
            yield sse({"type": "error", "message": "Retrieved chunks did not pass the relevance threshold."})
            return

        # 4. Emit citation metadata before tokens start flowing
        citations = [
            {
                "file_name": c["metadata"].get("file_name", "Unknown"),
                "chunk_id": c["metadata"].get("chunk_id", ""),
                "relevance_score": round(c.get("relevance_score", 0.0), 4),
                "text_preview": c["text"][:160].strip(),
            }
            for c in gated[:5]
        ]
        yield sse({"type": "citation", "chunks": citations})

        # 5. Build context block
        context_parts = []
        for i, chunk in enumerate(gated[:5], 1):
            fname = chunk["metadata"].get("file_name", "Unknown")
            context_parts.append(f"[Source {i} — {fname}]\n{chunk['text'].strip()}")
        context_block = "\n\n".join(context_parts)

        # 6. LLM streaming
        # NOTE: ChatHuggingFace doesn't support true streaming natively via .stream(),
        # so we invoke the full response and emit tokens word-by-word to simulate
        # progressive rendering on the frontend. Replace with .astream() when
        # your endpoint supports it.
        system_instruction = (
            "You are an advanced RAG Document Assistant. Use ONLY the retrieved context below "
            "to answer the user's question. Cite source numbers when referencing specific facts. "
            "If the context does not contain the answer, state clearly that it is not in the documents.\n\n"
            f"Retrieved Context:\n{context_block}"
        )

        messages = [
            SystemMessage(content=system_instruction),
            HumanMessage(content=query),
        ]

        response_obj = await asyncio.to_thread(services.llm.invoke, messages)
        full_text: str = response_obj.content.strip()

        # Emit token-by-token (word granularity for smooth UX)
        words = full_text.split(" ")
        for i, word in enumerate(words):
            chunk_text = word if i == len(words) - 1 else word + " "
            yield sse({"type": "token", "text": chunk_text})
            await asyncio.sleep(0.018)  # ~55 words/sec — feels natural

        yield sse({"type": "done"})

    except Exception as exc:
        yield sse({"type": "error", "message": str(exc)})


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    Streaming chat endpoint. Returns SSE stream.
    Frontend should consume with fetch + ReadableStream (not EventSource,
    since POST bodies aren't supported by EventSource).
    """
    return StreamingResponse(
        token_stream(
            query=request.query,
            history=request.history,
            top_k=request.top_k,
            rerank_threshold=request.rerank_threshold,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disables Nginx response buffering
        },
    )


# ── Health check ───────────────────────────────────────────────────────────
@app.get("/api/health")
async def health():
    return {"status": "ok", "services_ready": services.llm is not None}
