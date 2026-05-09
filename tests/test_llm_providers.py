import unittest

from app.rag.llm_providers import available_llm_providers, load_provider_configs, provider_api_key


class LLMProviderTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
