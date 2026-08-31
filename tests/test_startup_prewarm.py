import threading
import time
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app import main


def _wait_for(predicate, timeout: float = 5.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.01)
    return False


class StartupPrewarmTests(unittest.TestCase):
    def test_lifespan_warms_both_discoveries_off_the_request_path(self) -> None:
        # The two slow round-trips `/settings` needs — the provider catalogues
        # and the live mSearch collection list — are fetched at startup so the
        # browser's first request usually finds them cached.
        retriever = main.pipeline.msearch_retriever
        with (
            patch.object(main, "_refresh_provider_state") as refresh,
            patch.object(retriever, "live_collections_by_prefix") as collections,
        ):
            with TestClient(main.app):
                self.assertTrue(_wait_for(lambda: refresh.called and collections.called))

        refresh.assert_called_once_with()
        collections.assert_called_once_with()

    def test_a_prewarm_that_fails_does_not_break_startup(self) -> None:
        # Discovery is best-effort: an unreachable provider must leave the app
        # serving, with the request path free to retry.
        retriever = main.pipeline.msearch_retriever
        with (
            patch.object(main, "_refresh_provider_state", side_effect=RuntimeError("no network")),
            patch.object(retriever, "live_collections_by_prefix") as collections,
        ):
            with TestClient(main.app) as client:
                self.assertTrue(_wait_for(lambda: collections.called))
                self.assertEqual(client.get("/health").status_code, 200)

    def test_refreshes_never_overlap(self) -> None:
        # A refresh rebuilds several module globals in place, and the startup
        # prewarm runs alongside request threads, so two must never interleave.
        in_flight = 0
        peak = 0
        counter_lock = threading.Lock()

        def slow_refresh(force_model_refresh: bool) -> None:
            nonlocal in_flight, peak
            with counter_lock:
                in_flight += 1
                peak = max(peak, in_flight)
            time.sleep(0.05)
            with counter_lock:
                in_flight -= 1

        with patch.object(main, "_refresh_provider_state_locked", side_effect=slow_refresh):
            threads = [
                threading.Thread(target=main._refresh_provider_state) for _ in range(4)
            ]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()

        self.assertEqual(peak, 1)


if __name__ == "__main__":
    unittest.main()
