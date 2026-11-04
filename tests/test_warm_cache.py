import argparse
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app import main
from app.rag.prompts import default_system_prompt_template, default_user_prompt_template
from app.cache_warming import Job, interleave_by_model, request_body, select_profiles, warm
from scripts.warm_cache import build_jobs, build_parser, load_options
from tests.test_answer_cache import EndpointTestCase

QUESTION = "Kdo byl Jan Hus?"


def browser_body(app_settings, wp, profile, provider, question):
    """What buildRequestPayload in app.js sends for a first turn with the
    default settings: everything explicit, defaults included."""

    def override(value, default):
        current = (value or "").strip()
        return None if not current or current == default.strip() else current

    defaults = app_settings["prompt_defaults"]
    budgets = app_settings["token_budget_defaults"]
    retrieval = app_settings["retrieval_defaults"]
    msearch = app_settings["msearch_defaults"]
    shared_defs = {record["name"]: record for record in app_settings["placeholders"]}
    effective_defs = {**shared_defs, **(profile.get("placeholders") or {})}
    model = provider["default_model"]
    collections = wp["collections"]
    collection = next(c for c in collections if c["id"] == wp["default_collection_id"])
    return {
        "question": question,
        "wp_id": wp["id"],
        "prompt_preset_id": profile["id"],
        "prompt_preset_name": profile["name"],
        "selections": {name: definition.get("default", "") for name, definition in effective_defs.items()},
        "placeholder_defs": effective_defs,
        "system_prompt": override(profile.get("system_prompt"), defaults["system_prompt"]),
        "user_prompt_template": override(profile.get("user_prompt_template"), defaults["user_prompt_template"]),
        "conversation_history": [],
        "context_window_tokens": (
            provider["model_context_windows"].get(model)
            or app_settings["model_context_windows"].get(model)
            or provider.get("default_context_window_tokens")
            or budgets["context_window_tokens"]
        ),
        "output_token_budget_short": budgets["output_token_budget_short"],
        "output_token_budget_medium": budgets["output_token_budget_medium"],
        "output_token_budget_long": budgets["output_token_budget_long"],
        "min_prompt_chunks": budgets["min_prompt_chunks"],
        "token_budget_safety_margin": budgets["token_budget_safety_margin"],
        "conversation_summary_trigger_tokens": budgets["conversation_summary_trigger_tokens"],
        "model": model,
        "llm_provider": provider["id"],
        "llm_base_url": provider["base_url"],
        "llm_api_key": None,
        "reasoning_effort": None,
        "admin_password": None,
        "top_k": msearch["max_results"],
        "retrieval_backend": "msearch",
        "msearch_collection": collection["msearch_collection_id"],
        "msearch_mode": "hybrid",
        "msearch_min_confidence": msearch["min_confidence"],
        "msearch_rescore": retrieval["msearch_rescore"],
        "min_relative_score": retrieval["min_relative_score"],
        "rerank_enabled": False,
    }


class WarmTestCase(EndpointTestCase):
    def setUp(self) -> None:
        super().setUp()
        live = patch.object(main.pipeline.msearch_retriever, "live_collections_by_prefix", return_value={})
        live.start()
        self.addCleanup(live.stop)
        self.app_settings = self.client.get("/settings").json()
        self.provider = self.app_settings["llm_providers"][0]

    def stream(self, body):
        response = self.client.post("/chat/stream", json=body)
        self.assertEqual(response.status_code, 200, response.text)
        yield from response.text.split("\n")

    def job(self, wp, profile, question=QUESTION):
        body = request_body(self.app_settings, wp, profile, self.provider, "", question, None)
        return Job(wp["id"], profile["id"], body["model"], question, body)


class KeyEqualityTests(WarmTestCase):
    def test_script_request_hits_the_browser_entry(self) -> None:
        for wp in self.app_settings["wps"]:
            for profile in wp["builtin_prompts"]:
                with self.subTest(wp=wp["id"], profile=profile["id"]):
                    browser = self.done(self.ask(**browser_body(self.app_settings, wp, profile, self.provider, QUESTION)))
                    self.assertFalse(browser["cache_hit"])
                    events = self.ask(**self.job(wp, profile).body)
                    sources = next(data for name, data in events if name == "sources")
                    self.assertTrue(sources["cache_hit"])
                    self.assertEqual(sources["cache_key"], browser["cache_key"])

    def test_profiles_and_wps_do_not_share_entries(self) -> None:
        keys = set()
        for wp in self.app_settings["wps"]:
            for profile in wp["builtin_prompts"]:
                keys.add(self.done(self.ask(**self.job(wp, profile).body))["cache_key"])
        self.assertEqual(len(keys), sum(len(wp["builtin_prompts"]) for wp in self.app_settings["wps"]))


class WarmTests(WarmTestCase):
    def setUp(self) -> None:
        super().setUp()
        wp = self.app_settings["wps"][0]
        self.warm_job = self.job(wp, wp["builtin_prompts"][0])

    def pinned(self, key):
        with self.cache._connect() as conn:
            return conn.execute("SELECT pinned FROM answers WHERE key = ?", (key,)).fetchone()["pinned"]

    def test_generates_pins_and_then_finds_it(self) -> None:
        self.assertEqual(warm(self.stream, self.cache, self.warm_job, force=False), "vygenerováno")
        key = self.done(self.ask(**self.warm_job.body))["cache_key"]
        self.assertEqual(self.pinned(key), 1)
        self.assertEqual(warm(self.stream, self.cache, self.warm_job, force=False), "v mezipaměti")
        self.assertEqual(len(self.generated), 1)

    def test_force_regenerates(self) -> None:
        warm(self.stream, self.cache, self.warm_job, force=False)
        self.assertEqual(warm(self.stream, self.cache, self.warm_job, force=True), "vygenerováno")
        self.assertEqual(len(self.generated), 2)

    def test_hit_disconnects_after_the_first_event(self) -> None:
        warm(self.stream, self.cache, self.warm_job, force=False)
        read = []

        def stream(body):
            for line in self.stream(body):
                read.append(line)
                yield line

        warm(stream, self.cache, self.warm_job, force=False)
        self.assertFalse(any(line.startswith("event: token") for line in read))

    def test_failures_are_reported(self) -> None:
        self.answer = []
        self.assertEqual(warm(self.stream, self.cache, self.warm_job, force=False), "chyba: prázdná odpověď")
        with patch.object(main, "_get_answer_cache", lambda: None):
            self.answer = [("answer", "Odpověď.")]
            status = warm(self.stream, self.cache, self.warm_job, force=False)
        self.assertTrue(status.startswith("chyba: záznam v mezipaměti nenalezen"), status)


WP = {
    "id": "WP1",
    "default_prompt_id": "b2",
    "default_collection_id": "c1",
    "collections": [{"id": "c0", "msearch_collection_id": "m0"}, {"id": "c1", "msearch_collection_id": "m1"}],
    "builtin_prompts": [
        {"id": "b1", "name": "B1", "system_prompt": "s1", "user_prompt_template": "u1"},
        {"id": "b2", "name": "B2", "system_prompt": "s2", "user_prompt_template": "u2"},
    ],
}
SHARED = [
    {"id": "p1", "name": "P1", "wp_id": "WP1", "system_prompt": "s", "user_prompt_template": "u"},
    {"id": "p2", "name": "P2", "wp_id": "WP2", "system_prompt": "s", "user_prompt_template": "u"},
]


class SelectionTests(unittest.TestCase):
    def ids(self, *wanted):
        return [profile["id"] for profile in select_profiles(WP, SHARED, wanted)]

    def test_profile_selection(self) -> None:
        self.assertEqual(self.ids("default"), ["b2"])
        self.assertEqual(self.ids("builtin"), ["b1", "b2"])
        self.assertEqual(self.ids("shared"), ["p1"])
        self.assertEqual(self.ids("all"), ["b1", "b2", "p1"])
        self.assertEqual(self.ids("p1", "default", "p2", "missing"), ["p1", "b2"])

    def test_jobs_cover_wps_profiles_models_and_questions(self) -> None:
        app_settings = {
            "wps": [WP, {**WP, "id": "WP2"}],
            "llm_provider": "test",
            "llm_providers": [{"id": "test", "default_model": "m", "model_context_windows": {"m2": 4096}}],
            "model_context_windows": {},
            "token_budget_defaults": {"context_window_tokens": 2048},
            "retrieval_defaults": {"msearch_rescore": True},
            "msearch_defaults": {"max_results": 7},
            "top_k": 5,
        }
        responses = {"/settings": app_settings, "/prompt-presets": SHARED}

        def fetch(path, params):
            if path == "/questions":
                return {"questions": [f"{params['wp_id']} q1", f"{params['wp_id']} q2"]}
            return responses[path]

        options = {"wp": ["WP1"], "questions": "prepared", "profile": ["all"], "provider": None, "model": ["m", "m2"]}
        jobs = build_jobs(fetch, options, "secret")
        self.assertEqual(len(jobs), 3 * 2 * 2)
        self.assertEqual({job.wp_id for job in jobs}, {"WP1"})
        body = next(job.body for job in jobs if job.profile_id == "b1" and job.model == "m2")
        self.assertEqual(
            {name: body[name] for name in ("msearch_collection", "context_window_tokens", "top_k", "msearch_rescore", "admin_password")},
            {"msearch_collection": "m1", "context_window_tokens": 4096, "top_k": 7, "msearch_rescore": True, "admin_password": "secret"},
        )
        self.assertEqual(next(job.body for job in jobs if job.model == "m")["context_window_tokens"], 2048)
        with self.assertRaises(SystemExit):
            build_jobs(fetch, {**options, "wp": ["WP9"]}, None)


class OptionTests(unittest.TestCase):
    def test_command_line_wins_over_the_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "warm.json"
            config.write_text(json.dumps({"wp": ["WP2"], "model": ["a"], "url": "http://x"}), encoding="utf-8")
            options = load_options(build_parser().parse_args(["--config", str(config), "--model", "b"]))
            self.assertEqual((options["wp"], options["model"], options["url"]), (["WP2"], ["b"], "http://x"))
            self.assertEqual(options["profile"], ["default"])
            config.write_text(json.dumps({"modle": ["a"]}), encoding="utf-8")
            with self.assertRaises(SystemExit):
                load_options(build_parser().parse_args(["--config", str(config)]))

    def test_the_example_config_is_valid(self) -> None:
        example = Path(__file__).resolve().parents[1] / "scripts" / "warm_cache.example.json"
        options = load_options(argparse.Namespace(config=str(example), **{name: None for name in
                               ("url", "wp", "questions", "profile", "provider", "model", "concurrency")}))
        self.assertEqual(options["wp"], ["all"])
