from typing import Any, Literal

from pydantic import BaseModel, Field


AnswerStyle = Literal["laik", "ucitel", "historik"]
AnswerLength = Literal["short", "medium", "long"]
RetrievalBackend = Literal["msearch", "local"]
MSearchMode = Literal["hybrid", "semantic", "keyword"]


class IngestRequest(BaseModel):
    path: str | None = Field(default=None, description="Directory with .txt, .md, and .pdf documents.")
    reset: bool = Field(default=True, description="Recreate the Qdrant collection before ingesting.")


class IngestResponse(BaseModel):
    documents_loaded: int
    chunks_indexed: int
    collection: str


class RetrieveRequest(BaseModel):
    question: str
    top_k: int | None = Field(default=None, ge=0, le=50)
    retrieval_backend: RetrievalBackend | None = None
    msearch_collection: str | None = None
    msearch_mode: MSearchMode | None = None
    msearch_min_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    dense_weight: float = Field(default=0.7, ge=0.0, le=1.0)
    bm25_weight: float = Field(default=0.3, ge=0.0, le=1.0)
    min_score: float | None = Field(default=None, ge=0.0, le=1.0)
    min_relative_score: float | None = Field(default=None, ge=0.0, le=1.0)
    rerank_enabled: bool | None = None
    rerank_weight: float | None = Field(default=None, ge=0.0, le=1.0)
    rerank_candidates: int | None = Field(default=None, ge=1, le=500)


class ChatRequest(BaseModel):
    question: str
    style: AnswerStyle | None = None
    length: AnswerLength | None = None
    custom_instructions: str | None = None
    system_prompt: str | None = None
    user_prompt_template: str | None = None
    style_prompts: dict[str, str] | None = None
    length_prompts: dict[str, str] | None = None
    conversation_history: list[dict[str, str]] = Field(default_factory=list)
    conversation_summary: str | None = None
    admin_password: str | None = None
    context_window_tokens: int | None = Field(default=None, ge=1024)
    output_token_budget_short: int | None = Field(default=None, ge=64)
    output_token_budget_medium: int | None = Field(default=None, ge=64)
    output_token_budget_long: int | None = Field(default=None, ge=64)
    min_prompt_chunks: int | None = Field(default=None, ge=0, le=20)
    token_budget_safety_margin: float | None = Field(default=None, ge=0.0, le=0.5)
    conversation_summary_trigger_tokens: int | None = Field(default=None, ge=256)
    top_k: int | None = Field(default=None, ge=0, le=50)
    retrieval_backend: RetrievalBackend | None = None
    llm_provider: str | None = None
    msearch_collection: str | None = None
    msearch_mode: MSearchMode | None = None
    msearch_min_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    model: str | None = None
    llm_base_url: str | None = None
    llm_api_key: str | None = None
    dense_weight: float = Field(default=0.7, ge=0.0, le=1.0)
    bm25_weight: float = Field(default=0.3, ge=0.0, le=1.0)
    min_score: float | None = Field(default=None, ge=0.0, le=1.0)
    min_relative_score: float | None = Field(default=None, ge=0.0, le=1.0)
    rerank_enabled: bool | None = None
    rerank_weight: float | None = Field(default=None, ge=0.0, le=1.0)
    rerank_candidates: int | None = Field(default=None, ge=1, le=500)


class PromptPreset(BaseModel):
    id: str
    name: str
    system_prompt: str
    user_prompt_template: str
    style_prompts: dict[str, str] = Field(default_factory=dict)
    length_prompts: dict[str, str] = Field(default_factory=dict)
    owner_id: str | None = None
    updated_at: str | None = None


class PromptPresetSaveRequest(BaseModel):
    id: str | None = None
    name: str
    system_prompt: str
    user_prompt_template: str
    style_prompts: dict[str, str] = Field(default_factory=dict)
    length_prompts: dict[str, str] = Field(default_factory=dict)
    owner_id: str | None = None
    admin_password: str | None = None


class UnlockRequest(BaseModel):
    password: str


class UnlockResponse(BaseModel):
    unlocked: bool


class Source(BaseModel):
    citation_id: str
    chunk_id: str
    source_kind: str | None = None
    title: str | None = None
    source_path: str | None = None
    source_path_display: str | None = None
    page_number: int | None = None
    url: str | None = None
    document_url: str | None = None
    source_url: str | None = None
    source_name: str | None = None
    score: float | None = None


class RetrievedChunk(BaseModel):
    citation_id: str
    chunk_id: str
    text: str
    metadata: dict[str, Any]
    score: float
    dense_score: float | None = None
    bm25_score: float | None = None
    rerank_score: float | None = None


class TokenBudgetMetadata(BaseModel):
    context_window_tokens: int
    usable_input_tokens: int
    reserved_output_tokens: int
    estimated_non_source_tokens: int
    estimated_source_tokens: int
    estimated_conversation_history_tokens: int = 0
    estimated_total_input_tokens: int = 0
    used_chunk_count: int
    omitted_chunk_count: int
    trimmed_chunk_count: int
    conversation_summary_used: bool = False


class RetrieveResponse(BaseModel):
    question: str
    retrieved_chunks: list[RetrievedChunk]
    baseline_chunks: list[RetrievedChunk] = Field(default_factory=list)


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]
    retrieved_chunks: list[RetrievedChunk]
    used_chunks: list[RetrievedChunk] = Field(default_factory=list)
    omitted_chunks: list[RetrievedChunk] = Field(default_factory=list)
    baseline_chunks: list[RetrievedChunk] = Field(default_factory=list)
    token_budget: TokenBudgetMetadata | None = None
    chunk_budget_warnings: list[str] = Field(default_factory=list)
    conversation_summary: str | None = None
    model: str
    upstream_model: str | None = None
    response_time_seconds: float
    rerank_time_seconds: float | None = None
    generation_time_seconds: float | None = None


class HealthResponse(BaseModel):
    status: str
    collection: str
