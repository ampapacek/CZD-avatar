from __future__ import annotations

from typing import Any


OPENROUTER_MODEL_PRESETS = [
    "openrouter/free",
    "meta-llama/llama-4-scout",
    "meta-llama/llama-4-maverick",
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
    "openai/gpt-5-nano",
    "openai/gpt-5.4",
    "openai/gpt-5.4-mini",
    "meta-llama/llama-3.3-70b-instruct",
    "anthropic/claude-3.5-haiku",
    "google/gemini-2.0-flash-001",
    "google/gemini-3.0-pro",
    "mistralai/mistral-small-3.1-24b-instruct",
]

AIUFAL_MODEL_PRESETS = [
    "VLLM-llm-server2.swiss-ai/Apertus-8B-Instruct-2509",
    "LLAMA4./opt/vllm/.cache/llama.cpp/unsloth_Llama-4-Scout-17B-16E-Instruct-GGUF_IQ4_XS_Llama-4-Scout-17B-16E-Instruct-IQ4_XS-00001-of-00002.gguf",
    "Apertus-70B-8b_4x3090.RedHatAI/Apertus-70B-Instruct-2509-FP8-dynamic",
    "Qwen/Qwen2.5-Omni-7B-GPTQ-Int4",
    "utter-project/EuroLLM-22B-Instruct-2512",
    "LLM1-A40.llama3.3:latest",
    "LLM3-AMD-MI210.gpt-oss:120b",
    "LLM3-AMD-MI210.llama3.3:latest",
    "LLM3-AMD-MI210.deepseek-r1:70b",
    "LLM2-A30.hf.co/bartowski/Qwen2.5-Coder-32B-Instruct-GGUF:Q4_0",
    "LLM5-RTX5000.deepseek-r1:8b",
    "LLM6-2xRTX5000.gemma3:12b-it-qat",
]

LLM_PROVIDER_PRESETS: list[dict[str, Any]] = [
    {
        "id": "aiufal",
        "label": "AIUfal",
        "base_url": "https://ai.ufal.mff.cuni.cz/api",
        "default_model": "LLM1-A40.llama3.3:latest",
        "api_key_label": "AIUfal token",
        "supports_streaming": True,
        "model_presets": AIUFAL_MODEL_PRESETS,
    },
    {
        "id": "openrouter",
        "label": "OpenRouter",
        "base_url": "https://openrouter.ai/api/v1",
        "default_model": "openai/gpt-5.4-mini",
        "api_key_label": "OpenRouter API key",
        "supports_streaming": True,
        "model_presets": OPENROUTER_MODEL_PRESETS,
    },
]

LLM_PROVIDER_BY_ID = {provider["id"]: provider for provider in LLM_PROVIDER_PRESETS}


def available_llm_providers() -> list[dict[str, Any]]:
    return [
        {
            "id": provider["id"],
            "label": provider["label"],
            "base_url": provider["base_url"],
            "default_model": provider["default_model"],
            "api_key_label": provider["api_key_label"],
            "supports_streaming": provider["supports_streaming"],
            "model_presets": list(provider["model_presets"]),
        }
        for provider in LLM_PROVIDER_PRESETS
    ]


def resolve_llm_provider(provider_id: str | None, base_url: str | None) -> str:
    normalized = (provider_id or "").strip().lower()
    if normalized in LLM_PROVIDER_BY_ID:
        return normalized
    resolved_base_url = (base_url or "").strip().rstrip("/")
    if resolved_base_url == "https://ai.ufal.mff.cuni.cz/api":
        return "aiufal"
    return "openrouter"


def provider_preset(provider_id: str | None = None, base_url: str | None = None) -> dict[str, Any]:
    return LLM_PROVIDER_BY_ID[resolve_llm_provider(provider_id, base_url)]


def provider_models(provider_id: str | None = None, base_url: str | None = None) -> list[str]:
    return list(provider_preset(provider_id, base_url)["model_presets"])


def provider_default_model(provider_id: str | None = None, base_url: str | None = None) -> str:
    return str(provider_preset(provider_id, base_url)["default_model"])
