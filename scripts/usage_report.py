#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any, Iterable


def load_events(paths: Iterable[Path]) -> tuple[list[dict[str, Any]], int]:
    events: list[dict[str, Any]] = []
    skipped = 0
    for path in paths:
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            print(f"warning: cannot read {path}: {exc}", file=sys.stderr)
            skipped += 1
            continue
        for line in lines:
            try:
                event = json.loads(line)
            except (ValueError, TypeError):
                skipped += 1
                continue
            if not isinstance(event, dict) or event.get("schema_version") != 1 or not event.get("event"):
                skipped += 1
                continue
            events.append(event)
    return events, skipped


def percentile(values: Iterable[float], percentile_value: float) -> float | None:
    ordered = sorted(float(value) for value in values if isinstance(value, (int, float)))
    if not ordered:
        return None
    rank = max(0, math.ceil(percentile_value * len(ordered)) - 1)
    return ordered[rank]


def filter_events(events: list[dict[str, Any]], args: argparse.Namespace) -> list[dict[str, Any]]:
    filters = {
        "event": args.event,
        "wp_id": args.wp,
        "operation": args.operation,
        "provider": args.provider,
        "requested_model": args.model,
        "endpoint_host": args.endpoint,
        "msearch_collection": args.collection,
        "prompt_id": args.prompt,
        "key_source": args.key_source,
        "status": args.status,
        "error_code": args.error_code,
        "client_id": args.client_id,
    }
    result = []
    for event in events:
        day = str(event.get("ts") or "")[:10]
        if args.from_date and day < args.from_date:
            continue
        if args.to_date and day > args.to_date:
            continue
        if any(value is not None and event.get(key) != value for key, value in filters.items()):
            continue
        result.append(event)
    return result


def count_rows(events: list[dict[str, Any]], fields: tuple[str, ...], section: str) -> list[dict[str, Any]]:
    counts = Counter(tuple(event.get(field) for field in fields) for event in events)
    return [
        {"section": section, **dict(zip(fields, key, strict=True)), "count": count}
        for key, count in sorted(counts.items(), key=lambda item: tuple(str(value) for value in item[0]))
    ]


def build_report(events: list[dict[str, Any]], skipped: int) -> dict[str, Any]:
    opens = [event for event in events if event.get("event") == "app_open"]
    turns = [event for event in events if event.get("event") == "turn"]
    calls = [event for event in events if event.get("event") == "upstream_call"]
    rows: list[dict[str, Any]] = []
    rows += count_rows(
        [{**event, "day": str(event.get("ts") or "")[:10]} for event in turns],
        ("day", "wp_id"),
        "usage_by_day_wp",
    )
    rows.append({
        "section": "opens_identity",
        "page_opens": len(opens),
        "distinct_browsers": len({event["client_id"] for event in events if event.get("client_id")}),
        "tab_sessions": len({event["session_id"] for event in events if event.get("session_id")}),
    })
    rows += count_rows(turns, ("operation",), "operation")
    rows += count_rows(turns, ("is_prepared_question", "is_default_question"), "question_kind")
    for field in ("provider", "requested_model", "upstream_model", "endpoint_host", "msearch_collection", "prompt_id", "key_source"):
        rows += count_rows(turns, (field,), field)
    rows += count_rows(calls, ("purpose", "key_source"), "upstream_calls")
    rows += count_rows(turns, ("status", "error_code"), "outcomes")

    timing_fields = (
        "total_ms", "query_transform_ms", "retrieval_ms", "rerank_ms", "prompt_prepare_ms",
        "time_to_first_token_ms", "token_stream_ms", "generation_ms",
    )
    timing_groups: dict[tuple[Any, Any, Any], list[dict[str, Any]]] = defaultdict(list)
    for event in turns:
        timing_groups[(event.get("wp_id"), event.get("provider"), event.get("requested_model"))].append(event)
    for key, group in sorted(timing_groups.items(), key=lambda item: tuple(str(value) for value in item[0])):
        for field in timing_fields:
            values = [event[field] for event in group if isinstance(event.get(field), (int, float))]
            if values:
                rows.append({
                    "section": "timings",
                    "wp_id": key[0], "provider": key[1], "requested_model": key[2], "metric": field,
                    "count": len(values), "p50": percentile(values, .50), "p95": percentile(values, .95),
                })
    for field in ("question_chars", "question_words", "answer_chars", "answer_words", "answer_tokens_estimated"):
        values = [event[field] for event in turns if isinstance(event.get(field), (int, float))]
        if values:
            rows.append({"section": "lengths", "metric": field, "count": len(values), "p50": percentile(values, .50), "p95": percentile(values, .95)})
    return {"event_count": len(events), "skipped_lines": skipped, "rows": rows}


def print_table(report: dict[str, Any]) -> None:
    print(f"events: {report['event_count']}  skipped malformed/unknown: {report['skipped_lines']}")
    current = None
    for row in report["rows"]:
        section = row.get("section")
        if section != current:
            current = section
            print(f"\n[{section}]")
        print("  " + "  ".join(f"{key}={value}" for key, value in row.items() if key != "section"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Aggregate rag-avatar monthly usage JSONL files.")
    parser.add_argument("paths", nargs="*", type=Path, help="JSONL files (default: logs/events/usage-*.jsonl)")
    parser.add_argument("--from", dest="from_date", type=_date_arg)
    parser.add_argument("--to", dest="to_date", type=_date_arg)
    for option, dest in (("--event", "event"), ("--wp", "wp"), ("--operation", "operation"), ("--provider", "provider"), ("--model", "model"), ("--endpoint", "endpoint"), ("--collection", "collection"), ("--prompt", "prompt"), ("--key-source", "key_source"), ("--status", "status"), ("--error-code", "error_code"), ("--client-id", "client_id")):
        parser.add_argument(option, dest=dest)
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--json", action="store_true")
    output.add_argument("--csv", action="store_true")
    args = parser.parse_args(argv)
    paths = args.paths or sorted(Path("logs/events").glob("usage-*.jsonl"))
    events, skipped = load_events(paths)
    report = build_report(filter_events(events, args), skipped)
    if args.json:
        json.dump(report, sys.stdout, ensure_ascii=False, indent=2)
        print()
    elif args.csv:
        keys = sorted({key for row in report["rows"] for key in row})
        writer = csv.DictWriter(sys.stdout, fieldnames=keys)
        writer.writeheader()
        writer.writerows(report["rows"])
    else:
        print_table(report)
    if skipped:
        print(f"warning: skipped {skipped} malformed or unknown-schema line(s)", file=sys.stderr)
    return 0


def _date_arg(value: str) -> str:
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("expected YYYY-MM-DD") from exc
    return value


if __name__ == "__main__":
    raise SystemExit(main())
