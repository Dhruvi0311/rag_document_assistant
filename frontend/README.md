# ARCHIVAL — RAG Document Intelligence System

A high-end document question-answering system. Hybrid semantic + keyword retrieval, cross-encoder reranking, query rewriting, streaming LLM responses with source citations. Wrapped in a Minimalist Monochrome UI.

---

## Architecture

```
rag-system/
├── backend/
│   ├── main.py              ← FastAPI server (2 endpoints)
│   ├── requirements.txt
│   ├── document_loader.py   ← your existing module
│   ├── document_chunker.py  ← your existing module
│   ├── vector_store.py      ← your existing module
│   ├── sparse_store.py      ← your existing module
│   ├── reranker.py          ← your existing module
│   └── query_rewriter.py    ← your existing module
└── frontend/
    ├── app/
    │   ├── layout.tsx
    │   ├── page.tsx          ← 12-column shell
    │   ├── globals.css       ← design system + noise texture
    │   ├── types.ts
    │   └── components/
    │       ├── Sidebar.tsx       ← file upload + active index
    │       ├── ChatArena.tsx     ← streaming chat
    │       └── CitationPanel.tsx ← expandable source badges
    ├── tailwind.config.ts    ← design tokens locked in
    ├── next.config.ts
    └── package.json
```

---

## Setup

### 1. Backend

Copy your RAG module files into `backend/`:

```bash
cp document_loader.py document_chunker.py vector_store.py \
   sparse_store.py reranker.py query_rewriter.py \
   backend/
```

Create a `.env` file in `backend/`:

```
HF_TOKEN=hf_your_token_here
```

Install dependencies and start the server:

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`.
Interactive docs: `http://localhost:8000/docs`

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

---

## API Reference

### `POST /api/upload`
Accepts multipart form data with one or more files.

```bash
curl -X POST http://localhost:8000/api/upload \
  -F "files=@document.pdf" \
  -F "files=@data.csv"
```

Response:
```json
{
  "status": "success",
  "indexed_files": ["document.pdf", "data.csv"],
  "total_chunks": 47,
  "rejected_files": []
}
```

### `POST /api/chat`
Returns a `text/event-stream` of SSE events.

```json
{ "query": "What is the power requirement?", "history": [], "top_k": 5, "rerank_threshold": 0.25 }
```

SSE event types:
- `{"type": "citation", "chunks": [...]}` — emitted first, before any tokens
- `{"type": "token", "text": "..."}` — streaming text
- `{"type": "done"}` — stream complete
- `{"type": "error", "message": "..."}` — retrieval or LLM error

### `GET /api/files`
Returns list of indexed file names.

### `DELETE /api/files/{file_name}`
Removes all chunks for a file from the index.

---

## Design System

**Minimalist Monochrome** — zero rounded corners, zero shadows, pure black/white.

| Role | Font | Usage |
|------|------|-------|
| Display | Playfair Display | User queries, headlines |
| Body | Source Serif 4 | Assistant responses |
| Labels | JetBrains Mono | Badges, metadata, UI chrome |

Depth is created via **color inversion** (hover = black bg / white text).  
Division is created via **thick 4px black borders**.  
Texture: SVG noise at 2.8% opacity on the body.

---

## Notes

- The streaming simulation runs at ~55 words/second. Replace with `.astream()` if your HuggingFace endpoint gains true streaming support.
- The `rerank_threshold` default (0.25 sigmoid probability) is intentionally permissive. Raise it to 0.5+ for stricter filtering.
- ChromaDB and the BM25 pickle are stored in `backend/chroma_db/`. Delete this directory to reset the index.
