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
from fastapi.staticfiles import StaticFiles
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
from router import route_intent
from general_chat import general_chat_stream
from rag_chain import rag_token_stream

# ── App bootstrap ──────────────────────────────────────────────────────────
load_dotenv()
app = FastAPI(title="RAG Document Assistant API", version="2.0.0")

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/api/documents", StaticFiles(directory=UPLOAD_DIR), name="documents")

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
    Accepts one or more files, saves them to a permanent directory,
    runs the full ingestion pipeline, and upserts to both indices.
    Returns a summary of what was indexed.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided.")

    saved_paths: List[str] = []
    rejected: List[str] = []

    # Save uploads to UPLOAD_DIR, reject unsupported types
    for upload in files:
        _, ext = os.path.splitext(upload.filename or "")
        if ext.lower() not in ALLOWED_EXTENSIONS:
            rejected.append(upload.filename)
            continue
        dest = os.path.join(UPLOAD_DIR, upload.filename)
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
    loader = DocumentLoader(target_dir=UPLOAD_DIR)
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


# ── /api/files ─────────────────────────────────────────────────────────────
@app.get("/api/files")
async def list_indexed_files():
    """Returns the list of file names currently in the vector index."""
    files = services.vdb.get_all_indexed_filenames()
    return {"files": files}


@app.delete("/api/files/{file_name}")
async def delete_file(file_name: str):
    """Removes all chunks for a given file from the vector index and disk."""
    services.vdb.delete_file_from_index(file_name)
    file_path = os.path.join(UPLOAD_DIR, file_name)
    if os.path.exists(file_path):
        os.remove(file_path)
    return {"status": "deleted", "file_name": file_name}


# ── /api/chat ──────────────────────────────────────────────────────────────
@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    Streaming chat endpoint with intelligent routing and short-term memory buffer.
    Frontend should consume with fetch + ReadableStream.
    """
    # 1. Short-term memory buffer (last 10 messages = 5 pairs)
    recent_history = request.history[-10:] if request.history else []
    
    # 2. Intent Classification
    intent = route_intent(request.query, recent_history, services.llm)
    print(f"[{request.query}] -> Routed as: {intent}")
    
    # 3. Conditional Routing
    if intent == "GENERAL_CHAT":
        stream_generator = general_chat_stream(
            query=request.query,
            history=recent_history,
            llm=services.llm
        )
    else:
        stream_generator = rag_token_stream(
            query=request.query,
            history=recent_history,
            top_k=request.top_k,
            rerank_threshold=request.rerank_threshold,
            services=services
        )
        
    return StreamingResponse(
        stream_generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disables Nginx response buffering
        },
    )


# ── /api/graph ─────────────────────────────────────────────────────────────
@app.get("/api/graph")
async def get_knowledge_graph():
    file_texts = {}
    file_chunks = {}
    for chunk in services.sparse_db.raw_chunks:
        fname = chunk["metadata"].get("file_name", "Unknown")
        file_texts[fname] = file_texts.get(fname, "") + " " + chunk["text"]
        file_chunks[fname] = file_chunks.get(fname, 0) + 1
        
    from collections import Counter
    import re
    stop_words = {"the","and","of","to","a","in","is","that","for","it","as","was","with","be","by","on","not","this","are","or","from","at","which","but","have","an","has","they","you","will","can","if","their","we","what","about","when","there","all","out","up","who","so","would","more","some","them","these","into","its","only","could","than","then","other","how","also"}
    
    nodes = []
    links = []
    keyword_freq = {}
    file_keywords = {}
    
    for fname, text in file_texts.items():
        nodes.append({
            "id": fname, 
            "group": "file", 
            "val": 12 + min(file_chunks[fname] / 2, 15), 
            "chunk_count": file_chunks[fname]
        })
        words = re.findall(r'\b[a-z]{4,}\b', text.lower())
        words = [w for w in words if w not in stop_words]
        counts = Counter(words)
        top_words = [w for w, c in counts.most_common(8)]
        file_keywords[fname] = top_words
        
        for w in top_words:
            keyword_freq[w] = keyword_freq.get(w, 0) + counts[w]
            
    added_keywords = set()
    for fname, top_words in file_keywords.items():
        for w in top_words:
            if w not in added_keywords:
                nodes.append({
                    "id": w, 
                    "group": "keyword", 
                    "val": 4 + min(keyword_freq[w] / 1.5, 12), 
                    "frequency": keyword_freq[w]
                })
                added_keywords.add(w)
            links.append({"source": fname, "target": w})
            
    return {"nodes": nodes, "links": links}

# ── Health check ───────────────────────────────────────────────────────────
@app.get("/api/health")
async def health():
    return {"status": "ok", "services_ready": services.llm is not None}
