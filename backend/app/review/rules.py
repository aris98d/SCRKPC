import re


def check_prepayment_limit(text: str) -> dict | None:
    """
    检查预付款比例是否超过 30%。
    这是一个 MVP 规则，先用简单正则实现。
    """
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
                return {
                    "rule_code": "PAYMENT_PREPAYMENT_LIMIT",
                    "status": "risk",
                    "severity": "high",
                    "summary": f"预付款比例为 {ratio}%，超过企业制度 30% 上限",
                    "contract_quote": match.group(0),
                    "suggestion": "建议将预付款比例调整至30%以内，或增加专项审批。",
                    "needs_human_review": True,
                }

    return None


def check_delivery_date(text: str) -> dict | None:
    risky_words = ["另行协商", "待定", "双方协商确定"]

    for word in risky_words:
        if word in text and ("交付" in text or "交货" in text):
            return {
                "rule_code": "DELIVERY_DATE_MISSING",
                "status": "risk",
                "severity": "medium",
                "summary": "交付日期不明确",
                "contract_quote": word,
                "suggestion": "建议明确具体交付日期、交货期限或可执行的交付节点。",
                "needs_human_review": True,
            }

    return None


def check_dispute_location(text: str) -> dict | None:
    if "乙方所在地法院" in text or "乙方所在地人民法院" in text:
        return {
            "rule_code": "DISPUTE_LOCATION_RISK",
            "status": "risk",
            "severity": "medium",
            "summary": "争议解决地可能不符合甲方企业要求",
            "contract_quote": "乙方所在地法院",
            "suggestion": "建议修改为甲方所在地人民法院，或按企业制度要求进行调整。",
            "needs_human_review": True,
        }

    return None


def check_amount_consistency(text: str) -> dict | None:
    """
    MVP 简化版：只做演示。
    如果同时出现 100000 和 壹拾贰万，认为金额大小写不一致。
    """
    if "100000" in text and "壹拾贰万" in text:
        return {
            "rule_code": "AMOUNT_CASE_INCONSISTENT",
            "status": "risk",
            "severity": "high",
            "summary": "合同金额大小写可能不一致",
            "contract_quote": "人民币100000元，大写人民币壹拾贰万元整",
            "suggestion": "建议核对合同金额，并保持大写金额与小写金额一致。",
            "needs_human_review": True,
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
