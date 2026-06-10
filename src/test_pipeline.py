import os
import sys
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace

# Import our architectural modules
from src.document_loader import DocumentLoader
from src.document_chunker import DocumentChunker
from src.vector_store import VectorStoreManager
from src.sparse_store import SparseStoreManager
from src.reranker import RerankerManager
from src.query_rewriter import QueryRewriter

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    END = '\033[0m'
    BOLD = '\033[1m'

def setup_antigravity_test_data():
    """Creates a temporary file to test the ingestion pipeline."""
    os.makedirs("test_files", exist_ok=True)
    file_path = os.path.join("test_files", "antigravity_specs.txt")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("The core component of the Project Daedalus antigravity engine is the inverse-tachyon matrix. "
                "To counteract Earth's local gravitational pull, this specific matrix requires a baseline power injection of 1.21 gigawatts. "
                "Warning: Never expose the matrix assembly to ionized water or severe catastrophic failure will occur.")
    print(f"{Colors.BLUE}➔ Created test file: {file_path}{Colors.END}")
    return [file_path]

def run_diagnostic():
    print(f"\n{Colors.BOLD}=== 🚀 STARTING ADVANCED RAG DIAGNOSTIC ENGINE ==={Colors.END}\n")
    
    # --- PHASE 0: LLM Setup ---
    load_dotenv()
    hf_token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACEHUB_ACCESS_TOKEN")
    if not hf_token:
        print(f"{Colors.RED}❌ FAILED: HF_TOKEN not found in environment. Rewriter will fail.{Colors.END}")
        sys.exit(1)
        
    os.environ["HUGGINGFACEHUB_ACCESS_TOKEN"] = hf_token
    base_llm = HuggingFaceEndpoint(repo_id="meta-llama/Meta-Llama-3-8B-Instruct", max_new_tokens=256, temperature=0.1)
    llm = ChatHuggingFace(llm=base_llm)

    test_files = setup_antigravity_test_data()

    # --- PHASE 1: INGESTION & CHUNKING ---
    try:
        print(f"\n{Colors.YELLOW}[TESTING PHASE 1: LOADER & CHUNKER]{Colors.END}")
        loader = DocumentLoader(target_dir="test_files")
        raw_docs = loader.load_batch(test_files)
        assert len(raw_docs) > 0, "Loader returned empty list."
        assert "metadata" in raw_docs[0], "Loader missing 'metadata' dict."
        
        chunker = DocumentChunker(chunk_size=500, chunk_overlap=100)
        chunks = chunker.chunk_documents(raw_docs)
        assert len(chunks) > 0, "Chunker returned empty list."
        assert "chunk_id" in chunks[0]["metadata"], "Chunker failed to assign 'chunk_id'."
        print(f"{Colors.GREEN}✅ PASSED: Data ingested and cryptographically chunked.{Colors.END}")
    except Exception as e:
        print(f"{Colors.RED}❌ PHASE 1 FAILED: {e}{Colors.END}")
        return

    # --- PHASE 2: DUAL INDEXING ---
    try:
        print(f"\n{Colors.YELLOW}[TESTING PHASE 2: DUAL INDEXING]{Colors.END}")
        vdb = VectorStoreManager(db_path="chroma_db", distance_metric="cosine")
        sparse_db = SparseStoreManager(storage_path="chroma_db/bm25_index.pkl")
        
        vdb.upsert_chunks(chunks)
        sparse_db.index_chunks(chunks)
        print(f"{Colors.GREEN}✅ PASSED: Vectors and BM25 Tokens saved to disk/memory.{Colors.END}")
    except Exception as e:
        print(f"{Colors.RED}❌ PHASE 2 FAILED: {e}{Colors.END}")
        return

    # --- PHASE 3: QUERY REWRITING ---
    try:
        print(f"\n{Colors.YELLOW}[TESTING PHASE 3: QUERY REWRITING (MEMORY)]{Colors.END}")
        rewriter = QueryRewriter(llm=llm)
        
        # Simulating a user asking a vague question using a pronoun ("it")
        chat_history = [
            HumanMessage(content="Tell me about the Project Daedalus antigravity engine."),
            AIMessage(content="It is an advanced propulsion system relying on an inverse-tachyon matrix.")
        ]
        raw_user_query = "How much power does it require?"
        print(f"   Raw User Query: '{raw_user_query}'")
        
        optimized_query = rewriter.condense_query(raw_user_query, chat_history)
        print(f"   Optimized Search Query: '{optimized_query}'")
        
        assert "power" in optimized_query.lower(), "Rewriter lost the core intent."
        assert len(optimized_query) > len(raw_user_query), "Rewriter likely failed to append historical context."
        print(f"{Colors.GREEN}✅ PASSED: Query contextualized successfully.{Colors.END}")
    except Exception as e:
        print(f"{Colors.RED}❌ PHASE 3 FAILED: {e}{Colors.END}")
        return

    # --- PHASE 4: PARALLEL RETRIEVAL ---
    try:
        print(f"\n{Colors.YELLOW}[TESTING PHASE 4: HYBRID SEARCH]{Colors.END}")
        dense_hits = vdb.search_similar_chunks(optimized_query, top_k=3)
        sparse_hits = sparse_db.search_keywords(optimized_query, top_k=3)
        
        print(f"   Dense Engine found {len(dense_hits)} chunks.")
        print(f"   Sparse Engine found {len(sparse_hits)} chunks.")
        assert len(dense_hits) > 0, "ChromaDB failed to return results."
        assert len(sparse_hits) > 0, "BM25 failed to return results."
        print(f"{Colors.GREEN}✅ PASSED: Parallel retrieval engines operational.{Colors.END}")
    except Exception as e:
        print(f"{Colors.RED}❌ PHASE 4 FAILED: {e}{Colors.END}")
        return

    # --- PHASE 5: FUSION & RERANKING ---
    try:
        print(f"\n{Colors.YELLOW}[TESTING PHASE 5: RRF & CROSS-ENCODER]{Colors.END}")
        reranker = RerankerManager(model_name="BAAI/bge-reranker-base")
        
        fused_chunks = reranker.reciprocal_rank_fusion(dense_hits, sparse_hits)
        assert len(fused_chunks) <= (len(dense_hits) + len(sparse_hits)), "RRF Math failed to deduplicate."
        print(f"   RRF Algorithm merged hits into {len(fused_chunks)} unique chunks.")
        
        # Testing with a low threshold just to ensure the model outputs scores correctly
        final_gated_chunks = reranker.rerank_and_gate_chunks(optimized_query, fused_chunks, threshold=0.01)
        
        assert len(final_gated_chunks) > 0, "No chunks passed the AI threshold gate."
        assert "relevance_score" in final_gated_chunks[0], "Cross-Encoder failed to assign 'relevance_score'."
        
        best_chunk = final_gated_chunks[0]
        print(f"{Colors.GREEN}✅ PASSED: Final chunk verified with Score: {best_chunk['relevance_score']:.4f}{Colors.END}")
    except Exception as e:
        print(f"{Colors.RED}❌ PHASE 5 FAILED: {e}{Colors.END}")
        return

    # --- FINAL VALIDATION ---
    print(f"\n{Colors.BOLD}{Colors.GREEN}========================================================{Colors.END}")
    print(f"{Colors.BOLD}{Colors.GREEN}🏆 ALL SYSTEMS NOMINAL. PIPELINE FLOW IS PERFECT.{Colors.END}")
    print(f"{Colors.BOLD}{Colors.GREEN}========================================================{Colors.END}")
    print(f"\n{Colors.BLUE}Best Extracted Fact:{Colors.END} {best_chunk['text']}\n")

if __name__ == "__main__":
    run_diagnostic()