from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import httpx

from app.config import Settings
from app.rag.wp_config import gated_wp_collection_prefixes


# mSearch publishes new collection versions rarely, so the full collection list
# is cached and only re-fetched once an hour. This mirrors the LLM model
# discovery cache (``llm_providers._discover_models_cached``): each page load
# reads the settings payload, which reuses the cached list unless it is stale.
_COLLECTIONS_CACHE_TTL_SECONDS = 3600.0


@dataclass
class _CollectionsCacheEntry:
    collections: list[dict[str, Any]]
    fetched_at: float


_collections_cache: dict[str, _CollectionsCacheEntry] = {}


def clear_collections_cache() -> None:
    _collections_cache.clear()


class MSearchRetriever:
    """Fetch mSearch documents and normalize passages to avatar chunk records."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _fetch_collections(self, force_refresh: bool = False) -> list[dict[str, Any]]:
        """All mSearch collections (raw dicts), cached with a 1h TTL.

        Returns the last good list on transient failure, or an empty list when no
        credentials are configured / nothing has ever been fetched.
        """

        if not self.settings.msearch_username or not self.settings.msearch_password:
            return []

        cache_key = self.base_url
        cached = _collections_cache.get(cache_key)
        now = time.time()
        if cached and not force_refresh and now - cached.fetched_at < _COLLECTIONS_CACHE_TTL_SECONDS:
            return cached.collections

        try:
            with httpx.Client(timeout=min(self.settings.msearch_timeout, 10.0)) as client:
                response = client.get(
                    f"{self.base_url}/msearch/collections",
                    params={"include_public": "false", "reload": "false"},
                    auth=(self.settings.msearch_username, self.settings.msearch_password),
                )
                response.raise_for_status()
                data = response.json()
        except Exception:
            return cached.collections if cached else []

        collections = data.get("collections") if isinstance(data, dict) else None
        if not isinstance(collections, list):
            return cached.collections if cached else []
        collections = [item for item in collections if isinstance(item, dict)]
        _collections_cache[cache_key] = _CollectionsCacheEntry(collections=collections, fetched_at=now)
        return collections

    def live_collections_by_prefix(self, force_refresh: bool = False) -> dict[str, list[dict[str, str]]]:
        """Live mSearch collections grouped by WP prefix (``wp1``..``wp4``).

        Each WP's list is newest-first. Empty dict when the live list is
        unavailable, so callers fall back to the static WP config collections.
        """

        return _group_collections_by_prefix(self._fetch_collections(force_refresh))

    def gated_collection_ids(self) -> set[str]:
        """Live mSearch collection ids whose WP is AI-Ufal-only (for policy)."""

        gated_prefixes = gated_wp_collection_prefixes()
        grouped = self.live_collections_by_prefix()
        return {
            collection["collection_id"]
            for prefix in gated_prefixes
            for collection in grouped.get(prefix, [])
        }

    def retrieve(
        self,
        question: str,
        top_k: int,
        collection_id: str | None = None,
        mode: str | None = None,
        min_confidence: float | None = None,
        min_score: float | None = None,
        min_relative_score: float | None = None,
    ) -> list[dict[str, Any]]:
        if top_k <= 0:
            return []
        if not self.settings.msearch_username or not self.settings.msearch_password:
            raise RuntimeError("MSEARCH_USERNAME and MSEARCH_PASSWORD must be configured for mSearch retrieval.")

        payload: dict[str, Any] = {
            "collections": [collection_id or self.settings.msearch_collection],
            "query": question,
            "max_results": top_k,
            "mode": mode or self.settings.msearch_mode,
            "include_content": ["full"],
            "result_format": "flat",
            "highlight": True,
        }
        resolved_min_confidence = (
            self.settings.msearch_min_confidence if min_confidence is None else min_confidence
        )
        if resolved_min_confidence is not None:
            payload["min_confidence"] = resolved_min_confidence

        with httpx.Client(timeout=self.settings.msearch_timeout) as client:
            response = client.post(
                f"{self.base_url}/msearch/collections/search",
                auth=(self.settings.msearch_username, self.settings.msearch_password),
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        records = _records_from_response(data, max(top_k * 3, top_k))
        return _filter_by_thresholds(records, min_score, min_relative_score)[:top_k]

    @property
    def base_url(self) -> str:
        return self.settings.msearch_base_url.rstrip("/")


def _records_from_response(data: dict[str, Any], limit: int) -> list[dict[str, Any]]:
    documents = data.get("documents") if isinstance(data, dict) else None
    if not isinstance(documents, list):
        return []

    records: list[dict[str, Any]] = []
    for index, item in enumerate(documents[:limit], start=1):
        if not isinstance(item, dict):
            continue
        document = item.get("document") if isinstance(item.get("document"), dict) else {}
        raw_id = _string(document.get("id")) or _string(item.get("document_id")) or f"msearch-{index}"
        display_id = _trim_doc_id(raw_id)
        score = _float(item.get("score"))
        text = _document_text(item, document)
        if not text:
            continue

        url = _string(document.get("url")).replace("https://storage.ufal.mff.cuni.cz//", "https://storage.ufal.mff.cuni.cz/")
        title = _string(document.get("title")) or _string(document.get("Název")) or display_id or "mSearch dokument"
        page_number = _page_number(document.get("page_number"))

        records.append(
            {
                "citation_id": f"Z{len(records) + 1}",
                "chunk_id": f"msearch:{raw_id}",
                "text": text,
                "metadata": {
                    "source_kind": "msearch",
                    "title": title,
                    "source_path": display_id,
                    "source_path_display": display_id,
                    "page_number": page_number,
                    "url": url,
                    "document_url": url,
                    "source_url": url,
                    "source_name": "mSearch",
                },
                "score": score,
                "dense_score": score if item.get("source") == "sem" else None,
                "bm25_score": score if item.get("source") == "key" else None,
            }
        )
    return records


def _document_text(item: dict[str, Any], document: dict[str, Any]) -> str:
    # `document.content` is the full chunk text (requested via include_content=full).
    # Prefer it over `passages`: with highlight=true, BM25 (source="key") hits return
    # `passages` whose entries are single matched query tokens, not real passage text.
    # Highlighting cited terms within this text is a frontend concern.
    content = _string(document.get("content"))
    if content:
        return content

    passages = item.get("passages")
    if isinstance(passages, list):
        # Skip single-token highlight fragments; keep only real multi-word snippets.
        texts = [
            text
            for passage in passages
            if isinstance(passage, dict)
            and (text := _string(passage.get("text")))
            and len(text.split()) > 1
        ]
        text = "\n\n".join(texts)
        if text:
            return text

    sections = item.get("sections")
    if isinstance(sections, list):
        texts = []
        for section in sections:
            if isinstance(section, dict):
                text = _string(section.get("content")) or _string(section.get("value"))
                if text:
                    texts.append(text)
        return "\n\n".join(texts)

    return ""


def _group_collections_by_prefix(collections: list[dict[str, Any]]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = {}
    for item in collections:
        name = _string(item.get("collection_name"))
        collection_id = _string(item.get("collection_id"))
        prefix = name.split("-", 1)[0].lower()
        if prefix not in {"wp1", "wp2", "wp3", "wp4"} or not collection_id:
            continue
        grouped.setdefault(prefix, []).append(
            {
                "collection_id": collection_id,
                "collection_name": name,
                "last_modified": _string(item.get("last_modified")),
            }
        )
    for entries in grouped.values():
        # Newest first so the default selection lands on the latest version.
        entries.sort(key=lambda entry: entry["last_modified"], reverse=True)
    return grouped


def _trim_doc_id(doc_id: str) -> str:
    value = doc_id
    if ":/" in value:
        value = value.split(":/", 1)[1]
    marker = "zdroje-z-tabulky/"
    if marker in value:
        value = value.split(marker, 1)[1]
    return value.lstrip("/")


def _string(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _float(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return 0.0
    return 0.0


def _page_number(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return None


def _filter_by_thresholds(
    records: list[dict[str, Any]],
    min_score: float | None,
    min_relative_score: float | None,
) -> list[dict[str, Any]]:
    if not records:
        return []
    ranked = sorted(records, key=lambda item: float(item.get("score") or 0.0), reverse=True)
    best_score = float(ranked[0].get("score") or 0.0)
    filtered = ranked
    if min_score is not None:
        filtered = [record for record in filtered if float(record.get("score") or 0.0) >= min_score]
    if min_relative_score is not None and best_score > 0:
        threshold = best_score * min_relative_score
        filtered = [record for record in filtered if float(record.get("score") or 0.0) >= threshold]
    for index, record in enumerate(filtered, start=1):
        record["citation_id"] = f"Z{index}"
    return filtered
