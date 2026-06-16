from functools import lru_cache

from FlagEmbedding import FlagReranker

from app.core.config import get_settings


@lru_cache
def get_reranker() -> FlagReranker:
    settings = get_settings()

    use_fp16 = settings.embedding_use_fp16 and settings.embedding_device == "cuda"

    return FlagReranker(
        settings.reranker_model,
        use_fp16=use_fp16,
        device=settings.embedding_device,
    )


def rerank(query: str, candidates: list[dict], top_k: int = 3) -> list[dict]:
    if not candidates:
        return []

    reranker = get_reranker()

    pairs = [[query, item["text"]] for item in candidates]
    scores = reranker.compute_score(pairs)

    if isinstance(scores, float):
        scores = [scores]

    reranked = []

    for item, score in zip(candidates, scores):
        reranked.append(
            {
                **item,
                "rerank_score": float(score),
            }
        )

    reranked.sort(key=lambda x: x["rerank_score"], reverse=True)
    return reranked[:top_k]