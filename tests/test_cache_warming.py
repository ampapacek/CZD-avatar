import logging
import threading
import unittest
from unittest.mock import patch

from app import main
from app.cache_warming import CACHED, GENERATED, Job, WarmRun, interleave_by_model
from app.rag.llm import OpenAICompatibleLLM, llm_timeout
from tests.test_answer_cache_admin import ADMIN, AdminTestCase


def job(model, question="q"):
    return Job("WP1", "p", model, question, {})


class InterleaveTests(unittest.TestCase):
    def test_round_robin_over_models_keeping_their_order(self) -> None:
        jobs = [job("a", "1"), job("a", "2"), job("a", "3"), job("b", "1"), job("c", "1"), job("c", "2")]
        self.assertEqual(
            [(item.model, item.question) for item in interleave_by_model(jobs)],
            [("a", "1"), ("b", "1"), ("c", "1"), ("a", "2"), ("c", "2"), ("a", "3")],
        )
        self.assertEqual(interleave_by_model([]), [])


class WarmRunTests(unittest.TestCase):
    def test_runs_every_job_and_counts_the_outcomes(self) -> None:
        outcomes = {"1": GENERATED, "2": CACHED, "3": "chyba: nic", "4": GENERATED}

        def run_job(item):
            if item.question == "5":
                raise RuntimeError("boom")
            return outcomes[item.question]

        run = WarmRun([job("m", str(index)) for index in range(1, 6)], run_job, concurrency=3)
        run.start()
        run.join(5)
        status = run.snapshot()
        self.assertEqual(
            {name: status[name] for name in ("state", "total", "done", "running", "pending", "generated", "cached", "failed")},
            {"state": "finished", "total": 5, "done": 5, "running": 0, "pending": 0, "generated": 2, "cached": 1, "failed": 2},
        )
        self.assertEqual(sorted(error["error"] for error in status["errors"]), ["boom", "nic"])

    def test_concurrency_is_bounded(self) -> None:
        self.assertEqual(WarmRun([], lambda _: GENERATED, concurrency=50).concurrency, 20)
        run = WarmRun([], lambda _: GENERATED, concurrency=0)
        self.assertEqual(run.concurrency, 1)
        run.start()
        self.assertEqual(run.snapshot()["state"], "finished")

    def test_cancel_drops_pending_jobs_and_lets_running_ones_finish(self) -> None:
        started, release = threading.Semaphore(0), threading.Event()

        def run_job(_item):
            started.release()
            release.wait(5)
            return GENERATED

        run = WarmRun([job("m", str(index)) for index in range(10)], run_job, concurrency=2)
        run.start()
        started.acquire(timeout=5)
        started.acquire(timeout=5)
        self.assertEqual({name: run.snapshot()[name] for name in ("state", "running", "pending")},
                         {"state": "running", "running": 2, "pending": 8})
        run.cancel()
        self.assertEqual(run.snapshot()["state"], "running")
        release.set()
        run.join(5)
        status = run.snapshot()
        self.assertEqual({name: status[name] for name in ("state", "done", "pending", "generated")},
                         {"state": "cancelled", "done": 2, "pending": 0, "generated": 2})


class WarmEndpointTests(AdminTestCase):
    def setUp(self) -> None:
        super().setUp()
        for item in (
            patch.object(main.pipeline.msearch_retriever, "live_collections_by_prefix", return_value={}),
            patch.object(main, "_warm_run", None),
            patch.object(main, "_load_questions_for_wp", lambda wp_id: (wp_id, ["Kdo byl Hus?", "Kdo byl Žižka?"])),
        ):
            item.start()
            self.addCleanup(item.stop)
        self.wp = self.client.get("/settings").json()["wps"][0]

    def warm(self, **body):
        response = self.client.post("/answer-cache/warm", json={"wp": [self.wp["id"]], **body}, headers=ADMIN)
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def finish(self):
        main._warm_run.join(10)
        return self.client.get("/answer-cache/warm", headers=ADMIN).json()

    def test_counts_then_warms_and_pins(self) -> None:
        self.assertEqual(self.client.get("/answer-cache/warm", headers=ADMIN).json(), {"state": "idle"})
        self.assertEqual(self.warm(dry_run=True), {"jobs": 2, "cached": 0})
        self.assertEqual(self.warm(dry_run=True, questions=["A?", " ", "B?"], profile=["builtin"]),
                         {"jobs": 2 * len(self.wp["builtin_prompts"]), "cached": 0})
        self.assertEqual(self.cache.count(), 0)

        self.warm(questions=["Kdo byl Jan Hus?", "Kdo byl Žižka?"], concurrency=2)
        status = self.finish()
        self.assertEqual({name: status[name] for name in ("state", "total", "generated", "cached", "failed")},
                         {"state": "finished", "total": 2, "generated": 2, "cached": 0, "failed": 0}, status)
        entries = self.client.get("/answer-cache", headers=ADMIN).json()["entries"]
        self.assertEqual(sorted(entry["question"] for entry in entries), ["Kdo byl Jan Hus?", "Kdo byl Žižka?"])
        self.assertTrue(all(entry["pinned"] for entry in entries))
        # The dry run finds the answers just stored under the keys a run would use.
        self.assertEqual(self.warm(dry_run=True, questions=["Kdo byl Jan Hus?", "Kdo byl Karel IV.?"]),
                         {"jobs": 2, "cached": 1})
        self.assertEqual({entry["prompt_preset_id"] for entry in entries}, {self.wp["default_prompt_id"]})

        self.warm(questions=["Kdo byl Jan Hus?"])
        self.assertEqual(self.finish()["cached"], 1)
        self.warm(questions=["Kdo byl Jan Hus?"], force=True)
        self.assertEqual(self.finish()["generated"], 1)
        self.assertEqual(len(self.generated), 3)

    def test_failures_are_listed(self) -> None:
        self.answer = []
        self.warm(questions=["Kdo byl Jan Hus?"])
        status = self.finish()
        self.assertEqual(status["failed"], 1)
        self.assertEqual(status["errors"][0]["error"], "prázdná odpověď")
        self.assertIn("Kdo byl Jan Hus?", status["errors"][0]["job"])

    def test_a_cut_answer_is_an_error(self) -> None:
        self.finish_reason = "length"
        self.warm(questions=["Kdo byl Jan Hus?"])
        status = self.finish()
        self.assertEqual((status["failed"], status["generated"]), (1, 0))
        self.assertEqual(status["errors"][0]["error"], "odpověď nebyla dokončena (důvod length)")
        self.assertEqual(self.cache.count(), 0)

    def test_status_polls_stay_out_of_the_access_log(self) -> None:
        quiet = main._QuietWarmPolls()

        def record(method, path, status):
            return logging.LogRecord("uvicorn.access", logging.INFO, "", 0, '%s - "%s %s HTTP/%s" %d',
                                     ("127.0.0.1:1", method, path, "1.1", status), None)

        self.assertFalse(quiet.filter(record("GET", "/answer-cache/warm", 200)))
        self.assertTrue(quiet.filter(record("GET", "/answer-cache/warm", 403)))
        self.assertTrue(quiet.filter(record("POST", "/answer-cache/warm", 200)))
        self.assertTrue(quiet.filter(record("GET", "/answer-cache", 200)))

    def test_one_run_at_a_time_and_cancel(self) -> None:
        release = threading.Event()
        original = self.generate

        def slow_generate(messages, **kwargs):
            release.wait(5)
            return original(messages, **kwargs)

        with patch.object(main.pipeline.llm, "stream_generate", side_effect=slow_generate):
            self.warm(questions=[f"Otázka {index}?" for index in range(5)], concurrency=1)
            response = self.client.post("/answer-cache/warm", json={"questions": ["x"]}, headers=ADMIN)
            self.assertEqual(response.status_code, 409)
            status = self.client.post("/answer-cache/warm/cancel", headers=ADMIN).json()
            self.assertTrue(status["cancelled"])
            release.set()
            status = self.finish()
        self.assertEqual((status["state"], status["done"], status["pending"]), ("cancelled", 1, 0))
        self.assertEqual(self.cache.count(), 1)

    def test_bad_requests(self) -> None:
        response = self.client.post("/answer-cache/warm", json={"wp": ["WP9"]}, headers=ADMIN)
        self.assertEqual(response.status_code, 400)
        self.assertIn("WP9", response.json()["detail"])
        response = self.client.post("/answer-cache/warm", json={"profile": ["missing"]}, headers=ADMIN)
        self.assertEqual(response.status_code, 400)
        response = self.client.post("/answer-cache/warm", json={"concurrency": 21}, headers=ADMIN)
        self.assertEqual(response.status_code, 422)
        for method, path in (("GET", "/answer-cache/warm"), ("POST", "/answer-cache/warm"), ("POST", "/answer-cache/warm/cancel")):
            with self.subTest(method=method, path=path):
                self.assertEqual(self.client.request(method, path, json={}).status_code, 403)


class WarmTimeoutTests(unittest.TestCase):
    def test_warming_waits_longer_for_the_model(self) -> None:
        client = OpenAICompatibleLLM("key", "model", "https://provider.example/v1", timeout=180)
        messages = [{"role": "user", "content": "q"}]
        with llm_timeout(600):
            self.assertEqual(client.stream_generate(messages).timeout, 600)
        self.assertEqual(client.stream_generate(messages).timeout, 180)

        seen = []

        def chat_events(request, http_request):
            def events():
                seen.append(client.stream_generate(messages).timeout)
                yield "event: done\ndata: {}\n"
            return events(), {}

        with patch.object(main, "_chat_events", chat_events), patch.object(main.settings, "cache_warm_llm_timeout_seconds", 600):
            list(main._warm_stream({"question": "q"}))
        self.assertEqual(seen, [600])
        self.assertEqual(client.stream_generate(messages).timeout, 180)


if __name__ == "__main__":
    unittest.main()
