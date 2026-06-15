from openai import OpenAI

from app.core.config import get_settings


def get_llm_client() -> OpenAI:
    settings = get_settings()

    return OpenAI(
        api_key=settings.llm_api_key or "ollama",
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
        response_format={"type": "json_object"},
    )

    return response.choices[0].message.content or ""
