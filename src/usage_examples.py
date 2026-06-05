"""
RAG Pipeline - Usage Examples
==============================
Run this to see the loader + chunker working end-to-end.
"""

from document_loader import DocumentLoader, Document
from document_chunker import DocumentChunker, ChunkStrategy, ChunkPostProcessor


# ─────────────────────────────────────────────
#  Example 1: Load a single file
# ─────────────────────────────────────────────

def example_single_file():
    loader = DocumentLoader()

    # Works for: .pdf, .docx, .txt, .md, .csv, .json, .html, http URLs
    docs = loader.load("data/7.pdf")

    for doc in docs:
        print(f"Source : {doc.source}")
        print(f"Title  : {doc.title}")
        print(f"Pages  : {doc.total_pages}")
        print(f"Preview: {doc.content[:200]}")
        print()


# ─────────────────────────────────────────────
#  Example 2: Load a whole folder
# ─────────────────────────────────────────────

def example_load_directory():
    loader = DocumentLoader()

    docs = loader.load_directory(
        directory="./data",
        recursive=True,
        extensions=[".pdf", ".txt", ".md"],
        exclude_patterns=["*draft*", "*~*"],
    )
    print(f"Loaded {len(docs)} documents")
    return docs


# ─────────────────────────────────────────────
#  Example 3: Chunk with Recursive (default)
# ─────────────────────────────────────────────

def example_recursive_chunking(docs):
    chunker = DocumentChunker(
        chunk_size=512,
        chunk_overlap=64,
        strategy=ChunkStrategy.RECURSIVE,
    )
    chunks = chunker.chunk_documents(docs)

    for chunk in chunks[:3]:
        print(f"Chunk ID  : {chunk.chunk_id}")
        print(f"Citation  : {chunk.citation_string()}")
        print(f"Content   : {chunk.content[:150]}...")
        print()

    return chunks


# ─────────────────────────────────────────────
#  Example 4: Markdown-aware chunking
# ─────────────────────────────────────────────

def example_markdown_chunking():
    loader = DocumentLoader()
    docs = loader.load("README.md")

    chunker = DocumentChunker(
        chunk_size=800,
        chunk_overlap=100,
        strategy=ChunkStrategy.MARKDOWN,  # Splits on ## headers
    )
    chunks = chunker.chunk_documents(docs)
    print(f"Markdown chunks: {len(chunks)}")
    return chunks


# ─────────────────────────────────────────────
#  Example 5: Token-based chunking for LLMs
# ─────────────────────────────────────────────

def example_token_chunking(docs):
    chunker = DocumentChunker(
        chunk_size=256,         # 256 tokens per chunk
        chunk_overlap=32,       # 32 token overlap
        strategy=ChunkStrategy.TOKEN,
    )
    return chunker.chunk_documents(docs)


# ─────────────────────────────────────────────
#  Example 6: Full post-processing pipeline
# ─────────────────────────────────────────────

def example_postprocessing(chunks):
    processed_chunks = ChunkPostProcessor.run_pipeline(
        chunks,
        dedupe=True,            # Remove near-duplicates
        normalize=True,         # Clean whitespace
        length_filter=True,     # Drop noise (< 50 chars) and oversized (> 8000)
        context_prefix=True,    # Prepend [Source: ...] for LLM context
        min_len=50,
        max_len=8000,
    )
    print(f"After post-processing: {len(processed_chunks)} chunks")
    return processed_chunks


# ─────────────────────────────────────────────
#  Example 7: Convert to dict for vector DB ingestion
# ─────────────────────────────────────────────

def example_to_vector_db_format(chunks):
    """
    Returns a list of dicts ready for Pinecone, Weaviate, Chroma, Qdrant, etc.
    You just need to add the 'embedding' field from your embedding model.
    """
    records = []
    for chunk in chunks:
        record = chunk.to_dict()
        # record["embedding"] = your_embedding_model.encode(chunk.content)
        records.append(record)

    print(f"Ready to upsert {len(records)} records into vector DB")
    return records


# ─────────────────────────────────────────────
#  Quick demo with synthetic data
# ─────────────────────────────────────────────

def demo_with_synthetic_data():
    """
    No files needed — tests the pipeline with a synthetic document.
    """
    from document_loader import Document

    synthetic_doc = Document(
        content="""
        Introduction to Neural Networks

        Neural networks are computational models inspired by the human brain.
        They consist of layers of interconnected nodes, called neurons.

        ## Architecture

        A typical neural network has three types of layers:
        - Input layer: receives raw data
        - Hidden layers: transform the data through learned weights
        - Output layer: produces the final prediction

        ## Training

        Training involves adjusting weights using backpropagation and gradient descent.
        The loss function measures prediction error, and the optimizer minimizes it.
        Common optimizers include Adam, SGD, and RMSprop.

        ## Applications

        Neural networks power image recognition, natural language processing,
        speech synthesis, and many other AI applications used today.
        """,
        source="synthetic://neural_networks_intro",
        file_type="txt",
        title="Introduction to Neural Networks",
    )

    # Chunk it
    chunker = DocumentChunker(
        chunk_size=300,
        chunk_overlap=50,
        strategy=ChunkStrategy.MARKDOWN,
    )
    chunks = chunker.chunk_document(synthetic_doc)

    # Post-process
    chunks = ChunkPostProcessor.run_pipeline(chunks, context_prefix=True)

    print(f"\n{'='*50}")
    print(f"Demo: {len(chunks)} chunks produced")
    print(f"{'='*50}\n")

    for i, chunk in enumerate(chunks):
        print(f"--- Chunk {i+1} ---")
        print(f"ID      : {chunk.chunk_id}")
        print(f"Citation: {chunk.citation_string()}")
        print(f"Content :\n{chunk.content}\n")


if __name__ == "__main__":
    #demo_with_synthetic_data()
    example_single_file()
    #example_load_directory()
