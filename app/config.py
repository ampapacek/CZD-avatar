from functools import lru_cache
from pathlib import Path

from dotenv import dotenv_values
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables and .env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    llm_provider: str = Field(default="", alias="LLM_PROVIDER")
    admin_password: str = Field(default="", alias="ADMIN_PASSWORD")
    llm_models_cache_ttl_seconds: int = Field(default=3600, alias="LLM_MODELS_CACHE_TTL_SECONDS")

    qdrant_url: str = Field(default="", alias="QDRANT_URL")
    qdrant_path: Path = Field(default=Path("data/qdrant"), alias="QDRANT_PATH")
    qdrant_collection: str = Field(default="czech_history_chunks", alias="QDRANT_COLLECTION")

    embedding_model: str = Field(default="BAAI/bge-m3", alias="EMBEDDING_MODEL")
    chunk_size: int = Field(default=800, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=120, alias="CHUNK_OVERLAP")
    top_k: int = Field(default=10, alias="TOP_K")
    min_score: float = Field(default=0.2, alias="MIN_SCORE")
    min_relative_score: float = Field(default=0.3, alias="MIN_RELATIVE_SCORE")
    retrieval_backend: str = Field(default="msearch", alias="RETRIEVAL_BACKEND")

    reranker_enabled: bool = Field(default=False, alias="RERANKER_ENABLED")
    reranker_model: str = Field(default="BAAI/bge-reranker-v2-m3", alias="RERANKER_MODEL")
    reranker_weight: float = Field(default=0.0, alias="RERANKER_WEIGHT")
    reranker_candidates: int = Field(default=40, alias="RERANKER_CANDIDATES")
    reranker_max_length: int = Field(default=512, alias="RERANKER_MAX_LENGTH")
    reranker_batch_size: int = Field(default=16, alias="RERANKER_BATCH_SIZE")
    reranker_device: str = Field(default="", alias="RERANKER_DEVICE")

    msearch_base_url: str = Field(default="https://api.msearch.themama.ai", alias="MSEARCH_BASE_URL")
    msearch_username: str = Field(default="", alias="MSEARCH_USERNAME")
    msearch_password: str = Field(default="", alias="MSEARCH_PASSWORD")
    msearch_collection: str = Field(
        default="64d6f521-5044-4b02-8658-380b639801af",
        alias="MSEARCH_COLLECTION",
    )
    msearch_max_results: int = Field(default=10, alias="MSEARCH_MAX_RESULTS")
    msearch_mode: str = Field(default="hybrid", alias="MSEARCH_MODE")
    msearch_min_confidence: float | None = Field(default=None, alias="MSEARCH_MIN_CONFIDENCE")
    msearch_timeout: float = Field(default=60.0, alias="MSEARCH_TIMEOUT")

    context_window_tokens: int = Field(default=32768, alias="CONTEXT_WINDOW_TOKENS")
    output_token_budget_short: int = Field(default=384, alias="OUTPUT_TOKEN_BUDGET_SHORT")
    output_token_budget_medium: int = Field(default=768, alias="OUTPUT_TOKEN_BUDGET_MEDIUM")
    output_token_budget_long: int = Field(default=1024, alias="OUTPUT_TOKEN_BUDGET_LONG")
    min_prompt_chunks: int = Field(default=3, alias="MIN_PROMPT_CHUNKS")
    token_budget_safety_margin: float = Field(default=0.10, alias="TOKEN_BUDGET_SAFETY_MARGIN")
    conversation_summary_trigger_tokens: int = Field(
        default=3000,
        alias="CONVERSATION_SUMMARY_TRIGGER_TOKENS",
    )

    raw_data_dir: Path = Field(default=Path("data/raw"), alias="RAW_DATA_DIR")
    chunk_catalog_path: Path = Field(default=Path("data/processed/chunks.jsonl"), alias="CHUNK_CATALOG_PATH")
    prompt_presets_path: Path = Field(default=Path("data/prompt_presets.json"), alias="PROMPT_PRESETS_PATH")
    placeholders_path: Path = Field(default=Path("data/placeholders.json"), alias="PLACEHOLDERS_PATH")

@lru_cache
def load_env_values() -> dict[str, str]:
    # For this local prototype, prefer explicit .env values over exported shell
    # variables so changing .env has the effect users expect.
    env_path = Path(".env")
    if env_path.exists():
        values = {key: value for key, value in dotenv_values(env_path).items() if value is not None}
        if "MSEARCH_USERNAME" not in values and values.get("MSEARCH_USER"):
            values["MSEARCH_USERNAME"] = values["MSEARCH_USER"]
        for optional_key in ("MSEARCH_MIN_CONFIDENCE", "MSEARCH_COLLECTION"):
            value = values.get(optional_key)
            if isinstance(value, str) and not value.strip():
                values.pop(optional_key)
        return values
    return {}


@lru_cache
def get_settings() -> Settings:
    return Settings(**load_env_values())
