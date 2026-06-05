from __future__ import annotations

from typing import Any

import httpx

from app.config import Settings


FALLBACK_COLLECTION_PRESETS = [
    {
        "label": "WP1: histoedu v2026-02",
        "collection_id": "64d6f521-5044-4b02-8658-380b639801af",
        "collection_name": "wp1-histoedu-v2026-02",
        "last_modified": "2026-02-23T14:23:48.294717",
    },
    {
        "label": "WP2: zaplavy v2026-6",
        "collection_id": "ab79b4f6-6a91-45a3-908e-edb2c771d3b0",
        "collection_name": "wp2-zaplavy-v2026-6",
        "last_modified": "2026-06-04T17:51:35.359767",
    },
    {
        "label": "WP3: law v2026-02",
        "collection_id": "d4be44d5-689c-4bbe-a372-b959929cd511",
        "collection_name": "wp3-law-v2026-02",
        "last_modified": "2026-03-06T16:05:12.481649",
    },
    {
        "label": "WP4: v2026-03",
        "collection_id": "3429956e-8a21-4502-ad21-a41fddc5ef99",
        "collection_name": "wp4-v2026-03",
        "last_modified": "2026-03-19T08:32:09.851531",
    },
]

WP2_COLLECTION_ID = "ab79b4f6-6a91-45a3-908e-edb2c771d3b0"


class MSearchRetriever:
    """Fetch mSearch documents and normalize passages to avatar chunk records."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def collection_presets(self) -> list[dict[str, str]]:
        if not self.settings.msearch_username or not self.settings.msearch_password:
            return FALLBACK_COLLECTION_PRESETS
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
            return FALLBACK_COLLECTION_PRESETS

        collections = data.get("collections") if isinstance(data, dict) else None
        if not isinstance(collections, list):
            return FALLBACK_COLLECTION_PRESETS
        presets = _newest_wp_presets(collections)
        return presets or FALLBACK_COLLECTION_PRESETS

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


def _newest_wp_presets(collections: list[Any]) -> list[dict[str, str]]:
    newest: dict[str, dict[str, str]] = {}
    for item in collections:
        if not isinstance(item, dict):
            continue
        name = _string(item.get("collection_name"))
        collection_id = _string(item.get("collection_id"))
        last_modified = _string(item.get("last_modified"))
        prefix = name.split("-", 1)[0].lower()
        if prefix not in {"wp1", "wp2", "wp3", "wp4"} or not collection_id:
            continue
        existing = newest.get(prefix)
        if existing is None or last_modified > existing.get("last_modified", ""):
            newest[prefix] = {
                "label": _preset_label(prefix, name),
                "collection_id": collection_id,
                "collection_name": name,
                "last_modified": last_modified,
            }
    return [newest[prefix] for prefix in ("wp1", "wp2", "wp3", "wp4") if prefix in newest]


def _preset_label(prefix: str, name: str) -> str:
    label_prefix = prefix.upper()
    tail = name.split("-", 1)[1] if "-" in name else name
    if prefix == "wp1":
        tail = tail.removeprefix("histoedu-")
        return f"{label_prefix}: histoedu {tail}"
    if prefix == "wp2":
        tail = tail.removeprefix("zaplavy-")
        return f"{label_prefix}: zaplavy {tail}"
    if prefix == "wp3":
        tail = tail.removeprefix("law-")
        return f"{label_prefix}: law {tail}"
    return f"{label_prefix}: {tail}"


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
