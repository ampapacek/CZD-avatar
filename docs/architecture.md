# Architecture and development

CZD-avatar uses FastAPI for orchestration, hosted mSearch for the supported retrieval workflow, and OpenAI-compatible chat completions for generation. The frontend combines static UI code with bundled ES modules.

The Python package and some internal identifiers use `rag-avatar`.

## API

Selected API endpoints (the complete schema is available at `/docs` when the app is running):

- `GET /health`
- `GET /settings`
- `GET /questions/random` (per-WP; reads the private files under `data/questions/`, see [Random Questions](prompts.md#random-questions))
- `GET /questions` (per-WP prepared-question list)
- `POST /llm-providers/refresh`
- `GET /prompt-presets`
- `POST /prompt-presets`
- `DELETE /prompt-presets/{preset_id}`
- `GET /placeholders`
- `POST /placeholders`
- `DELETE /placeholders/{name}`
- `POST /unlock`
- `POST /ingest`
- `POST /retrieve`
- `POST /chat`
- `POST /chat/stream`

Example `/chat` body. Parameter placeholders (e.g. `length`, `custom_instructions`) travel as a generic `selections` map; `placeholder_defs` carries the frontend's fully-resolved effective definitions for the placeholders the selected prompt uses (so the server substitutes exactly what the browser configured):

```json
{
  "question": "Jaký byl význam husitských válek?",
  "wp_id": "WP1-historie",
  "retrieval_backend": "msearch",
  "selections": {
    "length": "medium",
    "custom_instructions": "Focus mainly on causes and consequences."
  },
  "placeholder_defs": {
    "length": {
      "label": "Délka",
      "kind": "select",
      "default": "medium",
      "options": [
        {"name": "short", "label": "Krátká", "text": "Odpověz stručně."},
        {"name": "medium", "label": "Střední", "text": "Odpověz středně dlouze."},
        {"name": "long", "label": "Dlouhá", "text": "Odpověz podrobněji."}
      ]
    }
  }
}
```

`selections` and `placeholder_defs` may be omitted; the server then falls back to the shared `data/placeholders.json` overlay and the `DEFAULT_PLACEHOLDERS` code floor.

## Ask A Question

From the browser, try a Czech-history question such as:

- `Jaký byl význam husitských válek?`
- `Co znamenalo Pražské jaro?`

From the CLI:

```bash
uv run python scripts/ask.py "Jaký byl význam husitských válek?"
```

Optional controls. Parameter placeholders are set generically with `--selection name=value` (repeatable); `--length` is a shortcut for `--selection length=value`:

```bash
uv run python scripts/ask.py "Co znamenala bitva na Bílé hoře pro české země?" \
  --length long \
  --selection custom_instructions="Zaměř se na příčiny a důsledky."
```

## Frontend Development

The deployed app serves committed static JavaScript and does not need Node.js. When changing any module under `frontend/`, install the development dependencies and rebuild the browser bundle locally:

```bash
npm ci
npm test
npm run build
```

ES modules and focused tests live under `frontend/`; the entry point is `frontend/bundle.js` and the generated bundle is `app/static/avatar.bundle.js`. Rebuild and include the bundle with frontend source changes.

The app can be adapted to any topic, but this is not fully configuration-driven yet. When creating a new avatar/domain, check and update the default prompts, random-question file, frontend labels, collection asset paths in `app/main.py`, example questions, and any collection-specific helper scripts. Collections and prompts are already selectable within WPs. Making instance specialization fully configuration-driven remains future work.

## Tests

```bash
uv sync --group dev
uv run pytest
npm ci
npm test
```

The Python tests never read `.env`: `tests/conftest.py` gives them a fixed fake provider, so they behave the same on every machine and never see real API keys. GitHub Actions (`.github/workflows/tests.yml`) runs both suites on every push and pull request from a clean checkout, without torch and without any gitignored file, and fails when `app/static/avatar.bundle.js` was not rebuilt after a change under `frontend/`.

## Possible extensions

- Improve token counting with the selected model's tokenizer where available.
- Add richer metadata extraction for document collections.
- Add evaluation sets and automated citation-grounding checks.
- Move remaining domain-specific prompts, labels, and assets into instance configuration.

## Repository layout

- `app/main.py` — routes, model presets, public settings, lifespan shutdown
- `app/config.py`, `app/models.py`, `app/logging_config.py`
- `app/rag/` — ingestion, chunking, retrieval, prompting, vector store, pipeline
- `app/rag/wp_config.py` — single source of WP config (labels, built-in prompts, collections, defaults)
- `app/rag/placeholders.py` — placeholder engine + `DEFAULT_PLACEHOLDERS` floor
- `app/static/` — frontend (index.html, app.js, styles.css) + the built `avatar.bundle.js`
  `/` serves index.html with `Cache-Control: no-cache` and rewrites each `static/<file>?v=...`
  to that file's content hash, so never bump the `?v=` tokens by hand.
- `frontend/` — ES modules bundled into `app/static/avatar.bundle.js` (global `Avatar`) by
  `npm run build`, each with a `*.test.js` beside it. Entry point is `frontend/bundle.js`.
  **Rebuild the bundle after editing any of them** and include it with source changes; the deployed app
  serves the built file and needs no Node.
- `scripts/` — `ingest.py`, `ask.py`, `batch_answers.py`, `download_wikipedia.py`
- `deploy/` — pull-based auto-deploy: `deploy.sh` run every minute by a systemd timer on the server, deploying whatever the `production` branch points at (see [Deployment](deployment.md)). `tests/test_deploy_script.py` drives it against a throwaway origin.
- `data/raw/` source docs · `data/processed/chunks.jsonl` · `data/qdrant/` local store
- `data/models.json` — the one tracked file describing models: context window, reasoning support, room for more. `MODEL_METADATA_PATH` overrides it.
- `data/prompt_presets.json`, `data/placeholders.json` — shared overlays (gitignored, may be absent)
- `data/questions/*.txt` — private per-WP random/prepared questions (gitignored, may be absent)
- `data/collections/czech_history/` — Czech-history assets/metadata kept for the current WP1 setup

## Development conventions

- Test non-trivial changes and report what was and was not verified.
- When changing a user-visible feature (profiles, sharing, history, conversation, settings), update the Help dialog in `app/static/index.html` (`#helpDialog`).
- Rebuild `app/static/avatar.bundle.js` after editing modules under `frontend/` and include it with the source changes.
- Tests must not depend on `.env`, gitignored files, the network, or torch. Keep torch imports lazy in `app/rag/embeddings.py` and `app/rag/reranker.py`; CI installs dependencies from `uv.lock` without sentence-transformers.

## Sources, history, and conversation state

- Sources panel: retrieval order while streaming, then a flip to first-citation order when the answer finishes — but never for aborted/errored streams, retrieve-only mode, or an answer that cites nothing. The view state is a parameter of `renderSourceCards`, shared by the main, conversation and history panels: do not turn it back into a module global. The rest of the ordering, labelling and cited/uncited rules are pinned by `frontend/sources-panel.test.js`.
- History: local entries live in `localStorage` with no entry-count cap; a full storage never evicts silently — the list that did not fit waits in `storagePendingSaves` (memory only) and the Úložiště dialog (`frontend/storage-usage.js`, assumed 5 MiB budget, warn at 80%, auto-open at 95% or on a failed save) asks what to free: reasoning, shared copies, oldest items, or a manual pick. The dialog's filter bar (`frontend/history-filters.js`) starts on the active WP each time it opens. Shared items carry `visibility` `listed`/`link`; `link` items are left out of `GET /shared-history` (except for their owner) but open via `?shared=<id>`, which switches to the item's WP. That is an unlisted link, not access control. A shared entry has one note: editing it anywhere (local detail, Shared tab, main-page share panel) PATCHes the server item and mirrors it into the local entry; the server keeps only the current text plus `note_edited_at`, shown as "upraveno". Sharing an already-shared entry again is skipped, not duplicated.
- Conversation compaction is rolling and token-aware: crossing either the token or the message trigger folds the older tail, the server returns `conversation_folded_message_count`, and the browser advances `conversation_compacted_through`. The single rolling summary lives on the conversation, not on each message. Compaction and prompt packing are separate decisions — lack of prompt space alone must not trigger compaction. The triggers, caps and packing order are pinned by `tests/test_conversation_compaction.py` and `tests/test_token_budget.py`.
- An upstream error body must be read *inside* the `with client.stream(...)` block (`_raise_for_status_with_body`). Once the block exits the response is closed and the body is gone, so reading it later reported httpx's "without having called `read()`" for every 4xx/5xx — a real 429 looked identical to a bad model name. `tests/test_llm_errors.py` pins it, using a one-shot iterator body because a `content=`-backed mock stays rewindable after close and would pass either way.
- `stream_generate` yields `(kind, text)` chunks, `ANSWER` or `REASONING` (`app/rag/llm.py`). Reasoning models emit the whole trace before the first answer token, so the trace streams to the browser as its own `reasoning` SSE event and the panel stays open until the answer starts. TTFT is measured from the first **answer** token — starting it on a reasoning delta would report a model as faster the longer it thinks. `stream.reasoning_text` still accumulates the trace whole for the `done` event and history.
