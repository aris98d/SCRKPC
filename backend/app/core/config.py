from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    llm_api_key: str = Field(default="ollama", alias="LLM_API_KEY")
    llm_base_url: str = Field(
        default="http://127.0.0.1:11434/v1",
        alias="LLM_BASE_URL",
    )
    llm_model: str = Field(default="qwen2.5:7b-instruct", alias="LLM_MODEL")

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
