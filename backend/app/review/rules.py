import re
from app.rag.policy_retriever import search_policy_evidence


def extract_number_amount(text: str) -> float | None:
    """提取合同中的阿拉伯数字金额"""
    pattern = r"￥?(\d+(?:[,，]\d{3})*(?:\.\d{2})?)"
    match = re.search(pattern, text)
    if match:
        amount_str = match.group(1).replace(",", "").replace("，", "")
        try:
            return float(amount_str)
        except ValueError:
            return None
    return None


def extract_chinese_amount(text: str) -> float | None:
    """提取合同中的中文大写金额"""
    # 简单的中文金额提取逻辑
    chinese_num_map = {
        "零": 0, "一": 1, "二": 2, "三": 3, "四": 4,
        "五": 5, "六": 6, "七": 7, "八": 8, "九": 9,
        "十": 10, "百": 100, "千": 1000, "万": 10000,
        "亿": 100000000
    }
    pattern = r"[零一二三四五六七八九十百千万亿元整]+"
    match = re.search(pattern, text)
    if match:
        # 简化处理：返回None，交由人工审核
        return None
    return None


def check_prepayment_limit(text: str) -> dict | None:
    patterns = [
        r"预付款.*?(\d+)%",
        r"支付合同总额的(\d+)%",
        r"支付.*?(\d+)%",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            ratio = int(match.group(1))
            if ratio > 30:
                citations = search_policy_evidence(
                    rule_code="PAYMENT_PREPAYMENT_LIMIT",
                    query="采购合同 预付款比例 超过30% 专项审批",
                    top_k=3,
                )

                return {
                    "rule_code": "PAYMENT_PREPAYMENT_LIMIT",
                    "status": "risk",
                    "severity": "high",
                    "summary": f"预付款比例为 {ratio}%，超过企业制度 30% 上限",
                    "contract_quote": match.group(0),
                    "suggestion": "建议将预付款比例调整至30%以内，或增加专项审批。",
                    "needs_human_review": True,
                    "knowledge_citations": citations,
                }

    return None


def check_delivery_date(text: str) -> dict | None:
    risky_words = ["另行协商", "待定", "双方协商确定"]

    for word in risky_words:
        if word in text and ("交付" in text or "交货" in text):
            citations = search_policy_evidence(
                rule_code="DELIVERY_DATE_MISSING",
                query="采购合同 交付日期 另行协商 待定 不确定表述",
                top_k=3,
            )
            
            return {
                "rule_code": "DELIVERY_DATE_MISSING",
                "status": "risk",
                "severity": "medium",
                "summary": "交付日期不明确",
                "contract_quote": word,
                "suggestion": "建议明确具体交付日期、交货期限或可执行的交付节点。",
                "needs_human_review": True,
                "knowledge_citations": citations,
            }

    return None


def check_dispute_location(text: str) -> dict | None:
    if "乙方所在地法院" in text or "乙方所在地人民法院" in text:
        citations = search_policy_evidence(
            rule_code="DISPUTE_LOCATION_RISK",
            query="采购合同 争议解决地 甲方所在地人民法院 法务审批",
            top_k=3,
        )

        return {
            "rule_code": "DISPUTE_LOCATION_RISK",
            "status": "risk",
            "severity": "medium",
            "summary": "争议解决地可能不符合甲方企业要求",
            "contract_quote": "乙方所在地法院",
            "suggestion": "建议修改为甲方所在地人民法院，或按企业制度要求进行调整。",
            "needs_human_review": True,
            "knowledge_citations": citations,
        }

    return None


def check_amount_consistency(text: str) -> dict | None:
    number_amount = extract_number_amount(text)
    chinese_amount = extract_chinese_amount(text)

    citations = search_policy_evidence(
        rule_code="AMOUNT_CASE_INCONSISTENT",
        query="采购合同 金额 小写金额 大写金额 一致",
        top_k=3,
    )

    if number_amount is None or chinese_amount is None:
        return {
            "rule_code": "AMOUNT_EXTRACTION_INCOMPLETE",
            "status": "warning",
            "severity": "medium",
            "summary": "合同金额大小写信息不完整，无法自动核验",
            "contract_quote": None,
            "suggestion": "建议人工核对合同金额的大写和小写表达是否完整一致。",
            "needs_human_review": True,
            "knowledge_citations": citations,
        }

    if abs(number_amount - chinese_amount) > 0.01:
        return {
            "rule_code": "AMOUNT_CASE_INCONSISTENT",
            "status": "risk",
            "severity": "high",
            "summary": f"合同金额大小写不一致，小写金额为 {number_amount:.2f} 元，大写金额约为 {chinese_amount:.2f} 元",
            "contract_quote": None,
            "suggestion": "建议核对合同金额，并保持大写金额与小写金额一致。",
            "needs_human_review": True,
            "knowledge_citations": citations,
        }

    return None


def review_contract(text: str) -> list[dict]:
    checks = [
        check_prepayment_limit,
        check_delivery_date,
        check_dispute_location,
        check_amount_consistency,
    ]

    findings = []

    for check in checks:
        result = check(text)
        if result:
            findings.append(result)

    return findings
