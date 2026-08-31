import unittest
from unittest.mock import Mock, patch

from app.rag.model_metadata import ReasoningSupport
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
                "LLM_PROVIDER_AIUFAL_PUBLIC_MODELS": (
                    "LLM1-A40.llama3.3:latest,rag-helper,openwebdocs,openwebuidocs,"
                    "LLM6-2xRTX5000.gemma3:12b-it-qat"
                ),
                "LLM_PROVIDER_AIUFAL_MODELS": (
                    "rag-helper,openwebdocs,openwebuidocs,LLM6-2xRTX5000.gemma3:12b-it-qat,"
                    "LLM1-A40.llama3.3:latest"
                ),
            }
        )

        aiufal = providers[0]

        self.assertEqual(aiufal["public_models"], ["LLM1-A40.llama3.3:latest"])
        self.assertEqual(aiufal["model_presets"], ["LLM1-A40.llama3.3:latest"])

    def test_einfra_non_chat_models_are_excluded_by_exact_id(self) -> None:
        response = Mock()
        response.json.return_value = {
            "data": [
                {"id": "multilingual-e5-large-instruct"},
                {"id": "qwen3-32b"},
                {"id": "mxbai-embed-large:latest"},
                {"id": "nomic-embed-text-v1.5"},
                {"id": "nomic-embed-text-v2-moe"},
                {"id": "qwen3-embedding-4b"},
                {"id": "qwen3-reranker-4b"},
                {"id": "whisper-large-v3"},
                {"id": "llama-3.3-70b-instruct"},
                # Near miss: merely contains an excluded id, so it must survive.
                {"id": "my-whisper-large-v3-chat"},
            ]
        }
        response.raise_for_status.return_value = None

        with patch("app.rag.llm_providers.httpx.get", return_value=response):
            providers = available_llm_providers(
                {
                    "LLM_PROVIDERS": "einfra",
                    "LLM_PROVIDER_EINFRA_BASE_URL": "https://llm.e-infra.cz/v1",
                    "LLM_PROVIDER_EINFRA_DEFAULT_MODEL": "qwen3-32b",
                    "LLM_PROVIDER_EINFRA_PUBLIC_MODELS": "*",
                    "LLM_PROVIDER_EINFRA_DISCOVER_MODELS": "true",
                }
            )

        einfra = providers[0]

        self.assertEqual(
            einfra["model_presets"],
            ["qwen3-32b", "llama-3.3-70b-instruct", "my-whisper-large-v3-chat"],
        )
        self.assertEqual(einfra["public_models"], einfra["model_presets"])

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

    def test_provider_payload_includes_known_context_windows_for_its_models(self) -> None:
        providers = available_llm_providers(
            {
                "LLM_PROVIDERS": "aiufal,openrouter",
                "LLM_PROVIDER_AIUFAL_DEFAULT_MODEL": "LLM1-A40.llama3.3:latest",
                "LLM_PROVIDER_AIUFAL_MODELS": "LLM1-A40.llama3.3:latest,unknown-aiufal-model",
                "LLM_PROVIDER_OPENROUTER_DEFAULT_MODEL": "openrouter/free",
                "LLM_PROVIDER_OPENROUTER_MODELS": "openrouter/free",
            },
            model_context_windows={
                "LLM1-A40.llama3.3:latest": 4500,
                "openrouter/free": 8192,
                "not-configured": 20000,
            },
        )

        aiufal = next(provider for provider in providers if provider["id"] == "aiufal")
        openrouter = next(provider for provider in providers if provider["id"] == "openrouter")

        self.assertEqual(aiufal["model_context_windows"], {"LLM1-A40.llama3.3:latest": 4500})
        self.assertEqual(openrouter["model_context_windows"], {"openrouter/free": 8192})

    def test_provider_context_window_default_applies_to_all_provider_models(self) -> None:
        providers = available_llm_providers(
            {
                "LLM_PROVIDERS": "provider2",
                "LLM_PROVIDER_PROVIDER2_NAME": "OpenRouter",
                "LLM_PROVIDER_PROVIDER2_DEFAULT_MODEL": "openrouter/free",
                "LLM_PROVIDER_PROVIDER2_MODELS": "openrouter/free,meta-llama/llama-4-scout",
            },
            provider_context_window_defaults={"OpenRouter": 50000},
        )

        self.assertEqual(providers[0]["default_context_window_tokens"], 50000)
        self.assertEqual(
            providers[0]["model_context_windows"],
            {
                "openrouter/free": 50000,
                "meta-llama/llama-4-scout": 50000,
            },
        )

    def test_einfra_model_info_context_windows_are_discovered(self) -> None:
        models_response = Mock()
        models_response.json.return_value = {
            "data": [
                {"id": "mini"},
                {"id": "thinker"},
            ]
        }
        models_response.raise_for_status.return_value = None
        model_info_response = Mock()
        model_info_response.json.return_value = {
            "data": [
                {"model_name": "mini", "model_info": {"context_size": 128000}},
                {"model_name": "thinker", "model_info": {"context_size": "64000"}},
            ]
        }
        model_info_response.raise_for_status.return_value = None

        with patch("app.rag.llm_providers.httpx.get", side_effect=[models_response, model_info_response]) as get:
            providers = available_llm_providers(
                {
                    "LLM_PROVIDERS": "einfra",
                    "LLM_PROVIDER_EINFRA_NAME": "e-infra",
                    "LLM_PROVIDER_EINFRA_BASE_URL": "https://llm.ai.e-infra.cz/v1",
                    "LLM_PROVIDER_EINFRA_API_KEY": "secret-token",
                    "LLM_PROVIDER_EINFRA_DEFAULT_MODEL": "mini",
                    "LLM_PROVIDER_EINFRA_PUBLIC_MODELS": "*",
                    "LLM_PROVIDER_EINFRA_DISCOVER_MODELS": "true",
                }
            )

        einfra = providers[0]

        self.assertEqual(get.call_count, 2)
        self.assertEqual(einfra["model_presets"], ["mini", "thinker"])
        self.assertEqual(
            einfra["model_context_windows"],
            {
                "mini": 128000,
                "thinker": 64000,
            },
        )

    def test_openrouter_reasoning_support_is_discovered_from_its_catalogue(self) -> None:
        response = Mock()
        response.json.return_value = {
            "data": [
                {
                    "id": "openai/gpt-5.4",
                    "supported_parameters": ["reasoning", "reasoning_effort"],
                    "reasoning": {
                        "mandatory": False,
                        "supported_efforts": ["xhigh", "high", "medium", "low", "none"],
                        "default_effort": "medium",
                    },
                },
                {
                    "id": "openai/gpt-oss-120b",
                    "supported_parameters": ["reasoning", "reasoning_effort"],
                    # Mandatory and still listing "none" is how OpenRouter's own
                    # catalogue reads for this model; sending it is a 400.
                    "reasoning": {"mandatory": True, "supported_efforts": ["high", "medium", "low", "none"]},
                },
                {"id": "anthropic/claude-haiku-4.5", "reasoning": {"mandatory": False}},
                {"id": "meta-llama/llama-4-scout", "reasoning": None},
                {"id": "openai/gpt-5-nano", "reasoning": {"mandatory": True, "supported_efforts": ["high"]}},
            ]
        }
        response.raise_for_status.return_value = None

        with patch("app.rag.llm_providers.httpx.get", return_value=response) as get:
            providers = available_llm_providers(
                {
                    "LLM_PROVIDERS": "openrouter",
                    "LLM_PROVIDER_OPENROUTER_NAME": "OpenRouter",
                    "LLM_PROVIDER_OPENROUTER_BASE_URL": "https://openrouter.ai/api/v1",
                    "LLM_PROVIDER_OPENROUTER_DEFAULT_MODEL": "openai/gpt-5.4",
                    "LLM_PROVIDER_OPENROUTER_MODELS": (
                        "openai/gpt-5.4,openai/gpt-oss-120b,anthropic/claude-haiku-4.5,"
                        "meta-llama/llama-4-scout,openai/gpt-5-nano"
                    ),
                },
                model_reasoning={
                    "openai/gpt-5-nano": ReasoningSupport(
                        param="reasoning", efforts=("minimal", "low"), mandatory=True, note="probed"
                    )
                },
            )

        discovered = providers[0]["model_reasoning"]

        self.assertEqual(get.call_args.args[0], "https://openrouter.ai/api/v1/models")
        # Published high-to-low, shown cheapest first.
        self.assertEqual(
            discovered["openai/gpt-5.4"]["efforts"], ["none", "low", "medium", "high", "xhigh"]
        )
        self.assertFalse(discovered["openai/gpt-5.4"]["mandatory"])
        # Nothing is sent for a user who never touches the selector.
        self.assertIsNone(discovered["openai/gpt-5.4"]["default"])
        # A mandatory model keeps no off switch, whatever the catalogue says.
        self.assertEqual(discovered["openai/gpt-oss-120b"]["efforts"], ["low", "medium", "high"])
        # It reasons either way, so the untouched selector asks for the cheapest
        # level rather than leaving it at the catalogue's "medium".
        self.assertEqual(discovered["openai/gpt-oss-120b"]["default"], "low")
        # "Reasons, but not by effort level" is nothing we can express: no
        # control, no parameter, exactly as before discovery existed.
        self.assertNotIn("anthropic/claude-haiku-4.5", discovered)
        self.assertNotIn("meta-llama/llama-4-scout", discovered)
        # A hand-written declaration is a correction, so it wins.
        self.assertEqual(discovered["openai/gpt-5-nano"]["efforts"], ["minimal", "low"])
        self.assertEqual(discovered["openai/gpt-5-nano"]["note"], "probed")

    def test_reasoning_is_not_discovered_from_providers_that_do_not_publish_it(self) -> None:
        # e-infra's LiteLLM catalogue reports `reasoning_effort` as supported for
        # every vLLM-served model, embeddings included, and omits it for the one
        # model that actually reasons. Asking it would be worse than not asking.
        models_response = Mock()
        models_response.json.return_value = {"data": [{"id": "mini"}]}
        models_response.raise_for_status.return_value = None
        model_info_response = Mock()
        model_info_response.json.return_value = {"data": []}
        model_info_response.raise_for_status.return_value = None

        with patch(
            "app.rag.llm_providers.httpx.get", side_effect=[models_response, model_info_response]
        ) as get:
            providers = available_llm_providers(
                {
                    "LLM_PROVIDERS": "einfra",
                    "LLM_PROVIDER_EINFRA_NAME": "e-infra",
                    "LLM_PROVIDER_EINFRA_BASE_URL": "https://llm.ai.e-infra.cz/v1",
                    "LLM_PROVIDER_EINFRA_DEFAULT_MODEL": "mini",
                    "LLM_PROVIDER_EINFRA_DISCOVER_MODELS": "true",
                }
            )

        # `/models` and `/model/info`, and no third call for reasoning.
        self.assertEqual(get.call_count, 2)
        self.assertEqual(providers[0]["model_reasoning"], {})

    def test_catalogue_context_length_is_imported_under_the_provider_ceiling(self) -> None:
        response = Mock()
        response.json.return_value = {
            "data": [
                # Smaller than the provider default: the case worth importing,
                # because assuming 60000 for it was over-packing the prompt.
                {"id": "small/model", "context_length": 32768},
                # A capacity nothing here can spend. Held at the ceiling.
                {"id": "huge/model", "context_length": 1048576},
                # Nonsense and absent both leave the provider default standing.
                {"id": "broken/model", "context_length": "lots"},
                {"id": "quiet/model"},
            ]
        }
        response.raise_for_status.return_value = None

        env = {
            "LLM_PROVIDERS": "openrouter",
            "LLM_PROVIDER_OPENROUTER_NAME": "OpenRouter",
            "LLM_PROVIDER_OPENROUTER_BASE_URL": "https://openrouter.ai/api/v1",
            "LLM_PROVIDER_OPENROUTER_DEFAULT_MODEL": "small/model",
            "LLM_PROVIDER_OPENROUTER_MODELS": "small/model,huge/model,broken/model,quiet/model",
        }

        with patch("app.rag.llm_providers.httpx.get", return_value=response):
            providers = available_llm_providers(
                env, provider_context_window_defaults={"OpenRouter": 60000}
            )

        self.assertEqual(
            providers[0]["model_context_windows"],
            {
                "small/model": 32768,
                "huge/model": 60000,
                "broken/model": 60000,
                "quiet/model": 60000,
            },
        )

        # Raising the ceiling is how the big windows get used on purpose.
        clear_model_discovery_cache()
        with patch("app.rag.llm_providers.httpx.get", return_value=response):
            raised = available_llm_providers(
                env,
                provider_context_window_defaults={"OpenRouter": 60000},
                provider_context_window_ceilings={"OpenRouter": 200000},
            )

        self.assertEqual(raised[0]["model_context_windows"]["huge/model"], 200000)
        self.assertEqual(raised[0]["model_context_windows"]["small/model"], 32768)

    def test_model_info_context_windows_obey_the_same_ceiling(self) -> None:
        # e-infra serves several models that report a million tokens. One policy
        # for the field, whichever endpoint published it.
        models_response = Mock()
        models_response.json.return_value = {"data": [{"id": "kimi"}, {"id": "mini"}]}
        models_response.raise_for_status.return_value = None
        model_info_response = Mock()
        model_info_response.json.return_value = {
            "data": [
                {"model_name": "kimi", "model_info": {"context_size": 1048576}},
                {"model_name": "mini", "model_info": {"context_size": 32768}},
            ]
        }
        model_info_response.raise_for_status.return_value = None

        with patch(
            "app.rag.llm_providers.httpx.get", side_effect=[models_response, model_info_response]
        ):
            providers = available_llm_providers(
                {
                    "LLM_PROVIDERS": "einfra",
                    "LLM_PROVIDER_EINFRA_NAME": "e-infra",
                    "LLM_PROVIDER_EINFRA_BASE_URL": "https://llm.ai.e-infra.cz/v1",
                    "LLM_PROVIDER_EINFRA_DEFAULT_MODEL": "mini",
                    "LLM_PROVIDER_EINFRA_DISCOVER_MODELS": "true",
                },
                provider_context_window_defaults={"e-infra": 60000},
            )

        self.assertEqual(providers[0]["model_context_windows"], {"kimi": 60000, "mini": 32768})

    def test_catalogue_is_read_once_for_reasoning_and_context(self) -> None:
        response = Mock()
        response.json.return_value = {
            "data": [
                {
                    "id": "openai/gpt-5.4",
                    "context_length": 40000,
                    "reasoning": {"mandatory": True, "supported_efforts": ["high", "low"]},
                }
            ]
        }
        response.raise_for_status.return_value = None

        with patch("app.rag.llm_providers.httpx.get", return_value=response) as get:
            providers = available_llm_providers(
                {
                    "LLM_PROVIDERS": "openrouter",
                    "LLM_PROVIDER_OPENROUTER_NAME": "OpenRouter",
                    "LLM_PROVIDER_OPENROUTER_BASE_URL": "https://openrouter.ai/api/v1",
                    "LLM_PROVIDER_OPENROUTER_DEFAULT_MODEL": "openai/gpt-5.4",
                    "LLM_PROVIDER_OPENROUTER_MODELS": "openai/gpt-5.4",
                }
            )

        # Both facts come from the same records, so they cost one request.
        self.assertEqual(get.call_count, 1)
        self.assertEqual(providers[0]["model_context_windows"], {"openai/gpt-5.4": 40000})
        self.assertEqual(providers[0]["model_reasoning"]["openai/gpt-5.4"]["default"], "low")

    def test_unreachable_catalogue_leaves_reasoning_undeclared(self) -> None:
        with patch("app.rag.llm_providers.httpx.get", side_effect=RuntimeError("boom")):
            providers = available_llm_providers(
                {
                    "LLM_PROVIDERS": "openrouter",
                    "LLM_PROVIDER_OPENROUTER_NAME": "OpenRouter",
                    "LLM_PROVIDER_OPENROUTER_BASE_URL": "https://openrouter.ai/api/v1",
                    "LLM_PROVIDER_OPENROUTER_DEFAULT_MODEL": "openai/gpt-5.4",
                    "LLM_PROVIDER_OPENROUTER_MODELS": "openai/gpt-5.4",
                }
            )

        # No selector and no parameter, rather than a startup failure.
        self.assertEqual(providers[0]["model_reasoning"], {})
        self.assertEqual(providers[0]["model_presets"], ["openai/gpt-5.4"])

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
