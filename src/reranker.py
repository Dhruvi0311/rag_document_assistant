import math
from typing import List, Dict, Any
from sentence_transformers import CrossEncoder

class RerankerManager:
    def __init__(self, model_name: str = "BAAI/bge-reranker-base"):
        """
        Initializes the Cross-Encoder model.
        """
        self.model = CrossEncoder(model_name)

    def reciprocal_rank_fusion(self, dense_hits: List[Dict[str, Any]], sparse_hits: List[Dict[str, Any]], k: int = 60) -> List[Dict[str, Any]]:
        """
        Merges dense and sparse hits using the Reciprocal Rank Fusion (RRF) formula.
        """
        rrf_scores = {}
        chunk_map = {}
        
        # Score dense hits
        for rank, hit in enumerate(dense_hits, start=1):
            chunk_id = hit["id"]
            chunk_map[chunk_id] = hit
            rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + (1.0 / (k + rank))
            
        # Score sparse hits
        for rank, hit in enumerate(sparse_hits, start=1):
            chunk_id = hit["id"]
            chunk_map[chunk_id] = hit
            rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + (1.0 / (k + rank))
            
        # Sort by fusion score descending
        sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
        
        fused_results = []
        for cid in sorted_ids:
            chunk = chunk_map[cid].copy()
            chunk["rrf_score"] = rrf_scores[cid]
            fused_results.append(chunk)
            
        return fused_results

    def rerank_and_gate_chunks(self, query: str, chunks: List[Dict[str, Any]], threshold: float = 0.75) -> List[Dict[str, Any]]:
        """
        Reranks chunks using the Cross-Encoder model against the query, 
        applies a sigmoid to the raw logit scores, and filters out chunks below the threshold.
        """
        if not chunks:
            return []
            
        pairs = [[query, chunk["text"]] for chunk in chunks]
        scores = self.model.predict(pairs)
        
        # Predict returns a single float if there's only one pair
        if isinstance(scores, (int, float)):
            scores = [scores]
            
        gated_results = []
        for idx, chunk in enumerate(chunks):
            logit_score = float(scores[idx])
            # Sigmoid activation to normalize to [0, 1] range
            prob_score = 1.0 / (1.0 + math.exp(-logit_score))
            
            if prob_score >= threshold:
                updated_chunk = chunk.copy()
                updated_chunk["relevance_score"] = prob_score
                gated_results.append(updated_chunk)
                
        # Sort by relevance score descending
        gated_results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return gated_results
