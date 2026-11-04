"""Warming the answer cache: building the requests and running them.

Shared by scripts/warm_cache.py, which runs the requests against the app over
HTTP, and the admin Cache dialog, which runs them inside the app. Both build
the same request bodies, so both fill the entries visitors hit.

Requests are built the way the browser builds them with its default settings:
the WP's default collection, the model's context window, and the profile's
prompts. A visitor who changed a setting (or uses a profile saved only in their
browser) asks a different request and is not served the warmed answer.
"""

from __future__ import annotations

import json
import logging
import threading
import time
from collections.abc import Callable, Generator, Iterable, Iterator
from contextlib import closing
from dataclasses import dataclass
from typing import Any

from app.answer_cache import AnswerCache

logger = logging.getLogger(__name__)

MAX_CONCURRENCY = 20
# Failures a run keeps for display; the count covers all of them.
MAX_RUN_ERRORS = 50

GENERATED = "vygenerováno"
CACHED = "v mezipaměti"

Fetch = Callable[[str, dict[str, str]], Any]
Stream = Callable[[dict[str, Any]], Generator[str, None, None]]


@dataclass
class Job:
    wp_id: str
    profile_id: str
    model: str
    question: str
    body: dict[str, Any]

    def label(self) -> str:
        return f"{self.wp_id} · {self.profile_id} · {self.model or 'výchozí model'} · {self.question}"


def builtin_profiles(wp: dict[str, Any]) -> list[dict[str, Any]]:
    return [{**preset, "wp_id": wp["id"]} for preset in wp.get("builtin_prompts") or []]


def default_profile_id(wp: dict[str, Any]) -> str:
    builtins = builtin_profiles(wp)
    return wp.get("default_prompt_id") or (builtins[0]["id"] if builtins else "")


def select_profiles(wp: dict[str, Any], shared: list[dict[str, Any]], wanted: Iterable[str]) -> list[dict[str, Any]]:
    """The WP's profiles named by ``wanted``: default, builtin, shared, all or ids."""

    builtins = builtin_profiles(wp)
    shared = [preset for preset in shared if preset.get("wp_id") == wp["id"]]
    by_id = {preset["id"]: preset for preset in builtins + shared}
    selected: dict[str, dict[str, Any]] = {}
    for name in wanted:
        if name == "default":
            ids = [default_profile_id(wp)]
        elif name == "builtin":
            ids = [preset["id"] for preset in builtins]
        elif name == "shared":
            ids = [preset["id"] for preset in shared]
        elif name == "all":
            ids = list(by_id)
        else:
            ids = [name]
        for profile_id in ids:
            if profile_id in by_id:
                selected.setdefault(profile_id, by_id[profile_id])
    return list(selected.values())


def provider_config(app_settings: dict[str, Any], provider_id: str | None) -> dict[str, Any]:
    providers = app_settings.get("llm_providers") or []
    wanted = provider_id or app_settings.get("llm_provider")
    for provider in providers:
        if provider.get("id") == wanted:
            return provider
    raise ValueError(f"Neznámý poskytovatel {wanted!r}; dostupní: {', '.join(p.get('id', '') for p in providers)}")


def wp_default_collection(wp: dict[str, Any]) -> str:
    """As wpDefaultCollectionMsearchId in app.js."""

    collections = wp.get("collections") or []
    preferred = next((c for c in collections if c.get("id") == wp.get("default_collection_id")), None)
    chosen = preferred or (collections[0] if collections else None)
    return (chosen or {}).get("msearch_collection_id") or ""


def model_context_window(app_settings: dict[str, Any], provider: dict[str, Any], model: str) -> int:
    """As selectedModelContextWindow in app.js, falling back to the server default."""

    windows = {**(app_settings.get("model_context_windows") or {}), **(provider.get("model_context_windows") or {})}
    for value in (windows.get(model), provider.get("default_context_window_tokens")):
        if isinstance(value, (int, float)) and value >= 1024:
            return int(value)
    return int(app_settings["token_budget_defaults"]["context_window_tokens"])


def request_body(
    app_settings: dict[str, Any],
    wp: dict[str, Any],
    profile: dict[str, Any],
    provider: dict[str, Any],
    model: str,
    question: str,
    admin_password: str | None,
) -> dict[str, Any]:
    """The first-turn body the browser sends with its default settings.

    Fields the browser fills from server defaults are left out: the server
    resolves them to the same values for the cache key.
    """

    model = model or provider.get("default_model") or ""
    retrieval = app_settings["retrieval_defaults"]
    msearch = app_settings["msearch_defaults"]
    return {
        "question": question,
        "wp_id": wp["id"],
        "prompt_preset_id": profile["id"],
        "placeholder_defs": profile.get("placeholders") or {},
        "system_prompt": profile.get("system_prompt") or None,
        "user_prompt_template": profile.get("user_prompt_template") or None,
        "conversation_history": [],
        "context_window_tokens": model_context_window(app_settings, provider, model),
        "model": model,
        "llm_provider": provider["id"],
        # Models that are not public need the shared password, as in the browser.
        "admin_password": admin_password or None,
        "top_k": msearch.get("max_results") if msearch.get("max_results") is not None else app_settings.get("top_k"),
        "retrieval_backend": "msearch",
        "msearch_collection": wp_default_collection(wp),
        "msearch_mode": "hybrid",
        "msearch_rescore": bool(retrieval.get("msearch_rescore")),
        "rerank_enabled": False,
    }


def interleave_by_model(jobs: list[Job]) -> list[Job]:
    """Round-robin over the models (A1, B1, A2, B2, …), keeping each model's
    order, so parallel requests go to different models where possible."""

    by_model: dict[str, list[Job]] = {}
    for job in jobs:
        by_model.setdefault(job.model, []).append(job)
    queues = list(by_model.values())
    return [queue[index] for index in range(max(map(len, queues), default=0)) for queue in queues if index < len(queue)]


def build_jobs(fetch: Fetch, options: dict[str, Any], admin_password: str | None) -> list[Job]:
    """Every request the options ask for, interleaved by model.

    ``options`` holds ``wp`` (ids or "all"), ``questions`` ("prepared" or a
    list of questions), ``profile`` (see select_profiles), ``provider`` and
    ``model`` (none means the provider's default model). ``fetch`` reads the
    app's /settings, /prompt-presets and /questions. Raises ValueError for an
    unknown WP or provider.
    """

    app_settings = fetch("/settings", {})
    shared = fetch("/prompt-presets", {})
    wps = app_settings["wps"]
    wanted_wps = options["wp"]
    if "all" not in wanted_wps:
        known = {wp["id"] for wp in wps}
        unknown = [wp_id for wp_id in wanted_wps if wp_id not in known]
        if unknown:
            raise ValueError(f"Neznámé WP: {', '.join(unknown)}; dostupné: {', '.join(sorted(known))}")
        wps = [wp for wp in wps if wp["id"] in wanted_wps]
    provider = provider_config(app_settings, options["provider"])
    models = options["model"] or [provider.get("default_model") or ""]
    jobs: list[Job] = []
    for wp in wps:
        profiles = select_profiles(wp, shared, options["profile"])
        if not profiles:
            logger.warning("%s: žádný vybraný profil", wp["id"])
            continue
        if options["questions"] == "prepared":
            questions = list(fetch("/questions", {"wp_id": wp["id"]})["questions"])
        else:
            questions = [question.strip() for question in options["questions"] if question.strip()]
        for profile in profiles:
            for model in models:
                for question in questions:
                    body = request_body(app_settings, wp, profile, provider, model, question, admin_password)
                    jobs.append(Job(wp["id"], profile["id"], body["model"], question, body))
    return interleave_by_model(jobs)


def sse_events(lines: Iterable[str]) -> Iterator[tuple[str, dict[str, Any]]]:
    name, data = "", []
    for line in lines:
        if line.startswith("event: "):
            name = line.removeprefix("event: ")
        elif line.startswith("data: "):
            data.append(line.removeprefix("data: "))
        elif not line and name:
            yield name, json.loads("\n".join(data) or "{}")
            name, data = "", []
    if name:
        yield name, json.loads("\n".join(data) or "{}")


def warm(stream: Stream, cache: AnswerCache, job: Job, force: bool) -> str:
    """Generate (or find) one answer and pin it; returns the status to print:
    GENERATED, CACHED or "chyba: …"."""

    body = {**job.body, "bypass_cache": True} if force else job.body
    with closing(stream(body)) as lines:
        events = sse_events(lines)
        for name, data in events:
            if name == "error":
                # Read to the end, so the stream records its error rather than
                # a disconnect (as after "done").
                _drain(events)
                return f"chyba: {data.get('detail')}"
            if name == "sources" and data.get("cache_hit"):
                # Already cached: disconnect rather than sit through the replay.
                return CACHED if _pin(cache, data.get("cache_key")) else _not_pinned()
            if name == "done":
                _drain(events)
                if not str(data.get("answer") or "").strip():
                    return "chyba: prázdná odpověď"
                return GENERATED if _pin(cache, data.get("cache_key")) else _not_pinned()
    return "chyba: odpověď skončila předčasně"


def _drain(events: Iterator[Any]) -> None:
    for _ in events:
        pass


def _pin(cache: AnswerCache, key: str | None) -> bool:
    return bool(key) and cache.pin(key)


def _not_pinned() -> str:
    return "chyba: záznam v mezipaměti nenalezen (je mezipaměť zapnutá a ANSWER_CACHE_PATH stejná jako v aplikaci?)"


class WarmRun:
    """Jobs run by ``concurrency`` worker threads in queue order.

    Cancelling drops the jobs not started yet; the running ones finish.
    ``run_job`` returns a status as warm() does and must not raise.
    """

    def __init__(self, jobs: list[Job], run_job: Callable[[Job], str], concurrency: int) -> None:
        self.jobs = jobs
        self.run_job = run_job
        self.concurrency = max(1, min(concurrency, MAX_CONCURRENCY))
        self.started_at = time.time()
        self.finished_at: float | None = None
        self.cancelled = False
        self.generated = self.cached = self.failed = 0
        self.errors: list[dict[str, str]] = []
        self._next = 0
        self._running = 0
        self._lock = threading.Lock()
        self._threads: list[threading.Thread] = []

    def start(self, wrap: Callable[[Callable[[], None]], Callable[[], None]] = lambda work: work) -> None:
        """Start the workers; ``wrap`` adapts each worker's function, e.g. to
        run it in a copy of the caller's context."""

        workers = min(self.concurrency, len(self.jobs))
        with self._lock:
            self._running = workers
            if not workers:
                self.finished_at = time.time()
        for _ in range(workers):
            thread = threading.Thread(target=wrap(self._work), name="cache-warm", daemon=True)
            self._threads.append(thread)
            thread.start()

    def _take(self) -> Job | None:
        with self._lock:
            if self.cancelled or self._next >= len(self.jobs):
                return None
            self._next += 1
            return self.jobs[self._next - 1]

    def _work(self) -> None:
        try:
            while (job := self._take()) is not None:
                try:
                    status = self.run_job(job)
                except Exception as exc:  # A worker must survive any job.
                    logger.exception("Warming %s failed", job.label())
                    status = f"chyba: {exc}"
                self._record(job, status)
        finally:
            with self._lock:
                self._running -= 1
                if not self._running:
                    self.finished_at = time.time()

    def _record(self, job: Job, status: str) -> None:
        with self._lock:
            if status == GENERATED:
                self.generated += 1
            elif status == CACHED:
                self.cached += 1
            else:
                self.failed += 1
                if len(self.errors) < MAX_RUN_ERRORS:
                    self.errors.append({"job": job.label(), "error": status.removeprefix("chyba: ")})

    def cancel(self) -> None:
        with self._lock:
            self.cancelled = True

    @property
    def finished(self) -> bool:
        return self.finished_at is not None

    def join(self, timeout: float | None = None) -> None:
        for thread in self._threads:
            thread.join(timeout)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            done = self.generated + self.cached + self.failed
            return {
                "state": "running" if self.finished_at is None else "cancelled" if self.cancelled else "finished",
                "cancelled": self.cancelled,
                "total": len(self.jobs),
                "done": done,
                "running": self._next - done,
                "pending": 0 if self.cancelled else len(self.jobs) - self._next,
                "generated": self.generated,
                "cached": self.cached,
                "failed": self.failed,
                "errors": list(self.errors),
                "concurrency": self.concurrency,
                "started_at": self.started_at,
                "finished_at": self.finished_at,
            }
