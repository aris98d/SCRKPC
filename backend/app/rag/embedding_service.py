from functools import lru_cache

from FlagEmbedding import BGEM3FlagModel

from app.core.config import get_settings


@lru_cache
def get_embedding_model() -> BGEM3FlagModel:
    settings = get_settings()

    use_fp16 = settings.embedding_use_fp16 and settings.embedding_device == "cuda"

    return BGEM3FlagModel(
        settings.embedding_model,
        use_fp16=use_fp16,
        device=settings.embedding_device,
    )


def embed_texts(texts: list[str]) -> list[list[float]]:
    model = get_embedding_model()

    outputs = model.encode(
        texts,
        batch_size=4,
        max_length=8192,
    )

    dense_vectors = outputs["dense_vecs"]
    return dense_vectors.tolist()


def embed_query(query: str) -> list[float]:
    return embed_texts([query])[0]