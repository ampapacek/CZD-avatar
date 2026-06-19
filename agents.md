# Agent Notes

Practical handoff for future agents in this repo.

## Working rules

- Respond in English unless asked otherwise.
- Treat "can we / could we / should we / is it possible / what about X?" as questions, not work orders. Answer with feasibility + approach; do NOT touch code until the user explicitly says to build it.
- For anything beyond a small/mechanical change, first reply with a short plan (files you'd touch, trade-offs, rough size) and wait for a clear go-ahead — even if implementing seems obviously wanted. Bigger change = more important to pause.
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
- `data/questions/*.txt` — private per-WP random/prepared questions (gitignored, may be absent)
- `data/collections/czech_history/` — Czech-history assets/metadata kept for the current WP1 setup

## Run

Python 3.12.

```bash
uv venv --python python3.12 && source .venv/bin/activate
uv pip install -e .
cp .env.example .env
uvicorn app.main:app --reload   # http://127.0.0.1:8000
```

Minimum `.env` for hosted msearch: one or more `LLM_PROVIDER_<ID>_*` provider blocks, `LLM_PROVIDER`, `LLM_PROVIDERS`, `RETRIEVAL_BACKEND=msearch`, `MSEARCH_USERNAME`, `MSEARCH_PASSWORD`.

- Generation is generic OpenAI-compatible, configured through provider env vars: `LLM_PROVIDER_<ID>_BASE_URL`, `API_KEY`, `DEFAULT_MODEL`, `PUBLIC_MODELS`, optional `MODELS`, `MODELS_URL`, `DISCOVER_MODELS`, `SUPPORTS_STREAMING`, `API_KEY_LABEL`. The UI's `LLM API` panel can override base URL/key per browser session.
- `LLM_MODELS_CACHE_TTL_SECONDS` controls server-side discovered model cache; `/llm-providers/refresh` busts model and live mSearch collection caches.
- `ADMIN_PASSWORD` unlocks the full model list and authorizes editing/deleting shared presets owned by others. (Replaced `LLM_UNLOCK_PASSWORD`, no back-compat.)
- `.env` intentionally wins over exported shell env vars (an old exported `OPENROUTER_API_KEY` used to override it). On odd LLM behavior, check the key fingerprint in startup logs — never print the key.

Local retrieval: `RETRIEVAL_BACKEND=local`, add docs under `data/raw/`, then `uv run python scripts/ingest.py --path data/raw`.

CLI test: `uv run python scripts/ask.py "Jaký byl význam husitských válek?"`

## WP config, prompts, placeholders

- WPs are typed dataclasses in `wp_config.py` (not env/JSON): `WP1-historie`, `WP2-média`, `WP3-právo`, `WP4-adiktologie`. WP1 holds the history prompts (`Učitel`/`Historik`/`Laik`); WP2–WP4 ship neutral starters.
- Collections map by number prefix (WP1→`wp1-*`, etc.). `wp_config.py` entries are only the offline fallback; at runtime `MSearchRetriever.live_collections_by_prefix()` lists live versions (cached 1h, busted by `/llm-providers/refresh`), injected into `/settings` by `_wps_payload_with_live_collections()` in `main.py`.
- AI-Ufal gating is per-WP (`WPConfig.requires_aiufal`, currently WP2). Backend `_enforce_msearch_collection_policy` gates by `wp_id`; frontend disables gated collections unless AI Ufal provider is selected.
- Random/prepared questions are per-WP plain-text files configured by `WPConfig.questions_path`: `data/questions/wp1-historie.txt`, `wp2-media.txt`, `wp3-pravo.txt`, `wp4-adiktologie.txt`. These are private/gitignored; missing files make `/questions/random` and `/questions` return 404 for that WP only.
- `/settings` exposes `wps` + `default_wp`; built-in prompts appear even without `data/prompt_presets.json`.
- Preset JSON shape (shared file + browser `localStorage`): `{id, name, wp_id, system_prompt, user_prompt_template, placeholders, owner_id, updated_at}`. Every preset stores `wp_id`; unknown/missing falls back to default WP. Legacy `style_prompts`/`length_prompts` removed; loader tolerates malformed files.

### Placeholders

- `DEFAULT_PLACEHOLDERS` (`length`, `custom_instructions`) is the floor. System placeholders (`{question}`, `{retrieved_snippets}`, `{current_date}`) are server-filled and hidden. Parameter placeholders (`select`/`text`) become data-driven main-page controls.
- Resolution, most specific wins (no option merging): inline-on-prompt → browser-local global → shared overlay (`data/placeholders.json`) → `DEFAULT_PLACEHOLDERS` → undeclared (render literally + warn, never crash).
- Chat request carries `selections` and `placeholder_defs` so the server stays stateless about `localStorage`. Shared-overlay edits need `owner_id` or `ADMIN_PASSWORD`; browser-local defs need none.

## Retrieval & UI

- Default backend `msearch`; hybrid already implemented. mSearch can return very short keyword snippets — watch grounding quality.
- UI controls: `top_k` 0–50 (`0` disables retrieval), dense/BM25 weights, min score, min relative score, backend, mSearch collection/mode/confidence floor, retrieve-only mode, reranking controls, LLM provider/model + custom base URL/key.
- Optional cross-encoder reranking runs after first-stage retrieval when enabled and available (`RERANKER_ENABLED`, `RERANKER_WEIGHT`, `RERANKER_CANDIDATES`, default model `BAAI/bge-reranker-v2-m3`). It uses `local_files_only=True`, so developers must pre-download the model; otherwise rerank controls stay hidden.
- Streaming `/chat/stream` can emit preliminary first-stage sources before reranking finishes, then final reranked sources. Responses may include `baseline_chunks` for comparing pre/post-rerank ordering in the UI.
- Implemented UX: dark mode, help modal, streaming `/chat/stream`, conversation threads + history in `localStorage`, random question (`/questions/random`), prepared questions (`/questions`), editable presets (`/prompt-presets`), expandable sources, lexical query-term highlighting (not embedding-similarity).

## Prompting

- Base prompt helpers live in `app/rag/prompts.py`; WP-specific built-in prompts live in `app/rag/wp_config.py`. WP1 still uses Czech-history personas, while WP2–WP4 use generic domain prompts. Model is asked to: answer in the question's language, separate sourced info from general knowledge, cite only used sources, avoid weak chunks, not force a rigid `Podle nalezených zdrojů...` opener, and not generate its own final source list.

