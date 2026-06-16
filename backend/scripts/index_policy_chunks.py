from sqlalchemy import delete

from app.db.session import SessionLocal
from app.models.knowledge import DocumentChunk
from app.rag.embedding_service import embed_texts
from app.rag.policy_loader import get_policy_source_path, build_policy_chunks


def main():
    chunks = build_policy_chunks()

    print(f"Loaded {len(chunks)} chunks.")

    texts = [chunk["text"] for chunk in chunks]
    embeddings = embed_texts(texts)

    db = SessionLocal()

    try:
        db.execute(delete(DocumentChunk))
        db.commit()

        for chunk, embedding in zip(chunks, embeddings):
            db.add(
                DocumentChunk(
                    chunk_id=chunk["chunk_id"],
                    document_name=chunk["document_name"],
                    chapter_title=chunk.get("chapter_title"),
                    section_title=chunk.get("section_title"),
                    text=chunk["text"],
                    embedding=embedding,
                    source_path=get_policy_source_path(),
                )
            )

        db.commit()
        print(f"Indexed {len(chunks)} chunks into pgvector.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()