# Agent Notes

Practical handoff for future agents in this repo.

## Working rules

- Respond in English unless asked otherwise.
- Ask clarifying questions before non-trivial code; skip the pause for small doc/mechanical edits.
- Dont start coding if the prompt is just some question.
- Test every non-trivial change (run the app/scripts or add automated tests) and report what was and wasn't verified.
- Don't commit or push without explicit approval. Split commits into related chunks with clear messages.

## What this is

`rag-avatar` is a FastAPI RAG web app: ask questions over a document collection, stream a grounded answer, inspect cited sources. Default domain is Czech history, but the goal is a general, configurable avatar framework — some prompts, questions, UI copy, asset paths, and collection ids are still hardcoded to history and should move into config.

Stack: FastAPI · hosted `msearch` retrieval (default) · local/remote Qdrant · sentence-transformers embeddings · hybrid dense+BM25 (local weights 0.7/0.3) · OpenAI-compatible chat completions for generation.

## Layout

- `app/main.py` — routes, model presets, public settings, lifespan shutdown
- `app/config.py`, `app/models.py`, `app/logging_config.py`
- `app/rag/` — ingestion, chunking, retrieval, prompting, vector store, pipeline
- `app/rag/wp_config.py` — single source of WP config (labels, built-in prompts, collections, defaults)
- `app/rag/placeholders.py` — placeholder engine + `DEFAULT_PLACEHOLDERS` floor
- `app/static/` — frontend (index.html, app.js, styles.css)
- `scripts/` — `ingest.py`, `ask.py`, `batch_answers.py`, `download_wikipedia.py`
- `data/raw/` source docs · `data/processed/chunks.jsonl` · `data/qdrant/` local store
- `data/prompt_presets.json`, `data/placeholders.json` — shared overlays (gitignored, may be absent)
- `data/collections/czech_history/questions/questions.txt` — random-question + downloader + batch seed

## Run

Python 3.12.

```bash
uv venv --python python3.12 && source .venv/bin/activate
uv pip install -e .
cp .env.example .env
uvicorn app.main:app --reload   # http://127.0.0.1:8000
```

Minimum `.env` for hosted msearch: `LLM_API_KEY`, `LLM_MODEL`, `RETRIEVAL_BACKEND=msearch`, `MSEARCH_USERNAME`, `MSEARCH_PASSWORD`.

- Generation is generic OpenAI-compatible (`LLM_BASE_URL`/`LLM_API_KEY`/`LLM_MODEL`); `OPENROUTER_*` are legacy aliases. The UI's `LLM API` panel can override base URL/key per browser session.
- `ADMIN_PASSWORD` unlocks the full preset list and authorizes editing/deleting shared presets owned by others. (Replaced `LLM_UNLOCK_PASSWORD`, no back-compat.)
- `.env` intentionally wins over exported shell env vars (an old exported `OPENROUTER_API_KEY` used to override it). On odd LLM behavior, check the key fingerprint in startup logs — never print the key.

Local retrieval: `RETRIEVAL_BACKEND=local`, add docs under `data/raw/`, then `uv run python scripts/ingest.py --path data/raw`.

CLI test: `uv run python scripts/ask.py "Jaký byl význam husitských válek?"`

## WP config, prompts, placeholders

- WPs are typed dataclasses in `wp_config.py` (not env/JSON): `WP1-historie`, `WP2-média`, `WP3-právo`, `WP4-adiktologie`. WP1 holds the history prompts (`Učitel`/`Historik`/`Laik`); WP2–WP4 ship neutral starters.
- Collections map by number prefix (WP1→`wp1-*`, etc.). `wp_config.py` entries are only the offline fallback; at runtime `MSearchRetriever.live_collections_by_prefix()` lists live versions (cached 1h, busted by `/llm-providers/refresh`), injected into `/settings` by `_wps_payload_with_live_collections()` in `main.py`.
- AI-Ufal gating is per-WP (`WPConfig.requires_aiufal`, currently WP2). Backend `_enforce_msearch_collection_policy` gates by `wp_id`; frontend disables gated collections unless AI Ufal provider is selected.
- `/settings` exposes `wps` + `default_wp`; built-in prompts appear even without `data/prompt_presets.json`.
- Preset JSON shape (shared file + browser `localStorage`): `{id, name, wp_id, system_prompt, user_prompt_template, placeholders, owner_id, updated_at}`. Every preset stores `wp_id`; unknown/missing falls back to default WP. Legacy `style_prompts`/`length_prompts` removed; loader tolerates malformed files.

### Placeholders

- `DEFAULT_PLACEHOLDERS` (`length`, `custom_instructions`) is the floor. System placeholders (`{question}`, `{retrieved_snippets}`, `{current_date}`) are server-filled and hidden. Parameter placeholders (`select`/`text`) become data-driven main-page controls.
- Resolution, most specific wins (no option merging): inline-on-prompt → browser-local global → shared overlay (`data/placeholders.json`) → `DEFAULT_PLACEHOLDERS` → undeclared (render literally + warn, never crash).
- Chat request carries `selections` and `placeholder_defs` so the server stays stateless about `localStorage`. Shared-overlay edits need `owner_id` or `ADMIN_PASSWORD`; browser-local defs need none.

## Retrieval & UI

- Default backend `msearch`; hybrid already implemented. mSearch can return very short keyword snippets — watch grounding quality.
- UI controls: `top_k` 0–50 (`0` disables retrieval), dense/BM25 weights, min score, min relative score, backend, mSearch collection/mode/confidence floor, retrieve-only mode, LLM model + custom base URL/key.
- Implemented UX: dark mode, help modal, streaming `/chat/stream`, conversation threads + history in `localStorage`, random question (`/questions/random`), editable presets (`/prompt-presets`), expandable sources, lexical query-term highlighting (not embedding-similarity).

## Prompting

- Prompt lives in `app/rag/prompts.py`, currently a Czech historical-assistant prompt — update text/examples for other domains. Model is asked to: answer in the question's language, separate sourced info from general knowledge, cite only used sources, avoid weak chunks, not force a rigid `Podle nalezených zdrojů...` opener. For non-history questions: answer briefly, note it's primarily a historical assistant, don't force citations.

## WP1 subset (special data)

- `data/raw/WP1-2026-02-subset/` has nested folders with PDFs + folder-level `meta.md` (ingestion parses these).
- UI shows generated storage links for WP1 files; source paths omit the `data/raw/` prefix. Link format:
  `https://storage.ufal.mff.cuni.cz/lib/2e093cea-cdcd-401d-a664-d1ca05112e55/file/v2026-02/<folder>/<filename>`

## Operational notes

- Re-ingest when: `data/raw/` docs change, `EMBEDDING_MODEL` changes, chunking/metadata-parsing changes, or `data/raw/agent.md` changes. Never mix embedding models in one collection.
- `data/raw/agent.md` is intentionally tracked — it grounds answers to `Kdo jsi?`. Re-ingest if edited.
- Each run writes a fresh timestamped log under `logs/` (API, ingest, ask, downloader). FastAPI lifespan closes the pipeline/vector store on shutdown (fixed a leaked-semaphore warning on Ctrl+C; if it returns, suspect `uvicorn --reload`).
- `scripts/download_wikipedia.py` is test-data only (curated list → search from questions.txt, skips existing, tolerates 403/429). Don't make the project Wikipedia-dependent.
- Ignored scratch: `answers_avatar*.txt`, `notes.md`, most of `data/raw/`, `data/collections/.obsidian/`, `.../topics/`, `.../wiki/`, `data/topics.txt`. The file is tracked as `agents.md` (case-insensitive FS may show `AGENTS.md`).

## Debug first

`pipeline.py`, `retrieval.py`, `documents.py`, `prompts.py`, `llm.py`, `vector_store.py` (in `app/rag/`); `app/main.py`; `app/static/{index.html,app.js,styles.css}`.

## Open issues / next steps

- Conversation retrieval: rewrite follow-ups into standalone queries before retrieval, keep original wording for the answer.
- Markdown rendering: custom `renderMarkdown()` in `app.js` doesn't render pipe tables; citations expect `[^Z1]` but models sometimes emit bare numbers that don't link.
- Frontend can't persist/send non-custom provider base-URL overrides despite the UI shape suggesting it can (`persistLlmSettings()` / `selectedProviderBaseUrl()`).
