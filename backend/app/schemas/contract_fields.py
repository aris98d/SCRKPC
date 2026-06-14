from pydantic import BaseModel, Field
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


class FieldExtractionResult(BaseModel):
    status: Literal["success", "failed"]
    fields: ContractFields | None = None
    error_message: str | None = None