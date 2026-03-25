"""
PDF Processing Service
======================
Handles PDF text extraction and intelligent chunking.
Uses PyPDF2 for extraction and LangChain's RecursiveCharacterTextSplitter
for semantically-aware chunking.
"""

import logging
import os
from typing import List, Tuple
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.core.config import settings

logger = logging.getLogger(__name__)


class PDFProcessor:
    """Extracts text from PDFs and splits into overlapping chunks."""

    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def extract_text(self, file_path: str) -> str:
        """Extract all text from a PDF file."""
        import PyPDF2

        text_parts = []
        try:
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                num_pages = len(reader.pages)
                logger.info(f"Processing PDF with {num_pages} pages: {file_path}")

                for i, page in enumerate(reader.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text.strip())
                    else:
                        logger.warning(f"Page {i+1} yielded no text (possibly scanned image).")

            full_text = "\n\n".join(text_parts)
            logger.info(f"Extracted {len(full_text)} characters from PDF.")
            return full_text

        except Exception as e:
            logger.error(f"PDF extraction failed: {e}")
            raise ValueError(f"Could not extract text from PDF: {e}")

    def chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks for embedding."""
        if not text.strip():
            raise ValueError("No text content to chunk — document may be empty or image-only.")

        chunks = self.text_splitter.split_text(text)
        logger.info(f"Split document into {len(chunks)} chunks (size={settings.CHUNK_SIZE}, overlap={settings.CHUNK_OVERLAP}).")
        return chunks

    def process_pdf(self, file_path: str) -> Tuple[str, List[str]]:
        """Full pipeline: extract text → chunk."""
        text = self.extract_text(file_path)
        chunks = self.chunk_text(text)
        return text, chunks

    @staticmethod
    def save_upload(file_content: bytes, filename: str) -> str:
        """Save uploaded file to disk. Returns the file path."""
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        file_path = os.path.join(settings.UPLOAD_DIR, filename)
        with open(file_path, "wb") as f:
            f.write(file_content)
        logger.info(f"Saved upload: {file_path}")
        return file_path
