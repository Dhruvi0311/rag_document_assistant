"""
RAG Pipeline - Document Chunker
=================================
Strategies: Recursive, Sentence-aware, Semantic, Token-based, Markdown
Features: Overlap, metadata inheritance, chunk IDs, deduplication
"""

import re
import hashlib
import logging
from enum import Enum
from typing import List, Optional, Dict, Any, Callable
from dataclasses import dataclass, field

from document_loader import Document

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
#  Chunk Data Model
# ─────────────────────────────────────────────

@dataclass
class Chunk:
    """
    A chunk is an atomic unit fed into the embedding + retrieval pipeline.
    Full citation metadata is preserved for every chunk.
    """
    content: str
    chunk_id: str = field(default="")

    # Source traceability (critical for citations)
    source: str = ""
    doc_id: str = ""
    chunk_index: int = 0
    total_chunks: int = 0

    # Position metadata for citations
    page_number: Optional[int] = None
    char_start: int = 0
    char_end: int = 0

    # Inherited document metadata
    title: Optional[str] = None
    author: Optional[str] = None
    file_type: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.chunk_id:
            self.chunk_id = self._generate_id()

    def _generate_id(self) -> str:
        raw = f"{self.doc_id}::{self.chunk_index}::{self.content[:100]}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "doc_id": self.doc_id,
            "source": self.source,
            "content": self.content,
            "chunk_index": self.chunk_index,
            "total_chunks": self.total_chunks,
            "page_number": self.page_number,
            "char_start": self.char_start,
            "char_end": self.char_end,
            "title": self.title,
            "author": self.author,
            "file_type": self.file_type,
            "metadata": self.metadata,
        }

    def citation_string(self) -> str:
        """Human-readable citation for UI display."""
        parts = [self.title or self.source]
        if self.page_number:
            parts.append(f"p.{self.page_number}")
        parts.append(f"chunk {self.chunk_index + 1}/{self.total_chunks}")
        return " · ".join(parts)


# ─────────────────────────────────────────────
#  Chunking Strategy Enum
# ─────────────────────────────────────────────

class ChunkStrategy(Enum):
    RECURSIVE   = "recursive"      # Best general-purpose (default)
    SENTENCE    = "sentence"       # Preserves sentence boundaries
    MARKDOWN    = "markdown"       # Splits on headers for structured docs
    TOKEN       = "token"          # Exact token-count control for LLMs
    SEMANTIC    = "semantic"       # Groups sentences by embedding similarity (advanced)
    FIXED       = "fixed"          # Simple character-count (baseline)


# ─────────────────────────────────────────────
#  Core Chunker
# ─────────────────────────────────────────────

class DocumentChunker:
    """
    Production-grade document chunker.

    Args:
        chunk_size:    Target chunk size in characters (or tokens if strategy=TOKEN)
        chunk_overlap: Overlap between consecutive chunks to preserve context
        strategy:      ChunkStrategy enum value
        min_chunk_size: Discard chunks smaller than this (noise filtering)
        length_fn:     Custom function to measure chunk length

    Usage:
        chunker = DocumentChunker(chunk_size=512, chunk_overlap=64)
        chunks  = chunker.chunk_documents(documents)
    """

    # Recursive separators (tried in order — most semantic to least)
    RECURSIVE_SEPARATORS = [
        "\n\n\n",    # Section breaks
        "\n\n",      # Paragraph breaks
        "\n",        # Line breaks
        ". ",        # Sentence ends
        "! ",
        "? ",
        "; ",
        ": ",
        ", ",
        " ",         # Word boundary
        "",          # Character (last resort)
    ]

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 64,
        strategy: ChunkStrategy = ChunkStrategy.RECURSIVE,
        min_chunk_size: int = 50,
        length_fn: Optional[Callable[[str], int]] = None,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.strategy = strategy
        self.min_chunk_size = min_chunk_size
        self.length_fn = length_fn or len

        # Validate config
        if chunk_overlap >= chunk_size:
            raise ValueError(f"chunk_overlap ({chunk_overlap}) must be < chunk_size ({chunk_size})")

    # ── Public API ─────────────────────────────

    def chunk_document(self, document: Document) -> List[Chunk]:
        """Chunk a single Document into Chunks."""
        text = document.content.strip()
        if not text:
            logger.warning(f"[Chunker] Empty document: {document.source}")
            return []

        # Dispatch to strategy
        strategy_fn = {
            ChunkStrategy.RECURSIVE: self._split_recursive,
            ChunkStrategy.SENTENCE:  self._split_sentences,
            ChunkStrategy.MARKDOWN:  self._split_markdown,
            ChunkStrategy.TOKEN:     self._split_by_tokens,
            ChunkStrategy.FIXED:     self._split_fixed,
            ChunkStrategy.SEMANTIC:  self._split_semantic,
        }[self.strategy]

        raw_chunks = strategy_fn(text)

        # Filter noise
        raw_chunks = [c for c in raw_chunks if self.length_fn(c.strip()) >= self.min_chunk_size]

        # Build Chunk objects with metadata
        chunks = self._build_chunks(raw_chunks, document)

        logger.info(
            f"[Chunker] '{document.source}' → {len(chunks)} chunks "
            f"(strategy={self.strategy.value}, size={self.chunk_size})"
        )
        return chunks

    def chunk_documents(self, documents: List[Document]) -> List[Chunk]:
        """Chunk a list of Documents."""
        all_chunks = []
        for doc in documents:
            chunks = self.chunk_document(doc)
            all_chunks.extend(chunks)

        logger.info(f"[Chunker] Total chunks: {len(all_chunks)} from {len(documents)} documents")
        return all_chunks

    # ── Strategies ─────────────────────────────

    def _split_recursive(self, text: str, separators: Optional[List[str]] = None) -> List[str]:
        """
        Recursively splits using a hierarchy of separators.
        Best general-purpose strategy — respects semantic structure.
        """
        separators = separators or self.RECURSIVE_SEPARATORS
        sep = separators[0]
        remaining_seps = separators[1:]

        splits = text.split(sep) if sep else list(text)
        splits = [s for s in splits if s]

        good_chunks: List[str] = []
        current_chunk = ""

        for split in splits:
            test = (current_chunk + sep + split).strip() if current_chunk else split.strip()

            if self.length_fn(test) <= self.chunk_size:
                current_chunk = test
            else:
                # Save current chunk
                if current_chunk:
                    good_chunks.append(current_chunk)

                # If the split itself is too large, recurse with next separator
                if self.length_fn(split) > self.chunk_size and remaining_seps:
                    sub_chunks = self._split_recursive(split, remaining_seps)
                    good_chunks.extend(sub_chunks)
                    current_chunk = ""
                else:
                    # Start new chunk with overlap
                    overlap = self._get_overlap_text(current_chunk)
                    current_chunk = (overlap + " " + split).strip() if overlap else split.strip()

        if current_chunk:
            good_chunks.append(current_chunk)

        return good_chunks

    def _split_sentences(self, text: str) -> List[str]:
        """
        Sentence-aware chunking. Fills a window up to chunk_size,
        then starts a new chunk with sentence-level overlap.
        """
        # Sentence tokenizer (no NLTK required)
        sentence_endings = re.compile(r'(?<=[.!?])\s+(?=[A-Z])')
        sentences = sentence_endings.split(text)

        chunks: List[str] = []
        current: List[str] = []
        current_len = 0

        for sentence in sentences:
            sentence = sentence.strip()
            slen = self.length_fn(sentence)

            if current_len + slen > self.chunk_size and current:
                chunks.append(" ".join(current))
                # Overlap: keep last N sentences that fit within overlap limit
                overlap_sentences: List[str] = []
                overlap_len = 0
                for s in reversed(current):
                    if overlap_len + self.length_fn(s) <= self.chunk_overlap:
                        overlap_sentences.insert(0, s)
                        overlap_len += self.length_fn(s)
                    else:
                        break
                current = overlap_sentences
                current_len = overlap_len

            current.append(sentence)
            current_len += slen

        if current:
            chunks.append(" ".join(current))

        return chunks

    def _split_markdown(self, text: str) -> List[str]:
        """
        Splits on Markdown headers (##, ###), then recursively splits
        large sections. Preserves section context by prepending the header.
        """
        header_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
        matches = list(header_pattern.finditer(text))

        if not matches:
            return self._split_recursive(text)

        sections: List[str] = []
        for i, match in enumerate(matches):
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            section = text[start:end].strip()
            sections.append(section)

        # Pre-text before first header
        if matches[0].start() > 0:
            pre = text[:matches[0].start()].strip()
            if pre:
                sections.insert(0, pre)

        chunks: List[str] = []
        for section in sections:
            if self.length_fn(section) <= self.chunk_size:
                chunks.append(section)
            else:
                # Extract header line to prepend as context
                lines = section.splitlines()
                header_line = lines[0] if lines else ""
                body = "\n".join(lines[1:]).strip()

                sub_chunks = self._split_recursive(body)
                for sub in sub_chunks:
                    chunks.append(f"{header_line}\n{sub}")

        return chunks

    def _split_by_tokens(self, text: str) -> List[str]:
        """
        Token-aware chunking using tiktoken (OpenAI tokenizer).
        Falls back to character-based estimation if tiktoken not installed.
        Requires: pip install tiktoken
        """
        try:
            import tiktoken
            enc = tiktoken.get_encoding("cl100k_base")

            tokens = enc.encode(text)
            chunks: List[str] = []

            step = self.chunk_size - self.chunk_overlap
            for i in range(0, len(tokens), step):
                window = tokens[i:i + self.chunk_size]
                chunk_text = enc.decode(window)
                chunks.append(chunk_text)

            return chunks

        except ImportError:
            logger.warning("[Chunker] tiktoken not found — falling back to char-based (÷4 estimate)")
            # Rough approximation: 1 token ≈ 4 characters
            char_size = self.chunk_size * 4
            char_overlap = self.chunk_overlap * 4
            original_size, original_overlap = self.chunk_size, self.chunk_overlap
            self.chunk_size, self.chunk_overlap = char_size, char_overlap
            result = self._split_recursive(text)
            self.chunk_size, self.chunk_overlap = original_size, original_overlap
            return result

    def _split_fixed(self, text: str) -> List[str]:
        """
        Simple fixed-size character chunking with overlap.
        Fast baseline — no structure awareness.
        """
        chunks: List[str] = []
        step = self.chunk_size - self.chunk_overlap

        for i in range(0, len(text), step):
            chunk = text[i:i + self.chunk_size]
            chunks.append(chunk)

        return chunks

    def _split_semantic(self, text: str) -> List[str]:
        """
        Semantic chunking: groups sentences that are semantically similar.
        Requires: pip install sentence-transformers numpy
        Falls back to sentence splitting if dependencies missing.
        """
        try:
            import numpy as np
            from sentence_transformers import SentenceTransformer

            sentence_endings = re.compile(r'(?<=[.!?])\s+')
            sentences = [s.strip() for s in sentence_endings.split(text) if s.strip()]

            if len(sentences) < 3:
                return self._split_sentences(text)

            model = SentenceTransformer("all-MiniLM-L6-v2")
            embeddings = model.encode(sentences)

            # Compute cosine similarity between consecutive sentences
            def cosine_sim(a, b):
                return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10)

            similarities = [cosine_sim(embeddings[i], embeddings[i + 1])
                            for i in range(len(embeddings) - 1)]

            # Find breakpoints where similarity drops (semantic shift)
            threshold = np.percentile(similarities, 25)  # Bottom 25% = topic change

            chunks: List[str] = []
            current: List[str] = [sentences[0]]

            for i, sim in enumerate(similarities):
                if sim < threshold and self.length_fn(" ".join(current)) >= self.min_chunk_size:
                    chunks.append(" ".join(current))
                    # Add overlap
                    overlap = current[-2:] if len(current) >= 2 else current[-1:]
                    current = overlap + [sentences[i + 1]]
                else:
                    current.append(sentences[i + 1])

                # Force split if chunk is too large
                if self.length_fn(" ".join(current)) > self.chunk_size:
                    chunks.append(" ".join(current))
                    current = [sentences[i + 1]]

            if current:
                chunks.append(" ".join(current))

            return chunks

        except ImportError:
            logger.warning("[Chunker] sentence-transformers not found — falling back to sentence split")
            return self._split_sentences(text)

    # ── Helpers ────────────────────────────────

    def _get_overlap_text(self, text: str) -> str:
        """Extract the last `chunk_overlap` characters of text for overlap."""
        if not text or self.chunk_overlap == 0:
            return ""
        return text[-self.chunk_overlap:].strip()

    def _build_chunks(self, raw_chunks: List[str], document: Document) -> List[Chunk]:
        """Attach document metadata to each raw text chunk."""
        chunks: List[Chunk] = []
        total = len(raw_chunks)
        cursor = 0

        for idx, text in enumerate(raw_chunks):
            # Find approximate char position in original document
            char_start = document.content.find(text[:40], cursor)
            char_start = max(char_start, cursor) if char_start != -1 else cursor
            char_end = char_start + len(text)
            cursor = char_end

            chunk = Chunk(
                content=text.strip(),
                source=document.source,
                doc_id=document.doc_id,
                chunk_index=idx,
                total_chunks=total,
                page_number=document.page_number,
                char_start=char_start,
                char_end=char_end,
                title=document.title,
                author=document.author,
                file_type=document.file_type,
                metadata={
                    **document.metadata,
                    "chunk_strategy": self.strategy.value,
                    "chunk_size_target": self.chunk_size,
                    "chunk_overlap": self.chunk_overlap,
                },
            )
            chunks.append(chunk)

        return chunks


# ─────────────────────────────────────────────
#  Chunk Post-Processors
# ─────────────────────────────────────────────

class ChunkPostProcessor:
    """
    Optional post-processing pipeline for chunks before embedding.
    Reduces noise, deduplicates, and improves retrieval quality.
    """

    @staticmethod
    def deduplicate(chunks: List[Chunk]) -> List[Chunk]:
        """Remove near-duplicate chunks using content hash."""
        seen: Dict[str, bool] = {}
        unique: List[Chunk] = []
        for chunk in chunks:
            key = hashlib.md5(chunk.content.encode()).hexdigest()
            if key not in seen:
                seen[key] = True
                unique.append(chunk)
        removed = len(chunks) - len(unique)
        if removed:
            logger.info(f"[PostProcessor] Removed {removed} duplicate chunks")
        return unique

    @staticmethod
    def normalize_whitespace(chunks: List[Chunk]) -> List[Chunk]:
        """Collapse excessive whitespace in chunk content."""
        for chunk in chunks:
            chunk.content = re.sub(r'\s+', ' ', chunk.content).strip()
        return chunks

    @staticmethod
    def filter_by_length(chunks: List[Chunk], min_len: int = 50, max_len: int = 10000) -> List[Chunk]:
        """Remove chunks that are too short (noise) or too long (retrieval quality)."""
        before = len(chunks)
        chunks = [c for c in chunks if min_len <= len(c.content) <= max_len]
        logger.info(f"[PostProcessor] Length filter: {before} → {len(chunks)} chunks")
        return chunks

    @staticmethod
    def add_context_prefix(chunks: List[Chunk]) -> List[Chunk]:
        """
        Prepend document title/source to each chunk for better retrieval context.
        Helps the LLM understand where information comes from during generation.
        """
        for chunk in chunks:
            prefix = f"[Source: {chunk.title or chunk.source}]"
            if chunk.page_number:
                prefix += f" [Page {chunk.page_number}]"
            chunk.content = f"{prefix}\n{chunk.content}"
        return chunks

    @classmethod
    def run_pipeline(
        cls,
        chunks: List[Chunk],
        dedupe: bool = True,
        normalize: bool = True,
        length_filter: bool = True,
        context_prefix: bool = False,
        min_len: int = 50,
        max_len: int = 8000,
    ) -> List[Chunk]:
        """Run a configurable post-processing pipeline."""
        if normalize:
            chunks = cls.normalize_whitespace(chunks)
        if dedupe:
            chunks = cls.deduplicate(chunks)
        if length_filter:
            chunks = cls.filter_by_length(chunks, min_len=min_len, max_len=max_len)
        if context_prefix:
            chunks = cls.add_context_prefix(chunks)
        return chunks
