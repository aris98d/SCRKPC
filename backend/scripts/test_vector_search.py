from pathlib import Path
import sys


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.rag.vector_retriever import search_policy_evidence_vector


def main():
    results = search_policy_evidence_vector(
        rule_code="PAYMENT_PREPAYMENT_LIMIT",
        query="合同签订后支付合同总额的50%，是否超过预付款比例限制",
        candidate_k=20,
        top_k=5,
        use_reranker=True,
    )

    for item in results:
        print("=" * 80)
        print("chunk_id:", item["chunk_id"])
        print("chapter_title:", item.get("chapter_title"))
        print("section_title:", item.get("section_title"))
        print("vector_score:", item.get("vector_score"))
        print("rerank_score:", item.get("rerank_score"))
        print("text:", item["text"][:500])


if __name__ == "__main__":
    main()
