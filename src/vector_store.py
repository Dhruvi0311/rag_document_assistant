import os
from typing import List, Dict, Any
import chromadb
from chromadb.config import Settings

class VectorStoreManager:
    def __init__(self, db_path: str = "chroma_db"):
        """
        Initializes the local persistent ChromaDB client and creates/gets 
        a standard collection for our chatbot chunks.
        """
        self.db_path = db_path
        
        # Initialize a persistent client (saves vectors directly to your disk)
        self.client = chromadb.PersistentClient(path=self.db_path)
        
        # Create or fetch the collection. 
        # By default, Chroma uses the 'all-MiniLM-L6-v2' HuggingFace model locally 
        # to generate 384-dimensional embeddings automatically.
        self.collection = self.client.get_or_create_collection(
            name="chatbot_docs",
            metadata={"hnsw:space": "cosine"} # Use cosine similarity for semantic matching
        )

    def upsert_chunks(self, chunks: List[Dict[str, Any]]):
        """
        Takes the final processed chunks array from your DocumentChunker,
        unpacks the payloads, and upserts them cleanly into ChromaDB.
        """
        if not chunks:
            print(" No chunks provided for vector storage database.")
            return

        ids = []
        documents = []
        metadatas = []

        for chunk in chunks:
            # Extract unique ID, text, and tracing metadata
            ids.append(chunk["metadata"]["chunk_id"])
            documents.append(chunk["text"])
            
            # ChromaDB metadatas can only store primitive types (str, int, float, bool).
            # Our tracking dictionaries are already perfectly flattened primitives.  
            metadatas.append(chunk["metadata"])

        print(f" Syncing {len(documents)} vectors to local DB storage...")
        
        # Upsert adds new chunks or updates them if the chunk_id already exists (No duplicates!)
        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        print(" Vector database synchronization complete.")

    def search_similar_chunks(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Queries the database for semantically similar context chunks 
        to feed directly to the Chatbot LLM.
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k
        )

        # Reformat Chroma's nested response structure into a clean, easy-to-read list 
        formatted_results = []
        if results and results["ids"] and results["ids"][0]:
            for i in range(len(results["ids"][0])):
                formatted_results.append({
                    "id": results["ids"][0][i],
                    "text": results["documents"][0][i], 
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i] if "distances" in results else None
                })
        return formatted_results
    def search_similar_chunks(self, query: str, top_k: int = 3, file_filter: str = None) -> List[Dict[str, Any]]:
        """
        Queries the database for semantically similar context chunks.
        Allows filtering by a specific file name if provided.
        """
        # Set up metadata filtering if a specific file is requested
        where_clause = {"file_name": file_filter} if file_filter else None

        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            where=where_clause # Pass the metadata filter to Chroma
        )

        formatted_results = []
        if results and results["ids"] and results["ids"][0]:
            for i in range(len(results["ids"][0])):
                formatted_results.append({
                    "id": results["ids"][0][i],
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i] if "distances" in results else None
                })
        return formatted_results