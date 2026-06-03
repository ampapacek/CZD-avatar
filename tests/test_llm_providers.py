import unittest
from unittest.mock import Mock, patch

from app.rag.llm_providers import (
    available_llm_providers,
    clear_model_discovery_cache,
    load_provider_configs,
    provider_api_key,
)


class LLMProviderTests(unittest.TestCase):
    def setUp(self) -> None:
        clear_model_discovery_cache()

    def test_provider_public_models_are_scoped_per_provider(self) -> None:
        providers = available_llm_providers(
            {
                "LLM_PROVIDER": "aiufal",
                "LLM_PROVIDERS": "aiufal,openrouter",
                "LLM_PROVIDER_AIUFAL_NAME": "AI Ufal",
                "LLM_PROVIDER_AIUFAL_BASE_URL": "https://ai.ufal.mff.cuni.cz/api",
                "LLM_PROVIDER_AIUFAL_DEFAULT_MODEL": "LLM1-A40.llama3.3:latest",
                "LLM_PROVIDER_AIUFAL_PUBLIC_MODELS": "LLM1-A40.llama3.3:latest",
                "LLM_PROVIDER_AIUFAL_MODELS": "LLM1-A40.llama3.3:latest",
                "LLM_PROVIDER_OPENROUTER_NAME": "OpenRouter",
                "LLM_PROVIDER_OPENROUTER_BASE_URL": "https://openrouter.ai/api/v1",
                "LLM_PROVIDER_OPENROUTER_DEFAULT_MODEL": "openrouter/free",
                "LLM_PROVIDER_OPENROUTER_PUBLIC_MODELS": "openrouter/free",
                "LLM_PROVIDER_OPENROUTER_MODELS": "openrouter/free,openai/gpt-oss-20b",
            }
        )

        openrouter = next(provider for provider in providers if provider["id"] == "openrouter")

        self.assertEqual(openrouter["public_models"], ["openrouter/free"])
        self.assertIn("openrouter/free", openrouter["model_presets"])

    def test_excluded_model_names_are_filtered(self) -> None:
        providers = available_llm_providers(
            {
                "LLM_PROVIDERS": "aiufal",
                "LLM_PROVIDER_AIUFAL_NAME": "AI Ufal",
                "LLM_PROVIDER_AIUFAL_BASE_URL": "https://ai.ufal.mff.cuni.cz/api",
                "LLM_PROVIDER_AIUFAL_DEFAULT_MODEL": "LLM1-A40.llama3.3:latest",
                "LLM_PROVIDER_AIUFAL_PUBLIC_MODELS": "LLM1-A40.llama3.3:latest,rag-helper,openwebuidocs",
                "LLM_PROVIDER_AIUFAL_MODELS": "rag-helper,openwebuidocs,LLM1-A40.llama3.3:latest",
            }
        )

        aiufal = providers[0]

        self.assertEqual(aiufal["public_models"], ["LLM1-A40.llama3.3:latest"])
        self.assertEqual(aiufal["model_presets"], ["LLM1-A40.llama3.3:latest"])

    def test_public_provider_dicts_do_not_expose_api_keys(self) -> None:
        providers = available_llm_providers(
            {
                "LLM_PROVIDERS": "aiufal",
                "LLM_PROVIDER_AIUFAL_NAME": "AI Ufal",
                "LLM_PROVIDER_AIUFAL_BASE_URL": "https://ai.ufal.mff.cuni.cz/api",
                "LLM_PROVIDER_AIUFAL_API_KEY": "secret-token",
                "LLM_PROVIDER_AIUFAL_DEFAULT_MODEL": "LLM1-A40.llama3.3:latest",
            }
        )

        self.assertNotIn("api_key", providers[0])

    def test_provider_api_key_can_read_private_config(self) -> None:
        providers = load_provider_configs(
            {
                "LLM_PROVIDERS": "aiufal",
                "LLM_PROVIDER_AIUFAL_NAME": "AI Ufal",
                "LLM_PROVIDER_AIUFAL_BASE_URL": "https://ai.ufal.mff.cuni.cz/api",
                "LLM_PROVIDER_AIUFAL_API_KEY": "secret-token",
                "LLM_PROVIDER_AIUFAL_DEFAULT_MODEL": "LLM1-A40.llama3.3:latest",
            }
        )

        self.assertEqual(provider_api_key("aiufal", providers), "secret-token")

    def test_public_star_exposes_all_discovered_models(self) -> None:
        response = Mock()
        response.json.return_value = {
            "data": [
                {"id": "LLM3.unsloth/gpt-oss-120b-GGUF:UD-Q8_K_XL"},
                {"id": "LLM3.unsloth/Llama-3.3-70B-Instruct-GGUF:UD-Q6_K_XL"},
            ]
        }
        response.raise_for_status.return_value = None

        with patch("app.rag.llm_providers.httpx.get", return_value=response):
            providers = available_llm_providers(
                {
                    "LLM_PROVIDERS": "aiufal",
                    "LLM_PROVIDER_AIUFAL_BASE_URL": "https://ai.ufal.mff.cuni.cz/api",
                    "LLM_PROVIDER_AIUFAL_API_KEY": "secret-token",
                    "LLM_PROVIDER_AIUFAL_DEFAULT_MODEL": "LLM1-A40.llama3.3:latest",
                    "LLM_PROVIDER_AIUFAL_PUBLIC_MODELS": "*",
                    "LLM_PROVIDER_AIUFAL_MODELS": "stale-model",
                    "LLM_PROVIDER_AIUFAL_DISCOVER_MODELS": "true",
                }
            )

        aiufal = providers[0]

        self.assertEqual(
            aiufal["model_presets"],
            [
                "LLM3.unsloth/gpt-oss-120b-GGUF:UD-Q8_K_XL",
                "LLM3.unsloth/Llama-3.3-70B-Instruct-GGUF:UD-Q6_K_XL",
            ],
        )
        self.assertEqual(aiufal["public_models"], aiufal["model_presets"])
        self.assertEqual(aiufal["default_model"], "LLM3.unsloth/gpt-oss-120b-GGUF:UD-Q8_K_XL")

    def test_static_models_are_fallback_when_discovery_fails(self) -> None:
        with patch("app.rag.llm_providers.httpx.get", side_effect=RuntimeError("offline")):
            providers = available_llm_providers(
                {
                    "LLM_PROVIDERS": "aiufal",
                    "LLM_PROVIDER_AIUFAL_BASE_URL": "https://ai.ufal.mff.cuni.cz/api",
                    "LLM_PROVIDER_AIUFAL_DEFAULT_MODEL": "LLM1-A40.llama3.3:latest",
                    "LLM_PROVIDER_AIUFAL_PUBLIC_MODELS": "*",
                    "LLM_PROVIDER_AIUFAL_MODELS": "fallback-a,fallback-b",
                    "LLM_PROVIDER_AIUFAL_DISCOVER_MODELS": "true",
                }
            )

        aiufal = providers[0]

        self.assertEqual(aiufal["model_presets"], ["LLM1-A40.llama3.3:latest", "fallback-a", "fallback-b"])
        self.assertEqual(aiufal["public_models"], aiufal["model_presets"])
        self.assertEqual(aiufal["default_model"], "LLM1-A40.llama3.3:latest")

    def test_discovery_cache_uses_ttl_until_forced(self) -> None:
        first_response = Mock()
        first_response.json.return_value = {"data": [{"id": "first-model"}]}
        first_response.raise_for_status.return_value = None
        second_response = Mock()
        second_response.json.return_value = {"data": [{"id": "second-model"}]}
        second_response.raise_for_status.return_value = None
        env = {
            "LLM_PROVIDERS": "aiufal",
            "LLM_PROVIDER_AIUFAL_BASE_URL": "https://ai.ufal.mff.cuni.cz/api",
            "LLM_PROVIDER_AIUFAL_PUBLIC_MODELS": "*",
            "LLM_PROVIDER_AIUFAL_DISCOVER_MODELS": "true",
            "LLM_MODELS_CACHE_TTL_SECONDS": "3600",
        }

        with patch("app.rag.llm_providers.httpx.get", side_effect=[first_response, second_response]) as get:
            first = available_llm_providers(env)
            cached = available_llm_providers(env)
            refreshed = available_llm_providers(env, force_model_refresh=True)

        self.assertEqual(get.call_count, 2)
        self.assertEqual(first[0]["model_presets"], ["first-model"])
        self.assertEqual(cached[0]["model_presets"], ["first-model"])
        self.assertEqual(refreshed[0]["model_presets"], ["second-model"])


if __name__ == "__main__":
    unittest.main()
