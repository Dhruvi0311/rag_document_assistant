import os
from typing import List, Dict, Any
import chromadb

class VectorStoreManager:
    def __init__(self, db_path: str = "chroma_db", distance_metric: str = "cosine"):
        """
        Initializes the local persistent ChromaDB client and creates/gets 
        a standard collection for our chatbot chunks.
        Allows setting the distance_metric parameter explicitly (e.g., 'cosine', 'l2', or 'ip').
        """
        self.db_path = db_path
        self.distance_metric = distance_metric
        
        # Initialize a persistent client (saves vectors directly to your disk)
        self.client = chromadb.PersistentClient(path=self.db_path)
        
        # Create or fetch the collection. 
        # By default, Chroma uses the 'all-MiniLM-L6-v2' HuggingFace model locally 
        # to generate 384-dimensional embeddings automatically.
        self.collection = self.client.get_or_create_collection(
            name="chatbot_docs",
            metadata={"hnsw:space": self.distance_metric} # Use specified distance metric
        )

    def upsert_chunks(self, chunks: List[Dict[str, Any]]):
        """
        Takes the final processed chunks array from your DocumentChunker,
        unpacks the payloads, and upserts them cleanly into ChromaDB.
        """
        if not chunks:
            print("⚠️ No chunks provided for vector storage database.")
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

        print(f"🔄 Syncing {len(documents)} vectors to local DB storage...")
        
        # Upsert adds new chunks or updates them if the chunk_id already exists (No duplicates!)
        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        print("✅ Vector database synchronization complete.")

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

    def get_all_indexed_filenames(self) -> List[str]:
        """
        Fetches all metadata from the collection, extracts unique file names, 
        and returns them as a sorted list for our UI Sidebar inventory display.
        """
        try:
            # Retrieve basic metadata fields from all records in the collection
            existing_data = self.collection.get(include=["metadatas"])
            if not existing_data or not existing_data["metadatas"]:
                return []
            
            # Extract unique file names using a set comprehension
            unique_files = {meta["file_name"] for meta in existing_data["metadatas"] if meta and "file_name" in meta}
            return sorted(list(unique_files))
        except Exception as e:
            print(f"⚠️ Could not pull active inventory filenames: {e}")
            return []

    def delete_file_from_index(self, file_name: str):
        """
        Deletes all chunks matching a specific file name from the database.
        Allows clean dynamic workspace resets from the frontend UI.
        """
        try:
            self.collection.delete(where={"file_name": file_name})
            print(f"🗑️ Cleaned out all vector chunks associated with file: {file_name}")
        except Exception as e:
            print(f"❌ Failed to drop file records for {file_name}: {e}")