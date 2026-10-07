"""Run every test against a fixed configuration instead of the developer's `.env`.

`app.main` builds its settings and provider presets at import time from
`.env`, so without this the endpoint tests passed or failed depending on the
local file, and saw real API keys. A clean checkout (CI) has no `.env` at all.
This module is imported before any test module, so the patch is in place
before `app.rag.llm_providers` binds `load_env_values` and before
`get_settings()` is first called.
"""

from __future__ import annotations

from functools import lru_cache

import app.config

TEST_ENV = {
    "LLM_PROVIDERS": "test",
    "LLM_PROVIDER": "test",
    "LLM_PROVIDER_TEST_NAME": "Test provider",
    "LLM_PROVIDER_TEST_BASE_URL": "https://llm.test.invalid/v1",
    "LLM_PROVIDER_TEST_API_KEY": "test-key",
    "LLM_PROVIDER_TEST_DEFAULT_MODEL": "test-model",
    "LLM_PROVIDER_TEST_PUBLIC_MODELS": "test-model",
    "LLM_PROVIDER_TEST_DISCOVER_MODELS": "false",
    "RETRIEVAL_BACKEND": "msearch",
    "MSEARCH_BASE_URL": "https://msearch.test.invalid",
    "MSEARCH_USERNAME": "test",
    "MSEARCH_PASSWORD": "test",
}


@lru_cache
def _test_env_values() -> dict[str, str]:
    return dict(TEST_ENV)


app.config.load_env_values = _test_env_values
# Settings also reads `.env` by itself for any field not passed explicitly.
app.config.Settings.model_config["env_file"] = None
app.config.get_settings.cache_clear()
