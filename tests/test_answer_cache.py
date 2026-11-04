import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app import auth, main
from app.accounts import AccountStore, LoginThrottle
from app.answer_cache import (
    KEY_EXCLUDED_FIELDS,
    REPLAY_MAX_SECONDS,
    REPLAY_MIN_SECONDS,
    AnswerCache,
    cache_key,
    key_input,
    replay_pieces,
)
from app.models import ChatRequest
from app.rag.llm import ANSWER, REASONING
from app.rag.pipeline import RetrievalCandidates

# Every ChatRequest field that is part of the cache key. A new field must be
# added here or to KEY_EXCLUDED_FIELDS: forgetting it in the key would serve
# one answer for requests that differ in it.
KEY_FIELDS = {
    "question",
    "retrieval_query",
    "use_retrieval_query_for_answer",
    "wp_id",
    "use_sources",
    "rewrite_query_for_retrieval",
    "selections",
    "placeholder_defs",
    "system_prompt",
    "user_prompt_template",
    "conversation_history",
    "conversation_summary",
    "context_window_tokens",
    "output_token_budget_short",
    "output_token_budget_medium",
    "output_token_budget_long",
    "min_prompt_chunks",
    "token_budget_safety_margin",
    "conversation_summary_trigger_tokens",
    "reasoning_effort",
    "top_k",
    "retrieval_backend",
    "llm_provider",
    "msearch_collection",
    "msearch_mode",
    "msearch_min_confidence",
    "msearch_rescore",
    "model",
    "llm_base_url",
    "dense_weight",
    "bm25_weight",
    "min_score",
    "min_relative_score",
    "rerank_enabled",
    "rerank_weight",
    "rerank_candidates",
}


class KeyTests(unittest.TestCase):
    def test_every_request_field_is_classified(self) -> None:
        fields = set(ChatRequest.model_fields)
        self.assertEqual(fields - KEY_FIELDS - KEY_EXCLUDED_FIELDS, set(), "classify the new field")
        self.assertEqual(KEY_FIELDS & KEY_EXCLUDED_FIELDS, set())
        self.assertEqual((KEY_FIELDS | KEY_EXCLUDED_FIELDS) - fields, set(), "drop the removed field")

    def test_excluded_fields_do_not_change_the_key(self) -> None:
        plain = ChatRequest(question="Kdo byl Hus?")
        other = ChatRequest(
            question="Kdo byl Hus?",
            llm_api_key="sk-secret",
            admin_password="heslo",
            prompt_preset_id="preset-1",
            query_transform_ms=120,
            query_transform_kind="llm",
            bypass_cache=True,
        )
        self.assertEqual(cache_key(key_input(plain)), cache_key(key_input(other)))
        self.assertNotIn("sk-secret", json.dumps(key_input(other)))

    def test_key_fields_and_resolved_values_change_the_key(self) -> None:
        base = cache_key(key_input(ChatRequest(question="Kdo byl Hus?"), model="a"))
        self.assertNotEqual(base, cache_key(key_input(ChatRequest(question="Kdo byl Žižka?"), model="a")))
        self.assertNotEqual(base, cache_key(key_input(ChatRequest(question="Kdo byl Hus?", top_k=3), model="a")))
        self.assertNotEqual(base, cache_key(key_input(ChatRequest(question="Kdo byl Hus?"), model="b")))

    def test_key_does_not_depend_on_dict_order(self) -> None:
        first = ChatRequest(question="q", selections={"length": "short", "custom_instructions": "x"})
        second = ChatRequest(question="q", selections={"custom_instructions": "x", "length": "short"})
        self.assertEqual(cache_key(key_input(first)), cache_key(key_input(second)))


class ReplayTests(unittest.TestCase):
    def test_pieces_rebuild_the_answer(self) -> None:
        answer = "  První věta. [1]\n\nDruhá  věta…\n"
        pieces, _ = replay_pieces(answer)
        self.assertEqual("".join(pieces), answer)
        self.assertEqual(replay_pieces(""), ([], 0.0))

    def test_duration_is_clamped(self) -> None:
        pieces, pause = replay_pieces("krátká odpověď")
        self.assertAlmostEqual(pause * len(pieces), REPLAY_MIN_SECONDS)
        pieces, pause = replay_pieces("slovo " * 2000)
        self.assertAlmostEqual(pause * len(pieces), REPLAY_MAX_SECONDS)


class StoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.cache = AnswerCache(Path(self.tmp.name) / "cache.sqlite3", ttl_seconds=100, max_entries=2)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_round_trip_counts_hits(self) -> None:
        self.cache.put("k", {"question": "q"}, {"answer": "odpověď"}, now=1000)
        self.assertTrue(self.cache.contains("k", now=1001))
        self.assertEqual(self.cache.get("k", now=1001), {"answer": "odpověď", "cached_at": 1000})
        self.assertIsNone(self.cache.get("missing"))
        with self.cache._connect() as conn:
            row = conn.execute("SELECT hit_count, last_hit_at FROM answers").fetchone()
        self.assertEqual((row["hit_count"], row["last_hit_at"]), (1, 1001))

    def test_entries_expire_unless_pinned(self) -> None:
        self.cache.put("old", {}, {"answer": "a"}, now=1000)
        self.cache.put("warm", {}, {"answer": "b"}, pinned=True, now=1000)
        self.assertIsNone(self.cache.get("old", now=1101))
        self.assertIsNotNone(self.cache.get("warm", now=99999))

    def test_least_recently_used_is_evicted_but_pinned_stays(self) -> None:
        self.cache.put("pinned", {}, {"answer": "p"}, pinned=True, now=1)
        self.cache.put("a", {}, {"answer": "a"}, now=2)
        self.cache.put("b", {}, {"answer": "b"}, now=3)
        self.cache.get("a", now=4)
        self.cache.put("c", {}, {"answer": "c"}, now=5)
        self.assertEqual(
            {key for key in ("pinned", "a", "b", "c") if self.cache.contains(key, now=6)},
            {"pinned", "a", "c"},
        )

    def test_overwrite_keeps_a_pinned_entry_pinned(self) -> None:
        self.cache.put("k", {}, {"answer": "old"}, pinned=True, now=1)
        self.cache.put("k", {}, {"answer": "new"}, now=2)
        self.assertEqual(self.cache.get("k", now=99999)["answer"], "new")
        self.assertEqual(self.cache.count(), 1)

    def test_pin_keeps_an_entry(self) -> None:
        self.cache.put("k", {}, {"answer": "a"}, now=1000)
        self.assertTrue(self.cache.pin("k"))
        self.assertFalse(self.cache.pin("missing"))
        self.assertIsNotNone(self.cache.get("k", now=99999))


class FakeStream:
    """Like the LLM stream: yields the parts, then carries the whole trace."""

    def __init__(self, parts, finish_reason="stop") -> None:
        self.parts = list(parts)
        self.finish_reason = finish_reason
        self.reasoning_text = "".join(text for kind, text in self.parts if kind == REASONING)

    def __iter__(self):
        return iter(self.parts)


class EndpointTestCase(unittest.TestCase):
    """/chat/stream against a temporary cache, with retrieval and the LLM faked."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.cache = AnswerCache(Path(self.tmp.name) / "cache.sqlite3", ttl_seconds=3600, max_entries=100)
        self.generated: list[list] = []
        self.answer = [(REASONING, "Přemýšlím."), (ANSWER, "Jan Hus byl "), (ANSWER, "kazatel [1].")]
        self.finish_reason = "stop"
        self.patches = [
            patch.object(main, "_get_answer_cache", lambda: self.cache),
            patch.object(main, "_replay_sleep", lambda _seconds: None),
            patch.object(main, "_resolve_llm_request", return_value=(
                "test", "test-model", "test-key", "https://llm.test.invalid/v1"
            )),
            patch.object(main, "_enforce_msearch_collection_policy"),
            patch.object(main, "_enforce_retrieval_backend_policy"),
            patch.object(main.pipeline, "retrieve_candidates", side_effect=self.retrieve),
            patch.object(main.pipeline, "apply_rerank_iter", side_effect=lambda *_: iter([("result", [], 0.0)])),
            patch.object(main.pipeline.llm, "stream_generate", side_effect=self.generate),
        ]
        for item in self.patches:
            item.start()
        self.retrievals = 0
        self.client = TestClient(main.app)

    def tearDown(self) -> None:
        for item in reversed(self.patches):
            item.stop()
        self.tmp.cleanup()

    def retrieve(self, *_args, **_kwargs):
        self.retrievals += 1
        return RetrievalCandidates([], [], False, 0.0, 0)

    def generate(self, messages, **_kwargs):
        self.generated.append(messages)
        return FakeStream(self.answer, self.finish_reason)

    def ask(self, **body):
        response = self.client.post("/chat/stream", json={"question": "Kdo byl Jan Hus?", **body})
        self.assertEqual(response.status_code, 200, response.text)
        events = []
        for block in response.text.strip().split("\n\n"):
            lines = block.split("\n")
            name = lines[0].removeprefix("event: ")
            data = json.loads("\n".join(line.removeprefix("data: ") for line in lines[1:]))
            events.append((name, data))
        return events

    def done(self, events):
        return next(data for name, data in events if name == "done")


class EndpointTests(EndpointTestCase):
    def test_second_identical_request_is_replayed(self) -> None:
        first = self.ask()
        self.assertFalse(self.done(first)["cache_hit"])
        second = self.ask(llm_api_key="sk-other", prompt_preset_id="whatever")
        self.assertEqual((len(self.generated), self.retrievals), (1, 1))
        done = self.done(second)
        self.assertTrue(done["cache_hit"])
        self.assertEqual(done["answer"], "Jan Hus byl kazatel [1].")
        self.assertEqual(done["reasoning"], "Přemýšlím.")
        self.assertEqual(done["model"], "test-model")
        self.assertEqual(done["retrieved_chunks"], done["used_chunks"])
        names = [name for name, _ in second]
        self.assertEqual(names[:2], ["sources", "reasoning"])
        self.assertEqual(names[-1], "done")
        tokens = "".join(data["text"] for name, data in second if name == "token")
        self.assertEqual(tokens, done["answer"])

    def test_bypass_generates_again_and_overwrites(self) -> None:
        self.ask()
        self.answer = [(ANSWER, "Nová odpověď.")]
        regenerated = self.ask(bypass_cache=True)
        self.assertFalse(self.done(regenerated)["cache_hit"])
        self.assertEqual(len(self.generated), 2)
        self.assertEqual(self.done(self.ask())["answer"], "Nová odpověď.")
        self.assertEqual(self.cache.count(), 1)

    def test_key_is_announced_and_stored_before_done(self) -> None:
        events = self.ask()
        sources = next(data for name, data in events if name == "sources")
        done = self.done(events)
        self.assertEqual((sources["cache_hit"], sources["cache_key"]), (False, done["cache_key"]))
        self.assertTrue(self.cache.contains(done["cache_key"]))
        replayed = self.ask()
        self.assertEqual(next(data for name, data in replayed if name == "sources")["cache_key"], done["cache_key"])

    def test_omitted_defaults_share_the_entry(self) -> None:
        self.ask()
        settings = main.settings
        self.ask(
            top_k=settings.top_k,
            msearch_mode=settings.msearch_mode,
            min_relative_score=settings.min_relative_score,
            context_window_tokens=settings.context_window_tokens,
            selections={"length": "medium"},
            reasoning_effort="",
        )
        self.assertEqual(len(self.generated), 1)

    def test_different_settings_miss(self) -> None:
        self.ask()
        self.ask(top_k=3)
        self.ask(selections={"length": "long"})
        self.assertEqual(len(self.generated), 3)

    def test_follow_up_turns_are_not_cached(self) -> None:
        history = [{"role": "user", "content": "Ahoj"}, {"role": "assistant", "content": "Dobrý den"}]
        self.ask(conversation_history=history)
        self.ask(conversation_history=history)
        self.assertEqual(len(self.generated), 2)
        self.assertEqual(self.cache.count(), 0)

    def test_empty_or_failed_answer_is_not_cached(self) -> None:
        self.answer = [(ANSWER, "   ")]
        self.ask()
        self.assertEqual(self.cache.count(), 0)

        def failing(messages, **_kwargs):
            yield ANSWER, "Začátek"
            raise RuntimeError("upstream died")

        with patch.object(main.pipeline.llm, "stream_generate", side_effect=failing):
            events = self.ask()
        self.assertIn("error", [name for name, _ in events])
        self.assertEqual(self.cache.count(), 0)

    def test_a_cut_answer_is_shown_with_a_warning_but_not_cached(self) -> None:
        for reason in ("length", None):
            self.finish_reason = reason
            done = self.done(self.ask())
            self.assertEqual(done["answer"], "Jan Hus byl kazatel [1].")
            self.assertEqual(done["finish_reason"], reason)
            self.assertIn("nebyla dokončena", done["chunk_budget_warnings"][-1])
            self.assertEqual(self.cache.count(), 0)
        self.finish_reason = "stop"
        done = self.done(self.ask())
        self.assertEqual((done["finish_reason"], done["chunk_budget_warnings"]), ("stop", []))
        self.assertEqual(self.cache.count(), 1)

    def test_policy_is_checked_on_a_hit(self) -> None:
        from fastapi import HTTPException

        self.ask()
        with patch.object(
            main,
            "_enforce_msearch_collection_policy",
            side_effect=HTTPException(status_code=400, detail="Not allowed."),
        ):
            events = self.ask()
        self.assertEqual(events, [("error", {"detail": "Not allowed."})])

    def test_model_access_is_checked_before_the_lookup(self) -> None:
        from fastapi import HTTPException

        self.ask()
        with patch.object(
            main, "_resolve_llm_request", side_effect=HTTPException(status_code=400, detail="Needs a key.")
        ):
            events = self.ask()
        self.assertEqual(events, [("error", {"detail": "Needs a key."})])

    def test_hit_is_logged_as_a_turn(self) -> None:
        with patch.object(main.analytics, "event") as event:
            self.ask()
            self.ask()
        turns = [call.kwargs for call in event.call_args_list if call.args[0] == "turn"]
        self.assertEqual([turn["cache_hit"] for turn in turns], [False, True])
        self.assertEqual([turn["status"] for turn in turns], ["ok", "ok"])


class QuotaTests(EndpointTestCase):
    """With accounts on, only answers that call the LLM count."""

    def setUp(self) -> None:
        super().setUp()
        self.store = AccountStore(Path(self.tmp.name) / "users.sqlite3")
        auth.set_store(self.store)
        self.auth_patches = [
            patch.object(main.settings, "auth_enabled", True),
            patch.object(main.settings, "user_daily_request_limit", 1),
            patch.object(auth, "login_throttle", LoginThrottle()),
        ]
        for item in self.auth_patches:
            item.start()
        self.client = TestClient(main.app, base_url="https://testserver")
        self.user = self.store.create_user("jan@seznam.cz", "user password")
        self.client.post("/auth/login", json={"email": "jan@seznam.cz", "password": "user password"})

    def tearDown(self) -> None:
        for item in reversed(self.auth_patches):
            item.stop()
        auth.set_store(None)
        super().tearDown()

    def test_hits_do_not_count(self) -> None:
        first = self.client.post("/chat/stream", json={"question": "Kdo byl Jan Hus?"})
        self.assertEqual(first.headers[auth.QUOTA_HEADER], "0")
        for _ in range(2):
            hit = self.client.post("/chat/stream", json={"question": "Kdo byl Jan Hus?"})
            self.assertEqual(hit.status_code, 200)
            self.assertIn('"cache_hit": true', hit.text)
            self.assertNotIn(auth.QUOTA_HEADER, hit.headers)
        self.assertEqual(self.store.requests_today(self.user.id), 1)
        miss = self.client.post("/chat/stream", json={"question": "Kdo byl Žižka?"})
        self.assertEqual(miss.status_code, 429)
        self.assertEqual(miss.headers[auth.QUOTA_HEADER], "0")
        # Regenerating calls the LLM, so it counts too.
        regenerate = self.client.post("/chat/stream", json={"question": "Kdo byl Jan Hus?", "bypass_cache": True})
        self.assertEqual(regenerate.status_code, 429)


if __name__ == "__main__":
    unittest.main()
