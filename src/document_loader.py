"""
RAG Pipeline - Document Loader
================================
Supports: PDF, DOCX, TXT, Markdown, HTML, CSV, JSON, URLs
Features: Metadata extraction, error handling, source tracking
"""

import os
import re
import json
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Iterator
from abc import ABC, abstractmethod

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
#  Core Data Models
# ─────────────────────────────────────────────

@dataclass
class Document:
    """
    Core document unit with full metadata for citation and traceability.
    Every chunk will inherit from this document.
    """
    content: str
    source: str                          # File path or URL
    doc_id: str = field(default="")      # SHA256 of content+source
    page_number: Optional[int] = None
    total_pages: Optional[int] = None
    file_type: str = ""
    title: Optional[str] = None
    author: Optional[str] = None
    created_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.doc_id:
            self.doc_id = self._generate_id()

    def _generate_id(self) -> str:
        """Generate a deterministic SHA256 ID for deduplication."""
        raw = f"{self.source}::{self.content[:200]}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "source": self.source,
            "content": self.content,
            "page_number": self.page_number,
            "total_pages": self.total_pages,
            "file_type": self.file_type,
            "title": self.title,
            "author": self.author,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }


# ─────────────────────────────────────────────
#  Base Loader Interface
# ─────────────────────────────────────────────

class BaseLoader(ABC):
    """Abstract base class for all document loaders."""

    @abstractmethod
    def load(self, source: str) -> List[Document]:
        """Load documents from a source. Returns list of Document objects."""
        pass

    @abstractmethod
    def supports(self, source: str) -> bool:
        """Return True if this loader handles the given source."""
        pass

    def _get_file_metadata(self, path: str) -> Dict[str, Any]:
        """Extract common file system metadata."""
        p = Path(path)
        stat = p.stat() if p.exists() else None
        return {
            "file_name": p.name,
            "file_size_bytes": stat.st_size if stat else None,
            "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat() if stat else None,
            "absolute_path": str(p.resolve()),
        }


# ─────────────────────────────────────────────
#  Concrete Loaders
# ─────────────────────────────────────────────

class TextLoader(BaseLoader):
    """Loads plain .txt and .md files."""

    SUPPORTED = {".txt", ".md", ".rst"}

    def supports(self, source: str) -> bool:
        return Path(source).suffix.lower() in self.SUPPORTED

    def load(self, source: str) -> List[Document]:
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {source}")

        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        doc = Document(
            content=content.strip(),
            source=str(path),
            file_type=path.suffix.lstrip("."),
            title=path.stem,
            metadata=self._get_file_metadata(source),
        )
        logger.info(f"[TextLoader] Loaded: {path.name} ({len(content)} chars)")
        return [doc]


class PDFLoader(BaseLoader):
    """
    Loads PDF files with per-page extraction and metadata.
    Requires: pip install pypdf
    """

    def supports(self, source: str) -> bool:
        return Path(source).suffix.lower() == ".pdf"

    def load(self, source: str) -> List[Document]:
        try:
            from pypdf import PdfReader
        except ImportError:
            raise ImportError("Install pypdf: pip install pypdf")

        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {source}")

        reader = PdfReader(str(path))
        total_pages = len(reader.pages)
        info = reader.metadata or {}

        documents = []
        for page_num, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            text = self._clean_pdf_text(text)

            if not text.strip():
                logger.debug(f"[PDFLoader] Skipping empty page {page_num}")
                continue

            doc = Document(
                content=text,
                source=str(path),
                file_type="pdf",
                page_number=page_num,
                total_pages=total_pages,
                title=info.get("/Title", path.stem),
                author=info.get("/Author"),
                metadata={
                    **self._get_file_metadata(source),
                    "pdf_subject": info.get("/Subject"),
                    "pdf_creator": info.get("/Creator"),
                },
            )
            documents.append(doc)

        logger.info(f"[PDFLoader] Loaded {len(documents)}/{total_pages} pages from: {path.name}")
        return documents

    def _clean_pdf_text(self, text: str) -> str:
        """Remove common PDF extraction artifacts."""
        # Remove ligature artifacts, excessive whitespace
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)  # Rejoin hyphenated line breaks
        return text.strip()


class DOCXLoader(BaseLoader):
    """
    Loads .docx files with paragraph and table extraction.
    Requires: pip install python-docx
    """

    def supports(self, source: str) -> bool:
        return Path(source).suffix.lower() == ".docx"

    def load(self, source: str) -> List[Document]:
        try:
            from docx import Document as DocxDocument
        except ImportError:
            raise ImportError("Install python-docx: pip install python-docx")

        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {source}")

        docx = DocxDocument(str(path))
        parts = []

        # Extract paragraphs
        for para in docx.paragraphs:
            if para.text.strip():
                parts.append(para.text.strip())

        # Extract tables
        for table in docx.tables:
            for row in table.rows:
                row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                if row_text:
                    parts.append(f"[Table Row] {row_text}")

        content = "\n\n".join(parts)
        core_props = docx.core_properties

        doc = Document(
            content=content,
            source=str(path),
            file_type="docx",
            title=core_props.title or path.stem,
            author=core_props.author,
            created_at=core_props.created.isoformat() if core_props.created else None,
            metadata=self._get_file_metadata(source),
        )
        logger.info(f"[DOCXLoader] Loaded: {path.name} ({len(parts)} paragraphs/rows)")
        return [doc]


class CSVLoader(BaseLoader):
    """
    Loads CSV files — each row becomes a separate Document for fine-grained retrieval.
    Requires: pip install pandas
    """

    def supports(self, source: str) -> bool:
        return Path(source).suffix.lower() == ".csv"

    def load(self, source: str, text_columns: Optional[List[str]] = None) -> List[Document]:
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("Install pandas: pip install pandas")

        path = Path(source)
        df = pd.read_csv(str(path))
        documents = []

        for idx, row in df.iterrows():
            if text_columns:
                content = " | ".join(str(row[col]) for col in text_columns if col in row)
            else:
                content = row.to_json()

            doc = Document(
                content=content,
                source=str(path),
                file_type="csv",
                title=path.stem,
                metadata={
                    **self._get_file_metadata(source),
                    "row_index": idx,
                    "columns": list(df.columns),
                },
            )
            documents.append(doc)

        logger.info(f"[CSVLoader] Loaded {len(documents)} rows from: {path.name}")
        return documents


class JSONLoader(BaseLoader):
    """
    Loads JSON/JSONL files. Supports jq-like key extraction.
    """

    def supports(self, source: str) -> bool:
        return Path(source).suffix.lower() in {".json", ".jsonl"}

    def load(self, source: str, content_key: Optional[str] = None) -> List[Document]:
        path = Path(source)
        documents = []

        with open(path, "r", encoding="utf-8") as f:
            if path.suffix == ".jsonl":
                records = [json.loads(line) for line in f if line.strip()]
            else:
                data = json.load(f)
                records = data if isinstance(data, list) else [data]

        for idx, record in enumerate(records):
            if content_key and content_key in record:
                content = str(record[content_key])
            else:
                content = json.dumps(record, ensure_ascii=False)

            doc = Document(
                content=content,
                source=str(path),
                file_type=path.suffix.lstrip("."),
                title=path.stem,
                metadata={
                    **self._get_file_metadata(source),
                    "record_index": idx,
                },
            )
            documents.append(doc)

        logger.info(f"[JSONLoader] Loaded {len(documents)} records from: {path.name}")
        return documents


class HTMLLoader(BaseLoader):
    """
    Loads HTML files or URLs with tag stripping.
    Requires: pip install beautifulsoup4 requests
    """

    def supports(self, source: str) -> bool:
        return source.startswith("http") or Path(source).suffix.lower() in {".html", ".htm"}

    def load(self, source: str) -> List[Document]:
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            raise ImportError("Install beautifulsoup4: pip install beautifulsoup4")

        if source.startswith("http"):
            import requests
            response = requests.get(source, timeout=15)
            response.raise_for_status()
            html_content = response.text
            file_type = "url"
        else:
            with open(source, "r", encoding="utf-8", errors="replace") as f:
                html_content = f.read()
            file_type = "html"

        soup = BeautifulSoup(html_content, "html.parser")

        # Remove script, style, nav, footer
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        title = soup.title.string if soup.title else Path(source).name
        content = soup.get_text(separator="\n", strip=True)
        content = re.sub(r"\n{3,}", "\n\n", content)

        doc = Document(
            content=content,
            source=source,
            file_type=file_type,
            title=title,
            metadata={"url": source} if source.startswith("http") else self._get_file_metadata(source),
        )
        logger.info(f"[HTMLLoader] Loaded: {source[:60]} ({len(content)} chars)")
        return [doc]


# ─────────────────────────────────────────────
#  Document Loader Orchestrator
# ─────────────────────────────────────────────

class DocumentLoader:
    """
    Unified loader that auto-detects file type and dispatches to the right loader.
    
    Usage:
        loader = DocumentLoader()
        docs = loader.load("report.pdf")
        docs = loader.load_directory("./docs", recursive=True)
    """

    def __init__(self, custom_loaders: Optional[List[BaseLoader]] = None):
        self._loaders: List[BaseLoader] = [
            PDFLoader(),
            DOCXLoader(),
            CSVLoader(),
            JSONLoader(),
            HTMLLoader(),
            TextLoader(),  # Fallback last
        ]
        if custom_loaders:
            self._loaders = custom_loaders + self._loaders

    def load(self, source: str, **kwargs) -> List[Document]:
        """Load a single file or URL."""
        for loader in self._loaders:
            if loader.supports(source):
                try:
                    return loader.load(source, **kwargs)
                except Exception as e:
                    logger.error(f"[DocumentLoader] Failed to load '{source}': {e}")
                    raise
        raise ValueError(f"No loader found for: {source}")

    def load_many(self, sources: List[str], **kwargs) -> List[Document]:
        """Load multiple sources, skipping failures."""
        all_docs = []
        for source in sources:
            try:
                docs = self.load(source, **kwargs)
                all_docs.extend(docs)
            except Exception as e:
                logger.warning(f"[DocumentLoader] Skipping '{source}': {e}")
        logger.info(f"[DocumentLoader] Total documents loaded: {len(all_docs)}")
        return all_docs

    def load_directory(
        self,
        directory: str,
        recursive: bool = True,
        extensions: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
    ) -> List[Document]:
        """
        Recursively load all supported files in a directory.
        
        Args:
            directory: Root directory path
            recursive: Whether to search subdirectories
            extensions: Filter by file extensions, e.g. [".pdf", ".txt"]
            exclude_patterns: Glob-style patterns to exclude, e.g. ["*draft*"]
        """
        root = Path(directory)
        if not root.is_dir():
            raise NotADirectoryError(f"Not a directory: {directory}")

        glob_pattern = "**/*" if recursive else "*"
        files = [p for p in root.glob(glob_pattern) if p.is_file()]

        # Filter by extensions
        if extensions:
            ext_set = {e.lower() if e.startswith(".") else f".{e.lower()}" for e in extensions}
            files = [f for f in files if f.suffix.lower() in ext_set]

        # Exclude patterns
        if exclude_patterns:
            import fnmatch
            files = [
                f for f in files
                if not any(fnmatch.fnmatch(f.name, pat) for pat in exclude_patterns)
            ]

        logger.info(f"[DocumentLoader] Found {len(files)} files in '{directory}'")
        return self.load_many([str(f) for f in files])

    def stream_directory(self, directory: str, **kwargs) -> Iterator[Document]:
        """Stream documents one by one to avoid memory pressure on large corpora."""
        root = Path(directory)
        for file_path in root.rglob("*"):
            if file_path.is_file():
                try:
                    docs = self.load(str(file_path), **kwargs)
                    yield from docs
                except Exception as e:
                    logger.warning(f"[DocumentLoader] Stream skip '{file_path}': {e}")
