from pathlib import Path


POLICY_PATH = Path("../sample-data/knowledge/purchase_policy.txt")


def load_policy_text() -> str:
    if not POLICY_PATH.exists():
        return ""

    return POLICY_PATH.read_text(encoding="utf-8")


def split_policy_into_chunks(policy_text: str) -> list[dict]:
    chunks = []

    for line in policy_text.splitlines():
        line = line.strip()
        if not line:
            continue

        if line[0].isdigit() or line.startswith("采购合同"):
            chunks.append(
                {
                    "chunk_id": f"policy-{len(chunks) + 1}",
                    "document_name": "采购合同管理制度",
                    "text": line,
                }
            )

    return chunks


def search_policy_evidence(query: str, top_k: int = 3) -> list[dict]:
    policy_text = load_policy_text()
    chunks = split_policy_into_chunks(policy_text)

    keywords = query.split()
    scored_chunks = []

    for chunk in chunks:
        score = 0
        for keyword in keywords:
            if keyword and keyword in chunk["text"]:
                score += 1

        if score > 0:
            scored_chunks.append(
                {
                    **chunk,
                    "score": score,
                }
            )

    scored_chunks.sort(key=lambda x: x["score"], reverse=True)
    return scored_chunks[:top_k]