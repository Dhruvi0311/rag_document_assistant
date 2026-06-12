import json
import time
import asyncio
from typing import AsyncGenerator, List
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

async def general_chat_stream(
    query: str,
    history: List,
    llm
) -> AsyncGenerator[str, None]:
    """
    General chat streaming generator bypassing the vector database.
    Yields Server-Sent Event (SSE) lines so the frontend can consume
    token-by-token.
    """
    start_time = time.time()

    def sse(payload: dict) -> str:
        return f"data: {json.dumps(payload)}\n\n"

    try:
        # Convert history
        lc_history = []
        for m in history:
            if m.role == "user":
                lc_history.append(HumanMessage(content=m.content))
            else:
                lc_history.append(AIMessage(content=m.content))

        system_instruction = (
            "You are a helpful AI assistant. Answer the user's questions in a friendly, conversational manner. "
            "You have access to their recent conversation history for context."
        )

        messages = [SystemMessage(content=system_instruction)]
        messages.extend(lc_history)
        messages.append(HumanMessage(content=query))

        response_obj = await asyncio.to_thread(llm.invoke, messages)
        full_text: str = response_obj.content.strip()

        # Emit token-by-token (word granularity for smooth UX)
        words = full_text.split(" ")
        token_count = len(words)
        for i, word in enumerate(words):
            chunk_text = word if i == len(words) - 1 else word + " "
            yield sse({"type": "token", "text": chunk_text})
            await asyncio.sleep(0.01) # Small delay to simulate streaming

        # Emit the analytics payload with zero retrieval hits so the UI doesn't break
        latency = int((time.time() - start_time) * 1000)
        yield sse({
            "type": "analytics",
            "data": {
                "dense_hits": 0,
                "sparse_hits": 0,
                "rerank_pool": 0,
                "token_count": token_count,
                "latency_ms": latency,
            }
        })

        yield sse({"type": "done"})

    except Exception as e:
        yield sse({"type": "error", "message": f"Error in general chat: {str(e)}"})
