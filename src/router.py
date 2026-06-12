import logging
from typing import List
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

logger = logging.getLogger(__name__)

def route_intent(query: str, history: List, llm) -> str:
    """
    Classifies the user's intent into either DOCUMENT_SEARCH or GENERAL_CHAT.
    
    Args:
        query: The latest user question.
        history: The list of recent ChatMessages (memory buffer).
        llm: The ChatHuggingFace instance.
        
    Returns:
        "DOCUMENT_SEARCH" or "GENERAL_CHAT"
    """
    
    # Construct a lightweight prompt for classification
    system_prompt = """You are an intelligent routing agent for a document assistant chatbot.
Your job is to determine if the user's latest query requires searching the uploaded documents/context, or if it is just a general conversation/coding question.

OUTPUT STRICTLY ONE OF THESE TWO EXACT STRINGS (no other text, no markdown):
- DOCUMENT_SEARCH
- GENERAL_CHAT

Rules:
1. If the user says a simple greeting ("hi", "hello", "how are you") with no other topic, output GENERAL_CHAT.
2. If the user explicitly asks to ignore the documents, output GENERAL_CHAT.
3. FOR ALL OTHER QUERIES (including questions about technical concepts, acronyms like MST, coding questions, algorithms, or any general knowledge), you MUST assume it is related to the uploaded documents. ALWAYS output DOCUMENT_SEARCH.
4. If unsure, output DOCUMENT_SEARCH.
"""

    messages = [SystemMessage(content=system_prompt)]
    
    # Add a condensed version of the history to provide context for pronouns
    if history:
        history_str = "\n".join([f"{m.role}: {m.content}" for m in history])
        messages.append(HumanMessage(content=f"Recent conversation:\n{history_str}"))
        
    messages.append(HumanMessage(content=f"User's new query: {query}\n\nClassify intent now:"))

    try:
        response = llm.invoke(messages)
        content = response.content.strip().upper()
        
        # Parse the output
        if "DOCUMENT_SEARCH" in content:
            return "DOCUMENT_SEARCH"
        elif "GENERAL_CHAT" in content:
            return "GENERAL_CHAT"
        else:
            logger.warning(f"Router returned unexpected string: {content}. Defaulting to DOCUMENT_SEARCH.")
            return "DOCUMENT_SEARCH"
            
    except Exception as e:
        logger.error(f"Error in route_intent: {e}. Defaulting to DOCUMENT_SEARCH.")
        return "DOCUMENT_SEARCH"
