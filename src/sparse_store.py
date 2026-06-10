import os
import re
import pickle
from typing import List, Dict, Any
from rank_bm25 import BM25Okapi

class SparseStoreManager:
    def __init__(self, storage_path: str = "chroma_db/bm25_index.pkl"):
        """
        Initializes an in-memory BM25 index that persists to disk via serialized pickle blocks.
        """
        self.storage_path = storage_path
        self.index_dir = os.path.dirname(self.storage_path)
        
        # Ensure the underlying tracking folder exists
        if self.index_dir and not os.path.exists(self.index_dir):
            os.makedirs(self.index_dir)
            
        self.bm25 = None
        self.raw_chunks = [] # Keeps structural matching payloads in memory
        
        # Load an existing index automatically if it exists on disk
        self.load_index()

    def _tokenize(self, text: str) -> List[str]:
        """
        Standardizes text strings into lower-case alphanumeric token arrays.
        """
        clean_text = text.lower()
        # Extract word boundaries cleanly, dropping standalone symbols
        tokens = re.findall(r'\b\w+\b', clean_text)
        return tokens

    def index_chunks(self, chunks: List[Dict[str, Any]]):
        """
        Compiles and fits a fresh BM25 keyword dictionary across raw ingestion chunks.
        """
        if not chunks:
            return
            
        self.raw_chunks = chunks
        corpus_tokenized = [self._tokenize(chunk["text"]) for chunk in self.raw_chunks]
        
        # Fit the BM25 algorithm parameters across tokenized spaces
        self.bm25 = BM25Okapi(corpus_tokenized)
        self.save_index()
        print(f"✅ Sparse Engine fitted successfully with {len(chunks)} text items.")

    def search_keywords(self, query: str, top_k: int = 3, file_filter: str = None) -> List[Dict[str, Any]]:
        """
        Performs classic algorithmic keyword lookup over document chunk sets.
        """
        if self.bm25 is None or not self.raw_chunks:
            return []

        # Filter chunks by file name if a specific filter is passed
        filtered_chunks = self.raw_chunks
        if file_filter:
            filtered_chunks = [c for c in self.raw_chunks if c["metadata"].get("file_name") == file_filter]
            
        if not filtered_chunks:
            return []

        tokenized_query = self._tokenize(query)
        
        # If a file filter was applied, compile a smaller, transient BM25 space to ensure correct rankings
        if file_filter:
            temp_corpus = [self._tokenize(c["text"]) for c in filtered_chunks]
            temp_bm25 = BM25Okapi(temp_corpus)
            scores = temp_bm25.get_scores(tokenized_query)
        else:
            scores = self.bm25.get_scores(tokenized_query)

       # Map scores directly back to their target chunks
        scored_results = []
        for idx, chunk in enumerate(filtered_chunks):
            score = float(scores[idx])
            # Use != 0.0 instead of > 0.0
            # This allows mathematically negative scores (when corpus size is tiny) to pass,
            # while still dropping chunks that have absolutely 0 keyword matches.
            if score != 0.0:
                scored_results.append({
                    "id": chunk["metadata"].get("chunk_id", "sparse_unknown"),
                    "text": chunk["text"],
                    "metadata": chunk["metadata"],
                    "score": score
                })

        # Sort results by descending keyword frequency scores
        scored_results.sort(key=lambda x: x["score"], reverse=True)
        return scored_results[:top_k]

    def save_index(self):
        """Persists the sparse configuration components to disk using serialization."""
        try:
            with open(self.storage_path, "wb") as f:
                pickle.dump({"raw_chunks": self.raw_chunks, "bm25": self.bm25}, f)
        except Exception as e:
            print(f"⚠️ Failed to serialize sparse index file data: {e}")

    def load_index(self):
        """Loads a serialized sparse index file if it exists on disk."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "rb") as f:
                    data = pickle.load(f)
                    self.raw_chunks = data.get("raw_chunks", [])
                    self.bm25 = data.get("bm25", None)
                print("📂 Serialized BM25 keyword index loaded from disk repository.")
            except Exception as e:
                print(f"⚠️ Could not read storage index pickle data, starting fresh: {e}")