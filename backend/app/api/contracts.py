import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, UploadFile, File, HTTPException

from app.services.field_extractor import extract_contract_fields
from app.schemas.review import ReviewDemoResponse
from app.services.document_parser import parse_document
from app.review.rules import review_contract
from app.schemas.review import ReviewDemoResponse

router = APIRouter()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_SUFFIXES = {".txt", ".docx", ".pdf"}


@router.post("/review-demo", response_model=ReviewDemoResponse)
async def review_demo(file: UploadFile = File(...)):
    suffix = Path(file.filename).suffix.lower()

    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {suffix}. Only txt, docx and pdf are supported.",
        )

    saved_name = f"{uuid4()}{suffix}"
    saved_path = UPLOAD_DIR / saved_name

    try:
        with saved_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        text = parse_document(str(saved_path), file.filename)
        field_extraction = extract_contract_fields(text)
        findings = review_contract(text)

        return {
            "filename": file.filename,
            "text_length": len(text),
            "text_preview": text[:1000],
            "field_extraction": field_extraction,
            "finding_count": len(findings),
            "findings": findings,
        }

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
