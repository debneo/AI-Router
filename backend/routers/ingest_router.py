import os
import tempfile
import uuid

from fastapi import APIRouter, File, HTTPException, UploadFile

from services.chunking import adaptive_chunks
from services.parsing import extract_text
from services.vector_store import add_chunks, count

router = APIRouter(tags=["Ingestion"])

@router.post("/ingest")
async def ingest(file:UploadFile = File(...)):
    suffix = os.path.splitext(file.filename)[1]
    # Save the upload to a temp file so parsers can read it from disk
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    try:
        text = extract_text(tmp_path)
    except ValueError as e:
        raise HTTPException(status_code=400,detail=str(e))
    finally:
        os.unlink(tmp_path)

    if not text.strip():
        raise HTTPException(
            status_code=422,
            detail="No readable text found",
        )

    chunks = adaptive_chunks(text)
    doc_id = str(uuid.uuid4())
    add_chunks(doc_id,file.filename,chunks)
    return {
        "doc_id":doc_id,
        "filename": file.filename,
        "chunks_added": len(chunks),
        "total_chunks":count(),
    }