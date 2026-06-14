import json
import re

from app.llm.client import call_llm
from app.schemas.contract_fields import ContractFields, FieldExtractionResult


def build_field_extraction_prompt(contract_text: str) -> str:
    return f"""
你是企业合同审查系统中的字段抽取模块。

请从下面合同文本中抽取结构化字段。

要求：
1. 只输出 JSON。
2. 不要输出 Markdown。
3. 不要输出解释。
4. 如果某个字段无法确定，填 null。
5. confidence 表示你对整体抽取结果的置信度，范围 0 到 1。

字段说明：
- contract_type：合同类型，例如采购合同、销售合同、服务合同
- party_a：甲方名称
- party_b：乙方名称
- amount_number：合同小写金额，数字类型
- amount_text：合同大写金额
- payment_terms：付款条件
- delivery_date：交付时间
- dispute_resolution：争议解决方式
- confidence：整体置信度

输出 JSON 格式如下：
{{
  "contract_type": "采购合同",
  "party_a": "甲方公司名称",
  "party_b": "乙方公司名称",
  "amount_number": 100000,
  "amount_text": "壹拾万元整",
  "payment_terms": "合同签订后支付合同总额的30%",
  "delivery_date": "2026年6月30日前",
  "dispute_resolution": "甲方所在地人民法院",
  "confidence": 0.9
}}

合同文本：
{contract_text[:6000]}
""".strip()


def extract_json_from_text(text: str) -> dict:
    """
    尽量从模型输出中提取 JSON。
    即使模型误输出 ```json ... ```，也尝试修复。
    """
    cleaned = text.strip()

    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```json", "", cleaned)
        cleaned = re.sub(r"^```", "", cleaned)
        cleaned = re.sub(r"```$", "", cleaned)
        cleaned = cleaned.strip()

    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in LLM output")

    return json.loads(match.group(0))


def extract_contract_fields(contract_text: str) -> FieldExtractionResult:
    try:
        prompt = build_field_extraction_prompt(contract_text)
        llm_output = call_llm(prompt)
        data = extract_json_from_text(llm_output)

        fields = ContractFields.model_validate(data)

        return FieldExtractionResult(
            status="success",
            fields=fields,
            error_message=None,
        )

    except Exception as exc:
        return FieldExtractionResult(
            status="failed",
            fields=None,
            error_message=str(exc),
        )