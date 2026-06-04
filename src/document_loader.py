# document_loader.py

import os
import json
import pandas as pd
import pdfplumber
from docx import Document
from pptx import Presentation
from bs4 import BeautifulSoup


class DocumentLoader:

    def load_file(self, file_path):

        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".pdf":
            text = self._load_pdf(file_path)

        elif ext == ".docx":
            text = self._load_docx(file_path)

        elif ext == ".txt":
            text = self._load_txt(file_path)

        elif ext == ".csv":
            text = self._load_csv(file_path)

        elif ext == ".xlsx":
            text = self._load_excel(file_path)

        elif ext == ".pptx":
            text = self._load_pptx(file_path)

        elif ext == ".html":
            text = self._load_html(file_path)

        elif ext == ".json":
            text = self._load_json(file_path)

        else:
            raise ValueError(f"Unsupported file type: {ext}")

        return {
            "content": text,
            "metadata": {
                "source": file_path,
                "filename": os.path.basename(file_path),
                "file_type": ext.replace(".", ""),
                "size_kb": round(os.path.getsize(file_path) / 1024, 2)
            }
        }

    def _load_pdf(self, file_path):
        text = ""

        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()

                if page_text:
                    text += page_text + "\n"

        return text

    def _load_docx(self, file_path):
        doc = Document(file_path)
        return "\n".join(p.text for p in doc.paragraphs)

    def _load_txt(self, file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def _load_csv(self, file_path):
        df = pd.read_csv(file_path)
        return df.to_string(index=False)

    def _load_excel(self, file_path):
        df = pd.read_excel(file_path)
        return df.to_string(index=False)

    def _load_pptx(self, file_path):

        prs = Presentation(file_path)

        text = ""

        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    text += shape.text + "\n"

        return text

    def _load_html(self, file_path):

        with open(file_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f.read(), "html.parser")

        return soup.get_text()

    def _load_json(self, file_path):

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return json.dumps(data, indent=2)
    
loader = DocumentLoader()

doc = loader.load_file("data/sample.csv")

print(doc)