# Agent Notes

This file is a practical handoff for future agents working in this repo.

## Collaboration rules

- Respond in English unless the user explicitly asks for another language.
- Before writing any non-trivial code, ask detailed clarifying questions and wait for answers. Small documentation edits, mechanical fixes, and clearly requested one-line changes do not need this pause.
- Test every non-trivial change before calling it done. Use the most relevant path: run the app and exercise it directly for UI/API behavior, run scripts for CLI behavior, or add/run automated tests when that gives better coverage.
- When testing directly, include enough detail in the final report that the user can see what was verified and what was not.
- Before committing, ask the user for approval. Prepare related git commits and clear commit messages, but do not commit or push without explicit user permission unless the user has already stated otherwise.
- Split commits into related chunks instead of committing all changes at once.

## What this project is

- `rag-avatar` is a RAG web app for asking questions over a document collection, streaming an answer, and inspecting the retrieved/cited sources.
- The current default avatar is Czech history, but the intended direction is a general avatar framework, not a history-only app.
- A few places are still hardcoded for the historical agent and Czech-history collection, including default prompts, random questions, UI copy, collection asset paths, and helper scripts.
- The underlying RAG pipeline is topic-agnostic and should be made fully configurable across domains by moving prompts, questions, assets, mSearch collections, and UI labels into avatar/collection config.
- Main goal: retrieve passages from hosted `msearch` or local documents and answer with grounded citations.
- Current stack:
  - FastAPI
  - hosted `msearch` retrieval
  - local/remote Qdrant
  - sentence-transformers embeddings
  - hybrid retrieval: dense + BM25
  - An OpenAI-compatible API for generation, with OpenRouter as one optional provider

## Important directories

- `app/main.py` - FastAPI app, routes, model presets, public settings, lifespan shutdown
- `app/models.py` - API request/response models
- `app/config.py` - settings loading
- `app/logging_config.py` - timestamped logging into `logs/`
- `app/rag/` - ingestion, chunking, retrieval, prompting, vector store, pipeline
- `app/static/` - frontend HTML/CSS/JS
- `data/prompt_presets.json` - saved prompt presets for the UI if present
- `scripts/ingest.py` - CLI ingestion
- `scripts/ask.py` - CLI ask
- `scripts/batch_answers.py` - batch question/answer runner
- `scripts/download_wikipedia.py` - test-data downloader
- `data/collections/czech_history/questions/questions.txt` - random-question seed and default batch/download input
- `data/collections/czech_history/questions/questions_extended.txt` - extended local question set
- `app/static/logo_ufal_110u.png` - logo served by the app
- `data/raw/` - source documents
- `data/processed/chunks.jsonl` - persisted chunk catalog for BM25/debug
- `data/qdrant/` - local Qdrant storage

## Repo hygiene

- `answers_avatar*.txt` and `notes.md` are ignored scratch/output files.
- `data/raw/` is mostly ignored, but `data/raw/agent.md` is intentionally tracked and should stay retrievable.
- `data/collections/czech_history/questions/questions.txt` is reused by the random-question endpoint, the Wikipedia downloader, and `scripts/batch_answers.py`.
- `data/collections/.obsidian/`, `data/collections/czech_history/topics/`, `data/collections/czech_history/wiki/`, and `data/topics.txt` are now ignored local workspace/content files.
- Git tracks this handoff file as `agents.md`; on this machine the working tree may display it as `AGENTS.md` because the filesystem is case-insensitive.

## How to run

Use Python 3.12.

```bash
uv venv --python python3.12
source .venv/bin/activate
uv pip install -e .
cp .env.example .env
```

For the default hosted `msearch` flow, set at least:

```env
LLM_API_KEY=your_key_here
LLM_MODEL=meta-llama/llama-3.3-70b-instruct
RETRIEVAL_BACKEND=msearch
MSEARCH_USERNAME=your_username
MSEARCH_PASSWORD=your_password
```

Despite the legacy alias names, generation is generic OpenAI-compatible chat completions. Set `LLM_BASE_URL`, `LLM_API_KEY`, and `LLM_MODEL` for another hosted provider or an OpenAI-compatible local server. The frontend `LLM API` panel can also override base URL/API key for the current browser session.

Future config cleanup should keep the `LLM_*` names as the primary interface, retain `OPENROUTER_*` as backward-compatible aliases for at least one release, and continue updating docs/UI copy to avoid implying that OpenRouter is required.

If a shared override is needed, `LLM_UNLOCK_PASSWORD` can unlock the full preset list in the browser while keeping the public-only default for everyone else.

Run the app:

```bash
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

Quick CLI test:

```bash
uv run python scripts/ask.py "Jaký byl význam husitských válek?"
```

If local retrieval is needed instead, set `RETRIEVAL_BACKEND=local`, add documents under `data/raw/`, then ingest:

```bash
uv run python scripts/ingest.py --path data/raw
uvicorn app.main:app --reload
```

## Config and a past gotcha

- `.env` is intentionally preferred over already-exported shell env vars.
- This was changed because an old exported `OPENROUTER_API_KEY` kept overriding the local `.env` key.
- If the LLM provider behaves strangely, check startup logs for the key fingerprint logged by `app/main.py`.
- Never print the actual key.

## Retrieval behavior

- Hybrid retrieval is already implemented.
- Default backend is `msearch`.
- Watch grounding quality: mSearch can return very short keyword-like snippets for some queries, so source context may need expansion or reranking before generation.
- Local retrieval uses hybrid weighting:
  - dense embeddings: `0.7`
  - BM25: `0.3`
- Web UI allows changing:
  - `top_k` from `0` to `50`
  - dense/BM25 weighting
  - minimum score
  - minimum relative score to the best chunk
  - retrieval backend: `msearch` or `local`
  - mSearch collection, mode, and optional confidence floor
  - retrieve-only mode
  - LLM model and custom OpenAI-compatible LLM base URL/API key
- Prompt presets can be loaded, saved, and deleted from the UI.
- `top_k=0` intentionally disables retrieval.

## Current UX features already implemented

- Dark mode
- Help modal
- Streaming chat responses from `/chat/stream`
- Conversation workspace with saved threads in `localStorage`
- Local browser history stored in `localStorage`
- Random question button backed by `/questions/random`
- Editable prompt presets backed by `/prompt-presets`
- Expandable source chunks
- Highlighting of query terms inside source excerpts and full chunks
  - this is lexical highlighting based on the current question
  - it is not an explanation of embedding similarity

## Prompting behavior

- Prompt is in `app/rag/prompts.py`.
- It is currently written as a historical assistant prompt. For non-history domains, update the prompt text and any Czech-history examples/UI labels that shape behavior.
- The model is asked to:
  - answer naturally in the language of the question, usually Czech
  - separate sourced information from general knowledge and uncertainty
  - cite only sources actually used
  - avoid citing weak or irrelevant retrieved chunks
  - use general historical knowledge when retrieved context is not relevant enough, without pretending it came from sources
  - not always start with a rigid template like `Podle nalezených zdrojů...`
- For clearly non-historical questions:
  - respond briefly and naturally
  - mention it is primarily a historical assistant
  - do not force citations if they are not relevant

## Special data handling: WP1 subset

- `data/raw/WP1-2026-02-subset/` contains nested folders with PDFs and `meta.md`.
- Ingestion was extended to parse these folder-level metadata files.
- For WP1 files, the UI should show generated storage links in the source panel.
- URL pattern is based on the relative file path under:
  - `data/raw/WP1-2026-02-subset/`
- The generated document link format is:

```text
https://storage.ufal.mff.cuni.cz/lib/2e093cea-cdcd-401d-a664-d1ca05112e55/file/v2026-02/<folder>/<filename>
```

- Source paths shown in UI should omit the `data/raw/` prefix.

## Wikipedia downloader behavior

- `scripts/download_wikipedia.py`:
  - uses a curated fallback topic list first
  - then searches based on `data/collections/czech_history/questions/questions.txt`
  - prints light progress logging
  - skips files already present in the target directory
  - logs and skips Wikipedia 403/429/API failures instead of crashing
- This is only test-data tooling. The project should not become Wikipedia-dependent.

## Logging

- Every new run creates a fresh timestamped log file under `logs/`.
- This is already wired for:
  - API
  - ingest script
  - ask script
  - Wikipedia downloader
- Third-party noise was reduced to keep logs usable.

## Shutdown cleanup

- The pipeline and vector store have explicit `close()` methods.
- FastAPI lifespan in `app/main.py` closes the pipeline on shutdown.
- This was added because Ctrl+C used to trigger a leaked semaphore warning.
- If that warning returns, also check whether `uvicorn --reload` is the actual source.

## Re-ingestion rules

You should re-run ingestion if:

- documents in `data/raw/` changed
- `EMBEDDING_MODEL` changed
- chunking parameters changed
- metadata parsing behavior changed
- `data/raw/agent.md` changed and should become retrievable

Do not mix vectors from different embedding models in one collection.

## Identity document

- `data/raw/agent.md` exists on purpose.
- It gives the assistant a grounded answer to questions like `Kdo jsi?`
- If it is edited, re-ingest.

## Files worth checking first when debugging

- `app/rag/pipeline.py`
- `app/rag/retrieval.py`
- `app/rag/documents.py`
- `app/rag/prompts.py`
- `app/rag/llm.py`
- `app/rag/vector_store.py`
- `app/static/index.html`
- `app/static/app.js`
- `app/static/styles.css`
- `app/main.py`

## Known review findings

- `/chat` and `/retrieve` in `app/main.py` wrap intended `HTTPException` 400 errors as 500s because the broad `except Exception` handlers catch them. Add `except HTTPException: raise` before generic exception handling so user/config errors such as a locked model or disallowed WP2 collection keep their original status code.
- The frontend currently cannot persist or send non-custom provider base URL overrides even though the UI/API shape suggests it can. `app/static/app.js` has listeners for `llmBaseUrl`, but `persistLlmSettings()` does not store `base_url` for normal providers and `selectedProviderBaseUrl()` returns only the provider preset base URL outside the custom provider path.
- Streaming chat assumes the LLM stream object has an `upstream_model` attribute. `pipeline.llm.stream_generate()` is typed as returning `Iterator[str]`, so a future LLM client or test double that returns a plain generator could stream tokens successfully and then fail before the final `done` event when `app/main.py` reads `stream.upstream_model`.
- Last review verification: `./.venv/bin/python -m unittest discover -s tests -v` passed, and `./.venv/bin/python -m compileall -q app scripts tests` passed. `./.venv/bin/python -m pytest -q` could not run because `pytest` was not installed in the venv.

## Nice next improvements

- Make the avatar general, not history-only:
  - move Czech-history prompts, UI copy, questions, logo/assets, mSearch collection ids, and example questions into avatar/collection config
  - keep the current Czech-history setup as one configured avatar
  - make it easy to add domains such as law, floods, medicine, project docs, or internal knowledge bases without code edits
- Rename LLM configuration:
  - introduce `LLM_BASE_URL`, `LLM_API_KEY`, and `LLM_MODEL`
  - keep `OPENROUTER_BASE_URL`, `OPENROUTER_API_KEY`, and `OPENROUTER_MODEL` as aliases during migration
  - update app settings, docs, and UI wording so other OpenAI-compatible providers feel first-class
- Improve conversation retrieval:
  - rewrite follow-up questions using conversation history before retrieval
  - retrieve against the resolved standalone query, not only the latest short user turn
  - keep the original user wording for the final answer
- Add batch generation:
  - likely use backend/pipeline code directly rather than driving the browser UI
  - support input question files, selected avatar/collection, model/provider settings, and structured output with answer, sources, timings, and errors
- Improve answer Markdown rendering:
  - `app/static/app.js` uses a custom `renderMarkdown()` implementation and currently does not render pipe tables, so valid Markdown tables appear as plain text
  - add focused table parsing/styling or replace the custom renderer with a sanitized Markdown parser
  - keep citation handling compatible with app source IDs like `[^Z1]`; models sometimes emit bare numeric citations such as `1`, which do not link to the source panel
- Show the most relevant sentence window around matches, not just raw chunk previews
- Better semantic explanation of why a chunk matched
- Optional reranker after hybrid retrieval
- More robust evaluation scripts for grounding quality
