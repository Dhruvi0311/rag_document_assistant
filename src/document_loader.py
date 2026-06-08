import os
import csv
import hashlib
from typing import Generator, List, Dict, Any
from pypdf import PdfReader
from docx import Document
from PIL import Image
import pytesseract
from pdf2image import convert_from_path

# Optional: If Tesseract is not in your system PATH on Windows, uncomment and point to your executable:
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class DocumentLoader:
    def __init__(self):
        """
        Initializes the DocumentLoader. Tesseract leverages system binaries.
        """
        pass

    def _generate_hash(self, content: str) -> str:
        """Generates a unique SHA-256 hash for a given string block."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def _create_chunk_metadata(self, doc_id: str, file_path: str, content: str, source_type: str, extra_meta: dict) -> dict:
        """Creates a standardized metadata structure for strict traceability."""
        chunk_hash = self._generate_hash(content)
        metadata = {
            "doc_id": doc_id,
            "chunk_id": f"{doc_id}_{chunk_hash[:12]}",
            "file_name": os.path.basename(file_path),
            "source_type": source_type,
            "chunk_hash": chunk_hash
        }
        metadata.update(extra_meta)
        return metadata

    # 1. PDF EXTRACTION (Page Level + Tesseract OCR fallback)
    def load_pdf(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Extracts content page-by-page. If a page yields no text, 
        it falls back to Tesseract OCR automatically.
        """
        doc_id = self._generate_hash(file_path)
        chunks = []
        reader = PdfReader(file_path)
        
        for page_idx, page in enumerate(reader.pages):
            page_num = page_idx + 1
            text = page.extract_text() or ""
            text = text.strip()
            
            # Fallback to Tesseract OCR if the page text is empty (likely a scanned PDF)
            if not text:
                # Convert only the specific page to an in-memory PIL image
                images = convert_from_path(file_path, first_page=page_num, last_page=page_num)
                if images:
                    # Run Tesseract OCR directly on the PIL image object
                    text = pytesseract.image_to_string(images[0]).strip()
            
            if text:
                meta = self._create_chunk_metadata(
                    doc_id=doc_id, 
                    file_path=file_path, 
                    content=text, 
                    source_type="pdf", 
                    extra_meta={"page_number": page_num}
                )
                chunks.append({"text": text, "metadata": meta})
                
        return chunks

    # 2. DOCX STREAMING PROCESS (Paragraphs & Tables)
    def stream_docx(self, file_path: str) -> Generator[Dict[str, Any], None, None]:
        """
        Streams elements from a DOCX file one-by-one to optimize memory.
        Identifies and parses both structural paragraphs and tables cleanly.
        """
        doc_id = self._generate_hash(file_path)
        doc = Document(file_path)
        
        element_idx = 0
        for element in doc.element.body:
            # Check if element is a paragraph
            if element.tag.endswith('p'):
                p = [p for p in doc.paragraphs if p._element == element]
                if p and p[0].text.strip():
                    text = p[0].text.strip()
                    element_idx += 1
                    meta = self._create_chunk_metadata(
                        doc_id=doc_id, file_path=file_path, content=text, 
                        source_type="docx_paragraph", extra_meta={"element_index": element_idx}
                    )
                    yield {"text": text, "metadata": meta}
                    
            # Check if element is a table
            elif element.tag.endswith('tbl'):
                t = [t for t in doc.tables if t._element == element]
                if t:
                    element_idx += 1
                    table_data = []
                    for row in t[0].rows:
                        row_data = [cell.text.strip() for cell in row.cells]
                        table_data.append(" | ".join(row_data))
                    
                    text = "\n".join(table_data).strip()
                    if text:
                        meta = self._create_chunk_metadata(
                            doc_id=doc_id, file_path=file_path, content=text, 
                            source_type="docx_table", extra_meta={"element_index": element_idx}
                        )
                        yield {"text": text, "metadata": meta}

    # 3. CSV ROW EXTRACTION
    def load_csv(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Parses CSV files and handles every row as an independent tracking chunk.
        """
        doc_id = self._generate_hash(file_path)
        chunks = []
        
        with open(file_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader):
                row_str = ", ".join([f"{k}: {v}" for k, v in row.items() if v])
                if row_str.strip():
                    meta = self._create_chunk_metadata(
                        doc_id=doc_id, file_path=file_path, content=row_str, 
                        source_type="csv", extra_meta={"row_index": idx + 1}
                    )
                    chunks.append({"text": row_str, "metadata": meta})
                    
        return chunks

    # 4. IMAGE TESSERACT OCR LOADING
    def load_image(self, file_path: str) -> Dict[str, Any]:
        """Loads pure image files (PNG/JPG) using Tesseract OCR."""
        doc_id = self._generate_hash(file_path)
        
        # Open image using Pillow
        img = Image.open(file_path)
        text = pytesseract.image_to_string(img).strip()
        
        meta = self._create_chunk_metadata(
            doc_id=doc_id, file_path=file_path, content=text, 
            source_type="image", extra_meta={"type": "scanned_ocr"}
        )
        return {"text": text, "metadata": meta}

    # 5. BATCH LOADING & DUPLICATE FILTERING
    def load_batch(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """
        Processes a batch list of multiple files. Uses a processed set tracker 
        to guarantee that identical chunks are completely deduplicated.
        """
        all_chunks = []
        seen_chunk_hashes = set()
        
        for path in file_paths:
            if not os.path.exists(path):
                print(f"File not found, skipping: {path}")
                continue
                
            ext = path.split('.')[-1].lower()
            print(f"Processing structural load for file: {path}...")
            
            if ext == 'pdf':
                file_chunks = self.load_pdf(path)
                for chunk in file_chunks:
                    h = chunk["metadata"]["chunk_hash"]
                    if h not in seen_chunk_hashes:
                        seen_chunk_hashes.add(h)
                        all_chunks.append(chunk)
                        
            elif ext == 'docx':
                for chunk in self.stream_docx(path):
                    h = chunk["metadata"]["chunk_hash"]
                    if h not in seen_chunk_hashes:
                        seen_chunk_hashes.add(h)
                        all_chunks.append(chunk)
                        
            elif ext == 'csv':
                file_chunks = self.load_csv(path)
                for chunk in file_chunks:
                    h = chunk["metadata"]["chunk_hash"]
                    if h not in seen_chunk_hashes:
                        seen_chunk_hashes.add(h)
                        all_chunks.append(chunk)
                        
            elif ext in ['png', 'jpg', 'jpeg']:
                chunk = self.load_image(path)
                h = chunk["metadata"]["chunk_hash"]
                if h not in seen_chunk_hashes:
                    seen_chunk_hashes.add(h)
                    all_chunks.append(chunk)
            else:
                print(f"Unsupported file format extension: .{ext}")
                
        return all_chunks