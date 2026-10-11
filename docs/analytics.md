# Usage analytics and logging

Structured usage events and prose/debug logs are separate outputs with different contents.

## Usage Analytics

Usage analytics are enabled by default and written as append-only monthly JSONL
files under `logs/events/` (which is gitignored). They record app opens, completed
or failed turns, actual upstream LLM calls, configuration choices, timings, and
text lengths. They do not record question text, answer text, prompt text, source
text, IP addresses, User-Agent strings, or API keys. Questions are represented
by an unsalted SHA-256 hash plus prepared/default-question classification.

Configure the writer in `.env`:

```env
ANALYTICS_ENABLED=true
ANALYTICS_DIR=logs/events
ANALYTICS_INSTANCE_ID=czd-avatar
```

Retention is indefinite and manual. To inspect all available monthly files:

```bash
uv run python scripts/usage_report.py
uv run python scripts/usage_report.py --from 2026-08-01 --wp WP1-historie
uv run python scripts/usage_report.py --json
uv run python scripts/usage_report.py --csv > usage.csv
```

The report skips malformed or unknown-schema lines and prints how many it
skipped. It supports filters for event, WP, operation, provider, model, endpoint,
collection, prompt, key source, status, error code, date range, and browser ID.

## Logs

Each server or script start creates a new timestamped log file in:

```text
logs/
```

Examples:

```text
logs/api-20260424-104255.log
logs/ingest-20260424-104501.log
logs/ask-20260424-104712.log
logs/download-wikipedia-20260424-104900.log
```

Console output stays shorter, while the file logs persist questions, retrieval metadata, selected model, response timing, and generated answers.
