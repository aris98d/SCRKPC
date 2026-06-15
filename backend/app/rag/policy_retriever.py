import re
from functools import lru_cache

from app.rag.policy_loader import build_policy_chunks


RULE_KEYWORDS = {
    "PAYMENT_PREPAYMENT_LIMIT": [
        "预付款",
        "30%",
        "专项审批",
        "合同总金额",
        "部门负责人",
        "法务负责人",
    ],
    "DELIVERY_DATE_MISSING": [
        "交付日期",
        "交付时间",
        "另行协商",
        "待定",
        "不确定表述",
        "交付条款",
    ],
    "AMOUNT_CASE_INCONSISTENT": [
        "金额",
        "小写金额",
        "大写金额",
        "一致",
        "金额不一致",
    ],
    "AMOUNT_EXTRACTION_INCOMPLETE": [
        "金额",
        "小写金额",
        "大写金额",
        "一致",
        "币种",
    ],
    "DISPUTE_LOCATION_RISK": [
        "争议解决",
        "甲方所在地",
        "人民法院",
        "供应商所在地",
        "法务审批",
    ],
    "INVOICE_TAX_MISSING": [
        "发票",
        "税率",
        "含税",
        "发票类型",
        "税务",
    ],
}


@lru_cache
def get_policy_chunks() -> tuple[dict, ...]:
    return tuple(build_policy_chunks())


def tokenize_query(query: str) -> list[str]:
    tokens = re.split(r"[\s,，。；;、]+", query)
    return [token.strip() for token in tokens if token.strip()]


def search_policy_evidence(
    query: str | None = None,
    rule_code: str | None = None,
    top_k: int = 3,
) -> list[dict]:
    chunks = list(get_policy_chunks())

    keywords: list[str] = []

    if rule_code and rule_code in RULE_KEYWORDS:
        keywords.extend(RULE_KEYWORDS[rule_code])

    if query:
        keywords.extend(tokenize_query(query))

    # 去重
    keywords = list(dict.fromkeys(keywords))

    scored_results = []

    for chunk in chunks:
        text = chunk["text"]
        title = chunk["section_title"]
        chapter = chunk["chapter_title"]

        score = 0

        for keyword in keywords:
            if keyword in text:
                score += 2
            if keyword in title:
                score += 3
            if keyword in chapter:
                score += 1

        if score > 0:
            scored_results.append(
                {
                    "chunk_id": chunk["chunk_id"],
                    "document_name": chunk["document_name"],
                    "chapter_title": chunk["chapter_title"],
                    "section_title": chunk["section_title"],
                    "text": chunk["text"][:800],
                    "score": score,
                }
            )

    scored_results.sort(key=lambda item: item["score"], reverse=True)
    return scored_results[:top_k]