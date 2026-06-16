from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.knowledge import DocumentChunk
from app.rag.embedding_service import embed_query
from app.rag.reranker_service import rerank


RULE_QUERY_MAP = {
    "PAYMENT_PREPAYMENT_LIMIT": "采购合同预付款比例不得超过合同总金额30%，超过30%需要部门负责人和法务负责人专项审批",
    "DELIVERY_DATE_MISSING": "采购合同应明确交付日期，不得使用另行协商、待定、双方后续确认等不确定表述",
    "AMOUNT_CASE_INCONSISTENT": "采购合同金额应同时包含小写金额和大写金额，且两者必须保持一致",
    "AMOUNT_EXTRACTION_INCOMPLETE": "采购合同金额应明确小写金额、大写金额、币种、含税状态和税率",
    "DISPUTE_LOCATION_RISK": "采购合同争议解决地原则上应为甲方所在地人民法院，供应商所在地法院需要法务审批",
    "INVOICE_TAX_MISSING": "采购合同应明确发票类型、税率、含税状态和发票内容",
}


def build_rule_query(rule_code: str | None, query: str | None) -> str:
    parts = []

    if rule_code and rule_code in RULE_QUERY_MAP:
        parts.append(RULE_QUERY_MAP[rule_code])

    if query:
        parts.append(query)

    return "。".join(parts)


def search_policy_evidence_vector(
    query: str | None = None,
    rule_code: str | None = None,
    candidate_k: int = 20,
    top_k: int = 3,
    use_reranker: bool = True,
) -> list[dict]:
    final_query = build_rule_query(rule_code, query)

    if not final_query:
        return []

    query_embedding = embed_query(final_query)

    db = SessionLocal()

    try:
        distance = DocumentChunk.embedding.cosine_distance(query_embedding)

        stmt = (
            select(
                DocumentChunk.chunk_id,
                DocumentChunk.document_name,
                DocumentChunk.chapter_title,
                DocumentChunk.section_title,
                DocumentChunk.text,
                distance.label("distance"),
            )
            .order_by(distance)
            .limit(candidate_k)
        )

        rows = db.execute(stmt).all()

        candidates = []

        for row in rows:
            candidates.append(
                {
                    "chunk_id": row.chunk_id,
                    "document_name": row.document_name,
                    "chapter_title": row.chapter_title,
                    "section_title": row.section_title,
                    "text": row.text[:1000],
                    "vector_score": float(1 - row.distance),
                }
            )

        if use_reranker:
            reranked = rerank(final_query, candidates, top_k=top_k)
            return reranked

        return candidates[:top_k]

    finally:
        db.close()