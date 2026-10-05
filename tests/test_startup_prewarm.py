import asyncio
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


class DiscoveryLoopTests(unittest.TestCase):
    def _run_loop(self, interval: float, until) -> None:
        async def run() -> None:
            task = asyncio.create_task(main._discovery_loop(interval))
            deadline = time.monotonic() + 5.0
            while not until() and not task.done() and time.monotonic() < deadline:
                await asyncio.sleep(0.005)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        asyncio.run(run())

    def test_loop_forces_a_refresh_and_survives_failures(self) -> None:
        # After startup the loop keeps re-fetching on its own, forced, so a
        # request never finds the caches expired. A failing round is logged
        # and the next one still runs.
        retriever = main.pipeline.msearch_retriever
        with (
            patch.object(main, "_refresh_provider_state"),
            patch.object(
                main, "_refresh_provider_state_in_background", side_effect=[RuntimeError("down"), None, None]
            ) as background,
            patch.object(retriever, "live_collections_by_prefix") as collections,
        ):
            self._run_loop(0.01, lambda: background.call_count >= 2)

        self.assertGreaterEqual(background.call_count, 2)
        collections.assert_any_call()
        collections.assert_any_call(force_refresh=True)

    def test_zero_interval_only_runs_startup_discovery(self) -> None:
        retriever = main.pipeline.msearch_retriever
        with (
            patch.object(main, "_refresh_provider_state") as refresh,
            patch.object(main, "_refresh_provider_state_in_background") as background,
            patch.object(retriever, "live_collections_by_prefix"),
        ):
            self._run_loop(0, lambda: False)

        refresh.assert_called_once_with()
        background.assert_not_called()

    def test_background_fetch_does_not_hold_the_settings_lock(self) -> None:
        # `/settings` takes the provider lock on every call; the slow forced
        # fetch must run outside it or every page load would wait for it.
        held_during_fetch = []

        def fake_load(*args, force_model_refresh: bool = False, **kwargs):
            if force_model_refresh:
                held_during_fetch.append(main._provider_state_lock.locked())
            return []

        with (
            patch.object(main, "load_provider_configs", side_effect=fake_load),
            patch.object(main, "_refresh_provider_state") as refresh,
        ):
            main._refresh_provider_state_in_background()

        self.assertEqual(held_during_fetch, [False])
        refresh.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
