from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid

from app.core.logger import logger

router = APIRouter()


class DocumentResponse(BaseModel):
    id: str
    filename: str
    size: int
    upload_time: datetime
    status: str
    chunk_count: Optional[int] = None


class DocumentListResponse(BaseModel):
    total: int
    documents: List[DocumentResponse]


# Temporary storage for documents (replace with database)
documents_db = {}


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
        background_tasks: BackgroundTasks,
        file: UploadFile = File(...),
        metadata: Optional[str] = None
):
    """
    Upload a document for processing
    """
    logger.info(f"Uploading document: {file.filename}")

    # Validate file size (50MB limit)
    content = await file.read()
    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(400, "File too large (max 50MB)")

    # Create document record
    doc_id = str(uuid.uuid4())
    documents_db[doc_id] = {
        "id": doc_id,
        "filename": file.filename,
        "size": len(content),
        "upload_time": datetime.now(),
        "status": "uploaded"
    }

    # Process in background
    background_tasks.add_task(process_document, doc_id, content, file.filename)

    return DocumentResponse(
        id=doc_id,
        filename=file.filename,
        size=len(content),
        upload_time=datetime.now(),
        status="uploaded"
    )


@router.get("/list", response_model=DocumentListResponse)
async def list_documents(
        skip: int = 0,
        limit: int = 10
):
    """List all uploaded documents"""
    docs = list(documents_db.values())
    return DocumentListResponse(
        total=len(docs),
        documents=docs[skip:skip + limit]
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str):
    """Get document details"""
    if document_id not in documents_db:
        raise HTTPException(404, "Document not found")
    return documents_db[document_id]


@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """Delete a document"""
    if document_id not in documents_db:
        raise HTTPException(404, "Document not found")
    del documents_db[document_id]
    return {"message": "Document deleted"}


async def process_document(doc_id: str, content: bytes, filename: str):
    """Background task to process document"""
    logger.info(f"Processing document {doc_id}: {filename}")

    # Update status
    documents_db[doc_id]["status"] = "processing"

    try:
        # This will be expanded with actual document processing
        # For now, just simulate processing
        import time
        time.sleep(2)

        documents_db[doc_id]["status"] = "completed"
        documents_db[doc_id]["chunk_count"] = 10
        logger.info(f"Document {doc_id} processed successfully")

    except Exception as e:
        logger.error(f"Failed to process document {doc_id}: {e}")
        documents_db[doc_id]["status"] = "failed"