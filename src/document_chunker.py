import hashlib
from typing import List, Dict, Any

class DocumentChunker:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initializes the chunker with a recursive character splitter for paragraphs/PDFs/TXT files.
        Tables and CSV rows bypass this to maintain their structural integrity.
        """
        try:
            from langchain_text_splitters import RecursiveCharacterTextSplitter
        except ImportError:
            print("⚠️ 'langchain-text-splitters' package not found. Run: pip install langchain-text-splitters")
            raise

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )

    def _generate_hash(self, content: str) -> str:
        """Generates a unique SHA-256 hash for a specific text chunk."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def process_chunk(self, text: str, source_metadata: Dict[str, Any], chunk_index: int) -> Dict[str, Any]:
        """
        Constructs a distinct child chunk with full traceability back to the document source.
        """
        chunk_hash = self._generate_hash(text)
        
        # Build strict traceability metadata
        chunk_metadata = source_metadata.copy()
        
        # Move the generic file-level chunk_hash to prevent confusion with the unique micro-chunk hash
        if "chunk_hash" in chunk_metadata:
            chunk_metadata["parent_source_hash"] = chunk_metadata.pop("chunk_hash")
            
        chunk_metadata.update({
            "chunk_id": f"{source_metadata['doc_id']}_c{chunk_index}_{chunk_hash[:8]}",
            "chunk_hash": chunk_hash,
            "chunk_index": chunk_index
        })
        
        return {
            "text": text,
            "metadata": chunk_metadata
        }

    def chunk_documents(self, loaded_documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Takes the output array from DocumentLoader.load_batch() and chunks them 
        based on their structural rules, completely avoiding duplication.
        """
        final_chunks = []
        seen_chunk_hashes = set()

        for doc in loaded_documents:
            text = doc["text"]
            meta = doc["metadata"]
            source_type = meta.get("source_type", "")
            sub_type = meta.get("sub_type", "")

            # --- STRUCTURAL STRATEGY ---
            # Bypass text-splitting for tabular CSV rows and structural Word Tables to keep rows/cells intact
            if source_type == "csv" or (source_type == "docx" and sub_type == "table"):
                if text.strip():
                    chunk_obj = self.process_chunk(text, meta, chunk_index=0)
                    h = chunk_obj["metadata"]["chunk_hash"]
                    if h not in seen_chunk_hashes:
                        seen_chunk_hashes.add(h)
                        final_chunks.append(chunk_obj)
            
            # --- SEMANTIC / PARAGRAPH STRATEGY ---
            # Split long articles, full OCR pages, Word paragraphs, or plain text file rows safely
            else:
                split_texts = self.text_splitter.split_text(text)
                for idx, split_text in enumerate(split_texts):
                    if split_text.strip():
                        chunk_obj = self.process_chunk(split_text, meta, chunk_index=idx)
                        h = chunk_obj["metadata"]["chunk_hash"]
                        
                        # Prevent duplicate identical sub-chunks from entering vector store
                        if h not in seen_chunk_hashes:
                            seen_chunk_hashes.add(h)
                            final_chunks.append(chunk_obj)

        print(f"✂️ Core Chunking complete. Generated {len(final_chunks)} unified semantic chunks.")
        return final_chunks