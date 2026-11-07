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
from pathlib import Path

import pytest

import app.config
from app.rag import wp_config

# A synthetic instance config; nothing reads the server's real one.
TEST_INSTANCE_CONFIG = Path(__file__).parent / "fixtures" / "instance.toml"

TEST_ENV = {
    "INSTANCE_CONFIG_PATH": str(TEST_INSTANCE_CONFIG),
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
    # Endpoint tests must not read or fill a cache file in the checkout; the
    # cache tests hand the app their own temporary one.
    "ANSWER_CACHE_ENABLED": "false",
    # Nor append test turns to the real usage log in logs/events; the analytics
    # tests write to their own temporary directory.
    "ANALYTICS_ENABLED": "false",
}


@lru_cache
def _test_env_values() -> dict[str, str]:
    return dict(TEST_ENV)


app.config.load_env_values = _test_env_values
# Settings also reads `.env` by itself for any field not passed explicitly.
app.config.Settings.model_config["env_file"] = None
app.config.get_settings.cache_clear()
# Modules that read the WP config without importing app.main need it loaded too.
wp_config.set_instance_config(wp_config.load_instance_config(TEST_INSTANCE_CONFIG))


@pytest.fixture(autouse=True)
def _fresh_admin_password_guard():
    """Wrong shared passwords sent by one test must not block the next one."""

    from app import main

    main.admin_password_guard.reset()
    yield


@pytest.fixture(autouse=True)
def _restore_instance_config():
    """A test may swap the active instance config; the next one gets it back."""

    previous = wp_config.instance_config()
    yield
    wp_config.set_instance_config(previous)
