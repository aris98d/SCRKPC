from pydantic import BaseModel
from typing import Literal

from app.schemas.contract_fields import FieldExtractionResult


class ReviewFinding(BaseModel):
    rule_code: str
    status: Literal["pass", "risk", "warning", "evidence_insufficient"]
    severity: Literal["low", "medium", "high"]
    summary: str
    contract_quote: str | None = None
    suggestion: str
    needs_human_review: bool = False


class ReviewDemoResponse(BaseModel):
    filename: str
    text_length: int
    text_preview: str
    field_extraction: FieldExtractionResult
    finding_count: int
    findings: list[ReviewFinding]