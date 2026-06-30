import unittest

from app.config import get_settings
from app.rag.llm import LLMGeneration
from app.rag.pipeline import RAGPipeline


class _FakeLLM:
    model = "fake-model"

    def __init__(self, answer: str = "rewritten query") -> None:
        self.answer = answer
        self.calls = []

    def generate(self, messages, model=None, api_key=None, base_url=None):
        self.calls.append(
            {
                "messages": messages,
                "model": model,
                "api_key": api_key,
                "base_url": base_url,
            }
        )
        return LLMGeneration(answer=self.answer, model=model)


class RetrievalQueryRewriteTests(unittest.TestCase):
    def _pipeline(self, answer: str = "rewritten query") -> tuple[RAGPipeline, _FakeLLM]:
        pipeline = RAGPipeline(get_settings())
        llm = _FakeLLM(answer)
        pipeline._llm = llm
        return pipeline, llm

    def test_disabled_returns_original_question_without_llm_call(self) -> None:
        pipeline, llm = self._pipeline()

        query = pipeline.rewrite_query_for_retrieval(
            "A co potom?",
            conversation_history=[{"role": "user", "content": "Mluvili jsme o Janu Husovi."}],
            conversation_summary=None,
            enabled=False,
            model="selected-model",
            api_key="key",
            base_url="https://example.test/v1",
        )

        self.assertEqual(query, "A co potom?")
        self.assertEqual(llm.calls, [])

    def test_first_conversation_message_returns_original_question(self) -> None:
        pipeline, llm = self._pipeline()

        query = pipeline.rewrite_query_for_retrieval(
            "Kdo byl Jan Hus?",
            conversation_history=[],
            conversation_summary=None,
            enabled=True,
            model="selected-model",
            api_key="key",
            base_url="https://example.test/v1",
        )

        self.assertEqual(query, "Kdo byl Jan Hus?")
        self.assertEqual(llm.calls, [])

    def test_uses_same_model_and_recent_conversation_for_rewrite(self) -> None:
        pipeline, llm = self._pipeline('"Jan Hus a jeho vliv"')

        query = pipeline.rewrite_query_for_retrieval(
            "A jaký měl vliv?",
            conversation_history=[
                {"role": "user", "content": "Kdo byl Jan Hus?"},
                {"role": "assistant", "content": "Jan Hus byl český reformátor."},
            ],
            conversation_summary="Konverzace je o Janu Husovi.",
            enabled=True,
            model="selected-model",
            api_key="key",
            base_url="https://example.test/v1",
        )

        self.assertEqual(query, "Jan Hus a jeho vliv")
        self.assertEqual(len(llm.calls), 1)
        self.assertEqual(llm.calls[0]["model"], "selected-model")
        self.assertEqual(llm.calls[0]["api_key"], "key")
        self.assertEqual(llm.calls[0]["base_url"], "https://example.test/v1")
        prompt = llm.calls[0]["messages"][1]["content"]
        self.assertIn("Konverzace je o Janu Husovi.", prompt)
        self.assertIn("Jan Hus byl český reformátor.", prompt)
        self.assertIn("A jaký měl vliv?", prompt)


if __name__ == "__main__":
    unittest.main()
