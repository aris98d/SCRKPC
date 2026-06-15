from pydantic import BaseModel, Field
from typing import Literal

from app.schemas.contract_fields import FieldExtractionResult


class KnowledgeCitation(BaseModel):
    chunk_id: str
    document_name: str
    text: str
    score: int | float | None = None


class ReviewFinding(BaseModel):
    rule_code: str
    status: Literal["pass", "risk", "warning", "evidence_insufficient"]
    severity: Literal["low", "medium", "high"]
    summary: str
    contract_quote: str | None = None
    suggestion: str
    needs_human_review: bool = False
    knowledge_citations: list[KnowledgeCitation] = Field(default_factory=list)


class ReviewDemoResponse(BaseModel):
    filename: str
    text_length: int
    text_preview: str
    field_extraction: FieldExtractionResult
    finding_count: int
    findings: list[ReviewFinding]