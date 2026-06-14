from openai import OpenAI

from app.core.config import get_settings


def get_llm_client() -> OpenAI:
    settings = get_settings()

    if not settings.llm_api_key:
        raise RuntimeError("LLM_API_KEY is not configured")

    return OpenAI(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
    )


def call_llm(prompt: str) -> str:
    settings = get_settings()
    client = get_llm_client()

    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=[
            {
                "role": "system",
                "content": "你是一个严谨的合同信息抽取助手。你只能输出 JSON，不要输出解释。",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0,
    )

    return response.choices[0].message.content or ""