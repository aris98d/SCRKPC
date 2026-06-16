from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    llm_api_key: str = Field(default="ollama", alias="LLM_API_KEY")
    llm_base_url: str = Field(default="http://localhost:11434/v1", alias="LLM_BASE_URL")
    llm_model: str = Field(default="qwen2.5:7b-instruct", alias="LLM_MODEL")

    database_url: str = Field(
        default="postgresql+psycopg2://contract_user:contract_pass@localhost:5432/contract_review",
        alias="DATABASE_URL",
    )

    embedding_model: str = Field(default="BAAI/bge-m3", alias="EMBEDDING_MODEL")
    reranker_model: str = Field(default="BAAI/bge-reranker-v2-m3", alias="RERANKER_MODEL")
    embedding_device: str = Field(default="cpu", alias="EMBEDDING_DEVICE")
    embedding_use_fp16: bool = Field(default=False, alias="EMBEDDING_USE_FP16")

    knowledge_base_dir: str = Field(default="sample-data/knowledge", alias="KNOWLEDGE_BASE_DIR")
    
    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()