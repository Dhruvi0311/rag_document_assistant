import os
import glob
from document_loader import DocumentLoader
from document_chunker import DocumentChunker
from vector_store import VectorStoreManager

def test_chatbot_pipeline():
    TARGET_DIR = "test_files"
    if not os.path.exists(TARGET_DIR):
        os.makedirs(TARGET_DIR)
        print(f" Created empty folder '{TARGET_DIR}'. Drop your files there and rerun!")
        return

    files = glob.glob(os.path.join(TARGET_DIR, "*.*"))
    if not files:
        print(f" No test files found in '{TARGET_DIR}/'. Add some files to test.")
        return

    print(f"🔍 Found {len(files)} file(s). Initializing Pipeline Engines...")
    
    # 1. Initialize Engines
    loader = DocumentLoader()
    chunker = DocumentChunker(chunk_size=500, chunk_overlap=100)
    vdb = VectorStoreManager()

    print("\n--- 1. LOADING AND OCR RUN ---")
    raw_docs = loader.load_batch(files)

    print("\n--- 2. CHUNKING RUN ---")
    final_chatbot_chunks = chunker.chunk_documents(raw_docs)
    print(f" Successfully split documents into {len(final_chatbot_chunks)} chunks.")

    print("\n--- 3. VECTOR STORAGE SYSTEM RUN ---")
    vdb.upsert_chunks(final_chatbot_chunks)

    # Find unique files loaded
    successfully_loaded_files = list(set([doc["metadata"]["file_name"] for doc in raw_docs]))

    print("\n--- 4. PER-FILE DATABASE SEMANTIC SEARCH VERIFICATION ---")
    test_query = "What are the primary concepts, data structures, or systems mentioned?"
    print(f" Universal Query: '{test_query}'")
    
    # CRITICAL: Distance threshold setup. 
    # For Cosine/L2 distance: closer to 0.0 = perfect match, closer to 1.0 = completely unrelated.
    DISTANCE_THRESHOLD = 0.75 

    for file_name in successfully_loaded_files:
        print("\n" + "=" * 90)
        print(f" RETRIEVING TOP 3 CHUNKS FOR FILE: {file_name.upper()}")
        print("=" * 90)
        
        search_hits = vdb.search_similar_chunks(test_query, top_k=3, file_filter=file_name)
        
        if not search_hits:
            print("   No chunks found or indexed for this file.")
            continue
            
        for idx, hit in enumerate(search_hits):
            distance = hit['distance']
            source_type = hit['metadata'].get('source_type', 'N/A')
            
            # Determine location tag
            if 'page_number' in hit['metadata']:
                location = f"Page {hit['metadata']['page_number']}"
            elif 'row_index' in hit['metadata']:
                location = f"CSV Row {hit['metadata']['row_index']}"
            elif 'element_index' in hit['metadata']:
                location = f"Layout Element {hit['metadata']['element_index']}"
            else:
                location = "Unknown"

            # Check if the vector distance actually passes our semantic sanity test
            if distance <= DISTANCE_THRESHOLD:
                status_tag = f" STRONG MATCH"
            else:
                status_tag = f" POOR MATCH (Irrelevant Context)"

            print(f" [{status_tag}] #{idx + 1} (Distance: {distance:.4f}) | [Type: {source_type}] | [Location: {location}]")
            print(f"  Text Snippet: \"{hit['text'].strip()[:200]}...\"")
            print("-" * 90)

    print("\n Pipeline test complete! Visual verification indicators updated.")

if __name__ == "__main__":
    test_chatbot_pipeline()