"""The per-provider cap on requests in flight (`LLM_PROVIDER_<ID>_MAX_CONCURRENCY`).

A gateway with a parallel-request limit refuses the request over it with an
immediate 429. With the cap set, that request waits for a free slot instead.
"""

import threading
import time
import unittest
from unittest.mock import patch

import httpx

from app.analytics import error_code
from app.rag.llm import LLMBusyError, OpenAICompatibleLLM
from app.rag.llm_providers import provider_concurrency_limits

BASE_URL = "https://provider.example/v1"
OK_BODY = {"choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}], "model": "m"}


class _InFlight:
    """A fake upstream that counts requests open at once and holds each one."""

    def __init__(self, hold: float = 0.05) -> None:
        self.hold = hold
        self.lock = threading.Lock()
        self.now = 0
        self.peak = 0
        self.release = threading.Event()
        self.release.set()

    def __enter__(self):
        with self.lock:
            self.now += 1
            self.peak = max(self.peak, self.now)

    def __exit__(self, *exc):
        with self.lock:
            self.now -= 1

    def post(self, url, **kwargs):
        with self:
            time.sleep(self.hold)
            self.release.wait(5)
        return httpx.Response(200, request=httpx.Request("POST", url), json=OK_BODY)


def _run_parallel(fn, count: int) -> list:
    results: list = [None] * count

    def run(index: int) -> None:
        try:
            results[index] = fn()
        except Exception as exc:  # noqa: BLE001 - collected for the assertion
            results[index] = exc

    threads = [threading.Thread(target=run, args=(i,)) for i in range(count)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(10)
    return results


class GenerateCapTests(unittest.TestCase):
    def test_requests_over_the_cap_wait_instead_of_going_out(self) -> None:
        upstream = _InFlight()
        client = OpenAICompatibleLLM("key", "m", BASE_URL, concurrency_limits={BASE_URL: 2})
        with patch("app.rag.llm.httpx.post", side_effect=upstream.post):
            results = _run_parallel(lambda: client.generate([{"role": "user", "content": "q"}]), 6)
        self.assertEqual(upstream.peak, 2)
        self.assertTrue(all(getattr(r, "answer", None) == "ok" for r in results), results)

    def test_no_cap_when_the_provider_sets_none(self) -> None:
        upstream = _InFlight(hold=0.2)
        client = OpenAICompatibleLLM("key", "m", BASE_URL)
        with patch("app.rag.llm.httpx.post", side_effect=upstream.post):
            _run_parallel(lambda: client.generate([{"role": "user", "content": "q"}]), 4)
        self.assertEqual(upstream.peak, 4)

    def test_a_different_api_key_has_its_own_slots(self) -> None:
        # The gateway counts per key, so a user's own key is not held up by
        # requests made with the server key.
        upstream = _InFlight(hold=0.2)
        client = OpenAICompatibleLLM("server-key", "m", BASE_URL, concurrency_limits={BASE_URL: 1})
        calls = iter([None, "user-key"])
        lock = threading.Lock()

        def call():
            with lock:
                key = next(calls)
            return client.generate([{"role": "user", "content": "q"}], api_key=key)

        with patch("app.rag.llm.httpx.post", side_effect=upstream.post):
            _run_parallel(call, 2)
        self.assertEqual(upstream.peak, 2)

    def test_waiting_too_long_gives_a_plain_busy_error(self) -> None:
        upstream = _InFlight(hold=0)
        upstream.release.clear()
        client = OpenAICompatibleLLM("key", "m", BASE_URL, timeout=0.2, concurrency_limits={BASE_URL: 1})
        with patch("app.rag.llm.httpx.post", side_effect=upstream.post):
            holder = threading.Thread(target=lambda: client.generate([{"role": "user", "content": "q"}]))
            holder.start()
            time.sleep(0.05)
            with self.assertRaises(LLMBusyError) as caught:
                client.generate([{"role": "user", "content": "q"}])
            upstream.release.set()
            holder.join(5)
        self.assertIn("vytížený", str(caught.exception))
        self.assertEqual(error_code(caught.exception), "llm_busy")


class StreamCapTests(unittest.TestCase):
    def test_the_slot_is_held_until_the_stream_ends_and_freed_on_cancel(self) -> None:
        client = OpenAICompatibleLLM("key", "m", BASE_URL, timeout=0.2, concurrency_limits={BASE_URL: 1})
        body = b'data: {"choices":[{"delta":{"content":"a"}}]}\n\ndata: [DONE]\n\n'

        real_client = httpx.Client

        def make_client(*args, **kwargs):
            return real_client(transport=httpx.MockTransport(
                lambda request: httpx.Response(200, request=request, content=body)
            ))

        with patch("app.rag.llm.httpx.Client", side_effect=make_client):
            first = iter(client.stream_generate([{"role": "user", "content": "q"}]))
            next(first)  # mid-stream: the slot is taken
            with self.assertRaises(LLMBusyError):
                list(client.stream_generate([{"role": "user", "content": "q"}]))
            first.close()  # the client went away
            self.assertEqual(list(client.stream_generate([{"role": "user", "content": "q"}])), [("answer", "a")])


class ConfigTests(unittest.TestCase):
    def test_limits_are_read_per_base_url(self) -> None:
        env = {
            "LLM_PROVIDER_A_BASE_URL": "https://a.example/v1/",
            "LLM_PROVIDER_A_MAX_CONCURRENCY": "4",
            "LLM_PROVIDER_B_BASE_URL": "https://b.example/v1",
            "LLM_PROVIDER_C_BASE_URL": "https://c.example/v1",
            "LLM_PROVIDER_C_MAX_CONCURRENCY": "lots",
            "LLM_PROVIDER_D_BASE_URL": "https://d.example/v1",
            "LLM_PROVIDER_D_MAX_CONCURRENCY": "0",
        }
        self.assertEqual(provider_concurrency_limits(env), {"https://a.example/v1": 4})


if __name__ == "__main__":
    unittest.main()
