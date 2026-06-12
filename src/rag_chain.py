import json
import time
import asyncio
from typing import AsyncGenerator, List
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

async def rag_token_stream(
    query: str,
    history: List,
    top_k: int,
    rerank_threshold: float,
    services
) -> AsyncGenerator[str, None]:  
    """
    Core RAG streaming generator.
    Yields Server-Sent Event (SSE) lines so the frontend can consume
    token-by-token via EventSource / ReadableStream.
    """
    start_time = time.time()
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
        for rank, chunk in enumerate(fused, start=1):
            chunk["rrf_rank"] = rank
            
        gated = services.reranker.rerank_and_gate_chunks(optimized_query, fused, threshold=rerank_threshold)

        if not gated:
            yield sse({"type": "error", "message": "Retrieved chunks did not pass the relevance threshold."})
            return

        # 4. Emit citation metadata before tokens start flowing
        citations = []
        for final_rank, c in enumerate(gated[:5], start=1):
            rrf_rank = c.get("rrf_rank", 0)
            shift = rrf_rank - final_rank
            citations.append({
                "file_name": c["metadata"].get("file_name", "Unknown"),
                "chunk_id": c["metadata"].get("chunk_id", ""),
                "relevance_score": round(c.get("relevance_score", 0.0), 4),
                "vector_distance": round(c.get("distance", -1.0), 4) if c.get("distance") is not None else None,
                "rank_shift": shift,
                "text_preview": c["text"][:160].strip(),
                "full_text": c["text"],
                "page_number": c["metadata"].get("page_number"),
            })
        yield sse({"type": "citation", "chunks": citations})

        # 5. Build context block
        context_parts = []
        for i, chunk in enumerate(gated[:5], 1):
            fname = chunk["metadata"].get("file_name", "Unknown")
            context_parts.append(f"[Source {i} — {fname}]\n{chunk['text'].strip()}")
        context_block = "\n\n".join(context_parts)

        # 6. LLM streaming
        system_instruction = (
            "You are an advanced RAG Document Assistant. Use ONLY the retrieved context below "
            "to answer the user's question. Cite source numbers when referencing specific facts. "
            "If the context does not contain the answer, state clearly that it is not in the documents.\n\n"
            f"Retrieved Context:\n{context_block}"
        )

        messages = [
            SystemMessage(content=system_instruction),
        ]
        messages.extend(lc_history)
        messages.append(HumanMessage(content=query))

        response_obj = await asyncio.to_thread(services.llm.invoke, messages)
        full_text: str = response_obj.content.strip()

        # Emit token-by-token (word granularity for smooth UX)
        words = full_text.split(" ")
        for i, word in enumerate(words):
            chunk_text = word if i == len(words) - 1 else word + " "
            yield sse({"type": "token", "text": chunk_text})
            await asyncio.sleep(0.018)  # ~55 words/sec — feels natural

        latency_ms = int((time.time() - start_time) * 1000)
        yield sse({"type": "analytics", "data": {
            "latency_ms": latency_ms,
            "token_count": len(words),
            "dense_hits": len(dense_hits),
            "sparse_hits": len(sparse_hits),
        }})
        yield sse({"type": "done"})

    except Exception as exc:
        yield sse({"type": "error", "message": str(exc)})
