import json
import tempfile
import threading
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import httpx
from fastapi.testclient import TestClient

import app.analytics as analytics_module
from app.analytics import AnalyticsContext, AnalyticsWriter, question_metadata
from app import main
from app.rag.llm import OpenAICompatibleLLM
from scripts.usage_report import build_report, load_events, percentile


class AnalyticsWriterTests(unittest.TestCase):
    def test_monthly_file_complete_lines_and_unique_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            writer = AnalyticsWriter(True, Path(tmp), "test")
            context = AnalyticsContext("request", "turn", "browser", "session", "ui", "test")
            now = datetime(2026, 9, 1, tzinfo=timezone.utc)
            records = [writer.event("app_open", context, status="ok") for _ in range(2)]
            # event() uses the actual clock; exercise explicit UTC rotation separately.
            writer.write({"schema_version": 1, "event": "turn", "ts": "2026-09-01T00:00:00Z"}, now=now)
            self.assertTrue((Path(tmp) / "usage-2026-09.jsonl").exists())
            self.assertNotEqual(records[0]["event_id"], records[1]["event_id"])
            current_file = next(path for path in Path(tmp).glob("usage-*.jsonl") if path.name != "usage-2026-09.jsonl")
            parsed = [json.loads(line) for line in current_file.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(parsed), 2)
            self.assertTrue(all(item["schema_version"] == 1 for item in parsed))

    def test_concurrent_writes_are_valid_json_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            writer = AnalyticsWriter(True, Path(tmp), "test")
            threads = [threading.Thread(target=lambda n=n: [writer.event("turn", value=n) for _ in range(30)]) for n in range(8)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
            path = next(Path(tmp).glob("usage-*.jsonl"))
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 240)
            self.assertEqual(len([json.loads(line) for line in lines]), 240)

    def test_disabled_and_failed_writes_do_not_escape(self):
        with tempfile.TemporaryDirectory() as tmp:
            disabled = AnalyticsWriter(False, Path(tmp), "test")
            disabled.event("turn")
            self.assertEqual(list(Path(tmp).iterdir()), [])
            writer = AnalyticsWriter(True, Path(tmp), "test")
            with patch("app.analytics.os.open", side_effect=PermissionError("no")):
                writer.event("turn")

    def test_question_classification_is_exact_and_deterministic(self):
        questions = [" First question ", "Second question"]
        first = question_metadata("First question", questions)
        repeated = question_metadata("First question", questions)
        edited = question_metadata("first question", questions)
        self.assertEqual(first["question_hash"], repeated["question_hash"])
        self.assertEqual(first["question_list_hash"], repeated["question_list_hash"])
        self.assertTrue(first["is_default_question"])
        self.assertEqual(first["prepared_question_index"], 1)
        self.assertFalse(edited["is_prepared_question"])


class AnalyticsEndpointTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.previous_writer = analytics_module._writer
        self.writer = analytics_module.configure(True, Path(self.tmp.name), "test-instance")
        self.previous_main_writer = main.analytics
        main.analytics = self.writer
        self.client = TestClient(main.app)

    def tearDown(self):
        main.analytics = self.previous_main_writer
        analytics_module._writer = self.previous_writer
        self.tmp.cleanup()

    def events(self):
        paths = list(Path(self.tmp.name).glob("usage-*.jsonl"))
        return load_events(paths)[0]

    def test_app_open_and_api_identity(self):
        response = self.client.get("/settings", headers={"X-App-Open": "1"})
        self.assertEqual(response.status_code, 200)
        event = self.events()[0]
        self.assertEqual(event["event"], "app_open")
        self.assertEqual(event["source"], "api")
        self.assertIsNone(event["client_id"])

    def test_retrieve_stream_logs_one_correlated_turn_without_text(self):
        candidates = main.pipeline.retrieve_candidates
        apply_iter = main.pipeline.apply_rerank_iter
        try:
            from app.rag.pipeline import RetrievalCandidates
            main.pipeline.retrieve_candidates = lambda *_args, **_kwargs: RetrievalCandidates([], [], False, 0.0, 0)
            main.pipeline.apply_rerank_iter = lambda *_args, **_kwargs: iter([("result", [], 0.0)])
            response = self.client.post(
                "/retrieve/stream",
                headers={"X-Client-Id": "browser-1", "X-Session-Id": "session-1", "X-Turn-Id": "turn-1"},
                json={"question": "secret question", "wp_id": "WP1-historie", "top_k": 0},
            )
        finally:
            main.pipeline.retrieve_candidates = candidates
            main.pipeline.apply_rerank_iter = apply_iter
        self.assertEqual(response.status_code, 200)
        turns = [event for event in self.events() if event["event"] == "turn"]
        self.assertEqual(len(turns), 1)
        self.assertEqual(turns[0]["turn_id"], "turn-1")
        self.assertEqual(turns[0]["source"], "ui")
        self.assertEqual(turns[0]["operation"], "retrieve_only")
        serialized = json.dumps(turns[0])
        self.assertNotIn("secret question", serialized)

    def test_blocking_and_streaming_llm_calls_are_correlated_without_text(self):
        context = AnalyticsContext("request-1", "turn-1", "browser-1", "session-1", "ui", "test-instance", "provider-1", "server", "answer")
        client = OpenAICompatibleLLM("server-secret-key", "requested-model", "https://provider.example/v1")
        blocking_response = httpx.Response(
            200,
            request=httpx.Request("POST", "https://provider.example/v1/chat/completions"),
            json={"model": "served-model", "choices": [{"message": {"content": "secret answer"}}]},
        )
        from app.analytics import bind_context
        with bind_context(context):
            with patch("app.rag.llm.httpx.post", return_value=blocking_response):
                client.generate([{"role": "user", "content": "secret prompt"}])

        def stream_handler(request):
            return httpx.Response(
                200,
                request=request,
                text='data: {"model":"served-stream","choices":[{"delta":{"content":"token"}}]}\n\ndata: [DONE]\n\n',
                headers={"content-type": "text/event-stream"},
            )

        real_client = httpx.Client(transport=httpx.MockTransport(stream_handler))
        with bind_context(context):
            with patch("app.rag.llm.httpx.Client", return_value=real_client):
                self.assertEqual(list(client.stream_generate([{"role": "user", "content": "another secret"}])), ["token"])
        calls = [event for event in self.events() if event["event"] == "upstream_call"]
        self.assertEqual(len(calls), 2)
        self.assertEqual({event["streaming"] for event in calls}, {False, True})
        self.assertTrue(all(event["turn_id"] == "turn-1" for event in calls))
        self.assertTrue(all(event["purpose"] == "answer" for event in calls))
        serialized = json.dumps(calls)
        for secret in ("secret prompt", "secret answer", "another secret", "server-secret-key"):
            self.assertNotIn(secret, serialized)

    def test_chat_stream_context_survives_worker_context_changes(self):
        from app.rag.pipeline import RetrievalCandidates

        def stream_handler(request):
            return httpx.Response(
                200,
                request=request,
                text=(
                    'data: {"model":"served-stream","choices":[{"delta":{"content":"first "}}]}\n\n'
                    'data: {"model":"served-stream","choices":[{"delta":{"content":"second"}}]}\n\n'
                    "data: [DONE]\n\n"
                ),
                headers={"content-type": "text/event-stream"},
            )

        real_client = httpx.Client(transport=httpx.MockTransport(stream_handler))
        with (
            patch("app.main._resolve_llm_request", return_value=(
                "provider-1", "requested-model", "server-key", "https://provider.example/v1"
            )),
            patch("app.main._enforce_msearch_collection_policy"),
            patch("app.main._enforce_retrieval_backend_policy"),
            patch.object(
                main.pipeline,
                "retrieve_candidates",
                return_value=RetrievalCandidates([], [], False, 0.0, 0),
            ),
            patch.object(
                main.pipeline,
                "apply_rerank_iter",
                return_value=iter([("result", [], 0.0)]),
            ),
            patch("app.rag.llm.httpx.Client", return_value=real_client),
        ):
            response = self.client.post(
                "/chat/stream",
                headers={
                    "X-Client-Id": "browser-1",
                    "X-Session-Id": "session-1",
                    "X-Turn-Id": "turn-stream-1",
                },
                json={"question": "secret question", "wp_id": "WP1-historie", "top_k": 0},
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn("event: done", response.text)
        self.assertNotIn("event: error", response.text)
        self.assertIn('"answer": "first second"', response.text)
        events = self.events()
        turns = [event for event in events if event["event"] == "turn"]
        calls = [event for event in events if event["event"] == "upstream_call"]
        self.assertEqual(len(turns), 1)
        self.assertEqual(turns[0]["status"], "ok")
        self.assertEqual(turns[0]["turn_id"], "turn-stream-1")
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["status"], "ok")
        self.assertEqual(calls[0]["turn_id"], "turn-stream-1")
        self.assertEqual(calls[0]["purpose"], "answer")

    def test_chat_stream_logs_policy_rejection(self):
        from fastapi import HTTPException

        with (
            patch("app.main._resolve_llm_request", return_value=(
                "openrouter", "requested-model", "server-key", "https://openrouter.ai/api/v1"
            )),
            patch(
                "app.main._enforce_msearch_collection_policy",
                side_effect=HTTPException(status_code=400, detail="Provider is not allowed for this WP."),
            ),
        ):
            response = self.client.post(
                "/chat/stream",
                headers={
                    "X-Client-Id": "browser-1",
                    "X-Session-Id": "session-1",
                    "X-Turn-Id": "turn-policy-1",
                },
                json={"question": "secret question", "wp_id": "WP2-média", "top_k": 10},
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn("event: error", response.text)
        events = self.events()
        turns = [event for event in events if event["event"] == "turn"]
        calls = [event for event in events if event["event"] == "upstream_call"]
        self.assertEqual(len(turns), 1)
        self.assertEqual(turns[0]["status"], "error")
        self.assertEqual(turns[0]["error_code"], "policy_rejected")
        self.assertEqual(turns[0]["http_status"], 200)
        self.assertEqual(turns[0]["turn_id"], "turn-policy-1")
        self.assertEqual(calls, [])


class UsageReportTests(unittest.TestCase):
    def test_report_counts_percentiles_and_skips_bad_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "usage.jsonl"
            path.write_text(
                "\n".join([
                    json.dumps({"schema_version": 1, "event": "app_open", "ts": "2026-08-01T00:00:00Z", "client_id": "b1", "session_id": "s1"}),
                    json.dumps({"schema_version": 1, "event": "turn", "ts": "2026-08-01T00:00:01Z", "wp_id": "WP1", "operation": "chat", "status": "ok", "total_ms": 10, "question_chars": 4}),
                    json.dumps({"schema_version": 1, "event": "turn", "ts": "2026-08-01T00:00:02Z", "wp_id": "WP1", "operation": "chat", "status": "ok", "total_ms": 100, "question_chars": 8}),
                    "not json",
                    json.dumps({"schema_version": 99, "event": "turn"}),
                ]) + "\n",
                encoding="utf-8",
            )
            events, skipped = load_events([path])
            report = build_report(events, skipped)
        self.assertEqual(report["event_count"], 3)
        self.assertEqual(report["skipped_lines"], 2)
        self.assertEqual(percentile([10, 100], .5), 10)
        timing = next(row for row in report["rows"] if row.get("section") == "timings" and row.get("metric") == "total_ms")
        self.assertEqual(timing["p95"], 100)


if __name__ == "__main__":
    unittest.main()
