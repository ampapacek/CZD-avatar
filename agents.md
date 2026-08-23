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
- `app/static/` — frontend (index.html, app.js, styles.css) + the built `avatar.bundle.js`
- `frontend/` — ES modules bundled into `app/static/avatar.bundle.js` (global `Avatar`) by
  `npm run build`, with vitest coverage: `markdown-renderer.js`, `citations.js`,
  `sources-panel.js` (panel ordering/flip rules), `answer-export.js` (clipboard text).
  Entry point is `frontend/bundle.js`; rebuild after editing any of them.
- `scripts/` — `ingest.py`, `ask.py`, `batch_answers.py`, `download_wikipedia.py`
- `data/raw/` source docs · `data/processed/chunks.jsonl` · `data/qdrant/` local store
- `data/models.json` — the one tracked file describing models: context window, reasoning support, room for more. `MODEL_METADATA_PATH` overrides it.
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
- Preset JSON shape (shared file + browser `localStorage`): `{id, name, wp_id, note, system_prompt, user_prompt_template, placeholders, owner_id, updated_at}`. `note` is user-facing metadata and is never sent to the model. Every preset stores `wp_id`; unknown/missing falls back to default WP. Legacy `style_prompts`/`length_prompts` removed; loader tolerates malformed files.

### Placeholders

- `DEFAULT_PLACEHOLDERS` (`length`, `custom_instructions`) is the floor. System placeholders (`{question}`, `{retrieved_snippets}`, `{current_date}`) are server-filled and hidden. Parameter placeholders (`select`/`text`) become data-driven main-page controls.
- Resolution, most specific wins (no option merging): inline-on-prompt → browser-local global → shared overlay (`data/placeholders.json`) → `DEFAULT_PLACEHOLDERS` → undeclared (render literally + warn, never crash).
- Chat request carries `selections` and `placeholder_defs` so the server stays stateless about `localStorage`. Shared-overlay edits need `owner_id` or `ADMIN_PASSWORD`; browser-local defs need none.

## Retrieval & UI

- Default backend `msearch`; hybrid already implemented. mSearch can return very short keyword snippets — watch grounding quality.
- UI controls: `top_k` 0–50 (`0` disables retrieval), dense/BM25 weights, min score, min relative score, backend, mSearch collection/mode/confidence floor, retrieve-only mode, reranking controls, LLM provider/model + custom base URL/key.
- Optional cross-encoder reranking runs after first-stage retrieval when enabled and available (`RERANKER_ENABLED`, `RERANKER_WEIGHT`, `RERANKER_CANDIDATES`, default model `BAAI/bge-reranker-v2-m3`). It uses `local_files_only=True`, so developers must pre-download the model; otherwise rerank controls stay hidden.
- Streaming `/chat/stream` can emit preliminary first-stage sources before reranking finishes, then final reranked sources. Responses may include `baseline_chunks` for comparing pre/post-rerank ordering in the UI.
- Implemented UX: dark mode, help modal, streaming `/chat/stream`, conversation threads + history in `localStorage`, random question (`/questions/random`), prepared questions (`/questions`), editable presets (`/prompt-presets`), expandable sources, lexical query-term highlighting (not embedding-similarity), copy-answer buttons (main/conversation/history).
- Sources panel: retrieval order while streaming, then flips to first-citation order when the answer finishes, hiding uncited sources behind a control. Cards are titled with the citation number alone (`[2]`); the retrieval id `Z7` sits on the diagnostics line with the scores. The cited-source green is painted only when cited and uncited cards are visible together — otherwise it distinguishes nothing — while `cited-source` (pointer, hover border, click-to-highlight) marks every cited card. The view state is a parameter of `renderSourceCards`, shared by the main, conversation and history panels — do not turn it back into a module global. No flip for aborted/errored streams, retrieve-only mode, or an answer that cites nothing.
- Conversation compaction is rolling: the server folds all but the last `CONVERSATION_RECENT_MESSAGES` into a summary once the uploaded history passes `CONVERSATION_SUMMARY_TRIGGER_TOKENS`, returns `conversation_folded_message_count`, and the browser advances `conversation_compacted_through` so it stops uploading them.
- Reasoning: declared per model in `data/models.json` (request field, effort vocabulary, default, `mandatory`, human-only `note`), and discovered from the provider's own catalogue where one publishes it — only OpenRouter's `/api/v1/models` does, so only OpenRouter is asked (`LLM_PROVIDER_<ID>_DISCOVER_REASONING` overrides). A hand-written entry beats discovery, because it is where a probe of what the model actually did gets recorded. Nothing is sent for a model neither declares. An empty/absent `efforts` list with `mandatory: true` is the "reasons anyway, cannot be steered" case: no control is offered, no parameter is sent, the trace is still shown collapsed. `mandatory` and a `none`/`off` effort contradict each other and the loader strips the switch — gpt-oss-120b shipped both and 400ed on every answer. Add models to the JSON, never to code.
- The effort sent when nobody touches the selector is derived, not declared: `mandatory` → the cheapest level the model accepts, optional → nothing at all (`ReasoningSupport.effective_default`). Lowering a mandatory model changes only how much it thinks; sending a level to an optional one changes whether it thinks, which would silently alter answers for users who never asked. Declare `default` only to overrule that. `mistral-medium-3.5` is why the rule is not a blanket "low": it accepts only `none`/`high`.
- The AI Ufal Open WebUI gateway **drops** `reasoning_effort` and `reasoning` on every endpoint (`/api`, `/api/v1`, `/openai`) — probed 2026-08-22 and again 2026-08-23, when ten parameter forms including `reasoning_effort: "bogus"` all returned 200 with a byte-identical trace. So no ai.ufal model declares efforts, and nothing sent there can break. Re-probe if the gateway is upgraded. OpenRouter and e-infra both honour the parameter; e-infra rejects a level its model does not take with a 400, so its vocabularies are probed per model.
- `stream_generate` yields `(kind, text)` chunks, `ANSWER` or `REASONING` (`app/rag/llm.py`). Reasoning models emit the whole trace before the first answer token, so the trace streams to the browser as its own `reasoning` SSE event and the panel stays open until the answer starts. TTFT is measured from the first **answer** token — starting it on a reasoning delta would report a model as faster the longer it thinks. `stream.reasoning_text` still accumulates the trace whole for the `done` event and history.

## Prompting

- Base prompt helpers live in `app/rag/prompts.py`; WP-specific built-in prompts live in `app/rag/wp_config.py`. WP1 still uses Czech-history personas, while WP2–WP4 use generic domain prompts. Model is asked to: answer in the question's language, separate sourced info from general knowledge, cite only used sources, avoid weak chunks, not force a rigid `Podle nalezených zdrojů...` opener, and not generate its own final source list or `[^Zn]:` footnote definitions.
- Models emit that closing list anyway. `strip_model_source_list` (`app/rag/answer_cleanup.py`) removes it server-side; `prepareCitationMarkdown` (`frontend/citations.js`) does the same at render time for streaming tokens. Keep the two in sync — `tests/test_answer_cleanup.py` is the shared contract.
