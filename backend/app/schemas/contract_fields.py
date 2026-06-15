import re

from pydantic import BaseModel, Field, field_validator
from typing import Literal


class ContractFields(BaseModel):
    contract_type: str | None = Field(default=None, description="合同类型")
    party_a: str | None = Field(default=None, description="甲方名称")
    party_b: str | None = Field(default=None, description="乙方名称")
    amount_number: float | None = Field(default=None, description="小写金额")
    amount_text: str | None = Field(default=None, description="大写金额")
    payment_terms: str | None = Field(default=None, description="付款条件")
    delivery_date: str | None = Field(default=None, description="交付时间")
    dispute_resolution: str | None = Field(default=None, description="争议解决方式")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    @field_validator("amount_number", mode="before")
    @classmethod
    def normalize_amount_number(cls, value: object) -> object:
        if value is None or isinstance(value, (int, float)):
            return value

        if isinstance(value, str):
            normalized = value.strip().replace(",", "").replace("，", "")
            match = re.search(r"-?\d+(?:\.\d+)?", normalized)
            return float(match.group()) if match else None

        return value


class FieldExtractionResult(BaseModel):
    status: Literal["success", "failed"]
    fields: ContractFields | None = None
    error_message: str | None = None
