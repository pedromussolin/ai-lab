"""Document upload and processing endpoints."""

import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile

from app.core.config import settings
from app.core.dependencies import get_document_service
from app.core.exceptions import NotFoundError
from app.core.security import verify_api_key
from app.models.document import Document
from app.repositories.document import DocumentRepository
from app.schemas.document import DocumentProcessRequest, DocumentSchema
from app.services.document_service import DocumentService

router = APIRouter()

ALLOWED_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
    "text/markdown",
    "application/json",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}


@router.post("/documents/upload", response_model=DocumentSchema, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    service: DocumentService = Depends(get_document_service),
    _: str = Depends(verify_api_key),
) -> DocumentSchema:
    if file.size and file.size > settings.max_upload_bytes:
        raise HTTPException(413, f"File exceeds maximum size of {settings.max_upload_size_mb}MB")

    content = await file.read()
    doc_id = uuid.uuid4()

    # Save file to disk
    upload_path = Path(settings.upload_dir)
    upload_path.mkdir(parents=True, exist_ok=True)
    (upload_path / str(doc_id)).write_bytes(content)

    doc = Document(
        id=doc_id,
        filename=file.filename or "unknown",
        content_type=file.content_type or "application/octet-stream",
        size_bytes=len(content),
        status="pending",
    )
    created = await service._repo.create(doc)
    return DocumentSchema.model_validate(created)


@router.post("/documents/process", response_model=DocumentSchema)
async def process_document(
    request: DocumentProcessRequest,
    background_tasks: BackgroundTasks,
    service: DocumentService = Depends(get_document_service),
    _: str = Depends(verify_api_key),
) -> DocumentSchema:
    doc = await service._repo.get_by_id(request.document_id)
    if not doc:
        raise NotFoundError("Document", request.document_id)

    background_tasks.add_task(
        service.process_document,
        document_id=request.document_id,
        chunk_size=request.chunk_size,
        chunk_overlap=request.chunk_overlap,
        indexing_strategy=request.indexing_strategy,
    )
    return DocumentSchema.model_validate(doc)


@router.get("/documents/{document_id}", response_model=DocumentSchema)
async def get_document(
    document_id: uuid.UUID,
    service: DocumentService = Depends(get_document_service),
    _: str = Depends(verify_api_key),
) -> DocumentSchema:
    doc = await service._repo.get_by_id(document_id)
    if not doc:
        raise NotFoundError("Document", document_id)
    return DocumentSchema.model_validate(doc)
