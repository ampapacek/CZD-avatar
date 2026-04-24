from functools import lru_cache
from pathlib import Path

from dotenv import dotenv_values
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables and .env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    openrouter_api_key: str = Field(default="", alias="OPENROUTER_API_KEY")
    openrouter_model: str = Field(default="openai/gpt-4o-mini", alias="OPENROUTER_MODEL")
    openrouter_base_url: str = Field(default="https://openrouter.ai/api/v1", alias="OPENROUTER_BASE_URL")

    qdrant_url: str = Field(default="", alias="QDRANT_URL")
    qdrant_path: Path = Field(default=Path("data/qdrant"), alias="QDRANT_PATH")
    qdrant_collection: str = Field(default="czech_history_chunks", alias="QDRANT_COLLECTION")

    embedding_model: str = Field(default="BAAI/bge-m3", alias="EMBEDDING_MODEL")
    chunk_size: int = Field(default=800, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=120, alias="CHUNK_OVERLAP")
    top_k: int = Field(default=10, alias="TOP_K")
    min_score: float = Field(default=0.2, alias="MIN_SCORE")
    min_relative_score: float = Field(default=0.3, alias="MIN_RELATIVE_SCORE")

    default_style: str = Field(default="ucitel", alias="DEFAULT_STYLE")
    default_length: str = Field(default="medium", alias="DEFAULT_LENGTH")

    raw_data_dir: Path = Field(default=Path("data/raw"), alias="RAW_DATA_DIR")
    chunk_catalog_path: Path = Field(default=Path("data/processed/chunks.jsonl"), alias="CHUNK_CATALOG_PATH")


@lru_cache
def get_settings() -> Settings:
    # For this local prototype, prefer explicit .env values over exported shell
    # variables so changing .env has the effect users expect.
    env_path = Path(".env")
    if env_path.exists():
        values = {key: value for key, value in dotenv_values(env_path).items() if value is not None}
        return Settings(**values)
    return Settings()
