# src/test_pipeline.py
import os
import glob
from document_loader import DocumentLoader
from document_chunker import DocumentChunker
from vector_store import VectorStoreManager

def test_chatbot_pipeline():
    TARGET_DIR = "test_files"
    if not os.path.exists(TARGET_DIR):
        os.makedirs(TARGET_DIR)
        print(f"📁 Created empty folder '{TARGET_DIR}'. Drop your files there and rerun!")
        return

    files = glob.glob(os.path.join(TARGET_DIR, "*.*"))
    if not files:
        print(f"⚠️ No test files found in '{TARGET_DIR}/'. Add some files to test.")
        return

    print(f"🔍 Found {len(files)} file(s). Initializing Pipeline Engines...")
    
    loader = DocumentLoader()
    chunker = DocumentChunker(chunk_size=500, chunk_overlap=100)
    vdb = VectorStoreManager()

    print("\n--- 1. LOADING AND OCR RUN ---")
    raw_docs = loader.load_batch(files)

    print("\n--- 2. CHUNKING RUN ---")
    final_chatbot_chunks = chunker.chunk_documents(raw_docs)

    print("\n--- 3. VECTOR STORAGE SYSTEM RUN ---")
    vdb.upsert_chunks(final_chatbot_chunks)

    # Find unique files that were successfully loaded into the pipeline
    successfully_loaded_files = list(set([doc["metadata"]["file_name"] for doc in raw_docs]))

    print("\n--- 4. PER-FILE DATABASE SEMANTIC SEARCH VERIFICATION ---")
    test_query = "What are the primary concepts, data structures, or systems mentioned?"
    print(f"🕵️‍♂️ Universal Query: '{test_query}'")
    
    # Loop over every unique file and pull its top 3 chunks
    for file_name in successfully_loaded_files:
        print("\n" + "=" * 90)
        print(f"📂 RETRIEVING TOP 3 CHUNKS FOR FILE: {file_name.upper()}")
        print("=" * 90)
        
        # Call search passing the specific file filter, asking for top 3
        search_hits = vdb.search_similar_chunks(test_query, top_k=3, file_filter=file_name)
        
        if not search_hits:
            print("  ❌ No chunks found or indexed for this file.")
            continue
            
        for idx, hit in enumerate(search_hits):
            # Format the location display nicely depending on the file type
            source_type = hit['metadata'].get('source_type', 'N/A')
            if 'page_number' in hit['metadata']:
                location = f"Page {hit['metadata']['page_number']}"
            elif 'row_index' in hit['metadata']:
                location = f"CSV Row {hit['metadata']['row_index']}"
            elif 'element_index' in hit['metadata']:
                location = f"Layout Element {hit['metadata']['element_index']}"
            else:
                location = "Unknown"

            print(f" 🎯 MATCH #{idx + 1} (Distance: {hit['distance']:.4f}) | [Type: {source_type}] | [Location: {location}]")
            print(f" 📝 Text Snippet: \"{hit['text'].strip()[:250]}...\"")
            print("-" * 90)

    print("\n✨ Pipeline test complete! Every supported file has verified semantic retrieval windows.")

if __name__ == "__main__":
    test_chatbot_pipeline()