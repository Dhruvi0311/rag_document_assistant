from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_huggingface import ChatHuggingFace

class QueryRewriter:
    def __init__(self, llm: ChatHuggingFace):
        """
        Initializes the Query Rewriter with our existing LangChain ChatHuggingFace model.
        """
        self.llm = llm
        self.system_instruction = (
            "You are an expert search query optimizer for a database retrieval system. "
            "Given the following conversation history and a new user follow-up question, "
            "rephrase the follow-up question into a STANDALONE, keyword-rich search query.\n\n"
            "CRITICAL RULES:\n"
            "1. Resolve all pronouns (it, its, they, that file, etc.) into explicit nouns mentioned in the history.\n"
            "2. Do NOT answer the question. Your ONLY output must be the optimized search phrase.\n"
            "3. If the question is already a standalone concept and doesn't need history, return it exactly as is.\n"
            "4. Do not include conversational filler like 'Here is the query:'."
        )

    def condense_query(self, user_message: str, chat_history: list) -> str:
        """
        Takes the current user message and the rolling chat history window.
        Returns a standalone query optimized for ChromaDB and BM25 search.
        """
        # If there is no history, the query is already as standalone as it can be
        if not chat_history:
            return user_message

        # Format the last few turns of history into a readable string context
        # (We only take the last 4 messages to save tokens and keep context relevant)
        history_str = ""
        for msg in chat_history[-4:]: 
            role = "User" if isinstance(msg, HumanMessage) else "Assistant"
            history_str += f"{role}: {msg.content}\n"

        # Construct the exact prompt for the rewriting task
        task_prompt = (
            f"Chat History:\n{history_str}\n"
            f"Follow-up Question: {user_message}\n\n"
            "Optimized Search Query:"
        )

        messages = [
            SystemMessage(content=self.system_instruction),
            HumanMessage(content=task_prompt)
        ]

        try:
            # Call the LLM to rewrite the query
            response = self.llm.invoke(messages)
            optimized_query = response.content.strip()
            
            # Clean up any accidental quotes the model might add
            optimized_query = optimized_query.strip('"').strip("'")
            
            print(f"🔄 Query Rewritten: '{user_message}' ──► '{optimized_query}'")
            return optimized_query
            
        except Exception as e:
            print(f"⚠️ Query Rewriter failed, falling back to original query. Error: {e}")
            return user_message