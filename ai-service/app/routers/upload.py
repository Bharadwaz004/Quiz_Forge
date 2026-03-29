"""
Upload Router — handles PDF upload, text extraction, and vector storage.
"""

import uuid
import os
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException

from app.core.config import settings
from app.services.pdf_processor import PDFProcessor
from app.services.vector_store import VectorStoreService
from app.models.schemas import UploadResponse, ErrorResponse

logger = logging.getLogger(__name__)
router = APIRouter()

pdf_processor = PDFProcessor()


@router.post(
    "/upload",
    response_model=UploadResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a PDF document for quiz generation.

    1. Validates file type and size
    2. Extracts text from PDF
    3. Chunks text into overlapping segments
    4. Generates embeddings and stores in ChromaDB
    5. Returns a session_id for quiz generation
    """
    # --- Validation ---
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > settings.MAX_UPLOAD_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({size_mb:.1f}MB). Maximum is {settings.MAX_UPLOAD_SIZE_MB}MB.",
        )

    # --- Processing ---
    session_id = uuid.uuid4().hex[:12]

    try:
        # Save file
        file_path = PDFProcessor.save_upload(content, f"{session_id}_{file.filename}")

        # Extract and chunk
        full_text, chunks = pdf_processor.process_pdf(file_path)

        if not chunks:
            raise HTTPException(
                status_code=400,
                detail="Could not extract any text from the PDF. It may be image-only or corrupted.",
            )

        # Store embeddings
        vs = VectorStoreService.get_instance()
        num_stored = vs.store_chunks(session_id, chunks)

        logger.info(f"Upload complete: session={session_id}, chunks={num_stored}")

        # Cleanup: delete PDF file — text is already extracted and embedded
        try:
            os.remove(file_path)
            print(f"[CLEANUP] Deleted PDF: {file_path}")
        except OSError as e:
            print(f"[CLEANUP] Could not delete PDF: {e}")

        return UploadResponse(
            session_id=session_id,
            filename=file.filename,
            num_chunks=num_stored,
            message=f"Document processed successfully. {num_stored} chunks indexed.",
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Upload processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error during document processing: {e}")