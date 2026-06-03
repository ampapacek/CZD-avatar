# rag-avatar

`rag-avatar` is a web app for asking questions over a document collection. It finds relevant source passages, streams an answer, shows the retrieved documents beside the answer, and keeps citations visible so you can inspect what the answer is based on.

The current default setup is a Czech-history avatar. A few places are still hardcoded for the historical agent and Czech-history collection, especially default prompts, random questions, UI text, collection assets, and helper scripts. The underlying RAG pipeline is topic-agnostic, though: with different documents, retrieval settings, and prompts it can be used for other domains.

## Quick Start

Use Python 3.12. The system `python` command may not exist on this machine, so the examples use `uv`.

```bash
uv venv --python python3.12
source .venv/bin/activate
uv pip install -e .
cp .env.example .env
```

Edit `.env`.

For the default hosted `msearch` flow, define one or more providers in `.env`. A minimal example looks like this:

```env
LLM_PROVIDER=aiufal
LLM_MODELS_CACHE_TTL_SECONDS=3600
LLM_PROVIDERS=aiufal,openrouter

LLM_PROVIDER_AIUFAL_NAME=AI Ufal
LLM_PROVIDER_AIUFAL_BASE_URL=https://ai.ufal.mff.cuni.cz/api
LLM_PROVIDER_AIUFAL_API_KEY=your_ai_ufal_key
LLM_PROVIDER_AIUFAL_DEFAULT_MODEL=LLM1-A40.llama3.3:latest
LLM_PROVIDER_AIUFAL_PUBLIC_MODELS=*
LLM_PROVIDER_AIUFAL_DISCOVER_MODELS=true

LLM_PROVIDER_OPENROUTER_NAME=OpenRouter
LLM_PROVIDER_OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
LLM_PROVIDER_OPENROUTER_API_KEY=your_openrouter_key
LLM_PROVIDER_OPENROUTER_DEFAULT_MODEL=openrouter/free
LLM_PROVIDER_OPENROUTER_PUBLIC_MODELS=openrouter/free
LLM_PROVIDER_OPENROUTER_DISCOVER_MODELS=true

RETRIEVAL_BACKEND=msearch
MSEARCH_USERNAME=your_username
MSEARCH_PASSWORD=your_password
```

`MSEARCH_BASE_URL`, `MSEARCH_COLLECTION`, `MSEARCH_MODE`, and the other mSearch defaults are already present in `.env.example`.

## LLM Providers

Generation uses OpenAI-compatible chat-completions APIs. You can point the app at any number of compatible providers by giving each one its own block of environment variables.

Each provider can define:

- a display name
- a base URL
- an API key
- a default model
- a static model list, or `DISCOVER_MODELS=true` to fetch models from `MODELS_URL` or the provider’s `/models` endpoint
- an optional public model list for browser use without an API key
- an optional API key label for the UI

If `LLM_PROVIDER` is set, that provider is selected by default in the UI. If it is empty, the first provider in `LLM_PROVIDERS` is used.

Discovered model lists are cached server-side for `LLM_MODELS_CACHE_TTL_SECONDS`, which defaults to `3600` seconds. Opening the app refreshes stale model lists through `/settings`; the Settings dialog also has an `Obnovit seznam modelů` button that forces an immediate server-side refresh without exposing provider API keys to the browser.

If you also set `LLM_UNLOCK_PASSWORD`, the browser can enter that shared password to unlock the full model list. Without it, only the public models configured for the selected provider appear in the selector.

Set `LLM_PROVIDER_<ID>_PUBLIC_MODELS=*` to make every resolved model for that provider public. If discovery succeeds, this means all discovered models. If discovery fails, it means the fallback configured models from `MODELS` plus `DEFAULT_MODEL`.

When `DISCOVER_MODELS=true`, discovered models are treated as authoritative. `MODELS` is used only as a fallback if discovery fails, so stale explicit model names do not appear while provider discovery is working.

Provider API keys go into `LLM_PROVIDER_<ID>_API_KEY`, where `<ID>` is the uppercase provider id from `LLM_PROVIDERS`. For example, `aiufal` uses `LLM_PROVIDER_AIUFAL_API_KEY`, and `openrouter` uses `LLM_PROVIDER_OPENROUTER_API_KEY`.

AI Ufal exposes models at:

```bash
curl -H "Authorization: Bearer $TOKEN" https://ai.ufal.mff.cuni.cz/api/models | jq ".data[].id"
```

OpenRouter has the same OpenAI-compatible shape and can usually list models without a key:

```bash
curl https://openrouter.ai/api/v1/models | jq ".data[].id"
```

The app filters internal/non-chat model ids matching `rag-*` and `openwebuidocs` from configured and discovered model lists.

## Run The App

Start the API and frontend:

```bash
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

The default experience uses hosted `msearch` retrieval, so you can run the app without ingesting local documents first.

## Ask A Question

From the browser, try a Czech-history question such as:

- `Jaký byl význam husitských válek?`
- `Co znamenalo Pražské jaro?`

From the CLI:

```bash
uv run python scripts/ask.py "Jaký byl význam husitských válek?"
```

Optional controls:

```bash
uv run python scripts/ask.py "Co znamenala bitva na Bílé hoře pro české země?" --style historik --length long --custom-instructions "Zaměř se na příčiny a důsledky."
```

## Use A Local Database Instead

If you want to use local Qdrant + BM25 retrieval instead of hosted `msearch`, do this:

1. Set `RETRIEVAL_BACKEND=local` in `.env`.
2. Put your `.txt`, `.md`, or `.pdf` files under `data/raw/`.
3. Ingest the files into the local index.
4. Run the app or ask questions from the CLI.

Example:

```env
RETRIEVAL_BACKEND=local
```

```bash
uv run python scripts/ingest.py --path data/raw
uvicorn app.main:app --reload
```

The ingest step creates/updates:

- local Qdrant storage in `data/qdrant/`
- BM25/debug chunk catalog in `data/processed/chunks.jsonl`

## Add Local Documents

Put `.txt`, `.md`, or `.pdf` files under:

```text
data/raw/
```

Text and Markdown files may include simple metadata frontmatter:

```md
---
title: Bitva na Bílé hoře
url: https://example.org/source
source_name: archive
document_type: article
historical_period: raný novověk
---

Document text...
```

## Czech Wikipedia Test Data

Czech Wikipedia is only for testing the current Czech-history collection before your own document collection is ready.

```bash
uv run python scripts/download_wikipedia.py --limit 100
```

The script reads `data/collections/czech_history/questions/questions.txt`, searches Czech Wikipedia, and saves Markdown files with metadata into `data/raw/wikipedia/`.

## Ingest Local Documents

```bash
uv run python scripts/ingest.py --path data/raw
```

This creates/updates:

- local Qdrant storage in `data/qdrant/`
- BM25/debug chunk catalog in `data/processed/chunks.jsonl`

## API

API endpoints:

- `GET /health`
- `GET /settings`
- `GET /questions/random`
- `GET /prompt-presets`
- `POST /prompt-presets`
- `DELETE /prompt-presets/{preset_id}`
- `POST /ingest`
- `POST /retrieve`
- `POST /chat`
- `POST /chat/stream`

Example `/chat` body:

```json
{
  "question": "Jaký byl význam husitských válek?",
  "style": "ucitel",
  "length": "medium",
  "retrieval_backend": "msearch",
  "custom_instructions": "Focus mainly on causes and consequences."
}
```

## Answer Grounding

The prompt instructs the model to separate:

- claims supported by retrieved chunks,
- general historical knowledge,
- uncertainty or insufficient coverage in the retrieved documents.

The model should first decide whether retrieved chunks are actually relevant. It should cite only chunks that support the answer, avoid forced citations from weak matches, and may add general historical context without pretending it came from the retrieved documents.

The answer cites retrieved chunks with Markdown footnotes. In the answer text these appear as simple footnote numbers, while the generated source list keeps stable source ids such as `[Z1]`, `[Z2]`, etc. The frontend displays source metadata and excerpts, highlights cited sources on the right, and lets you expand retrieved chunks.

## Retrieval Controls

The web UI lets you tune retrieval while testing:

- `top-k` from 0 to 50
- embedding vs. BM25 weighting
- minimum combined score
- minimum score relative to the best retrieved chunk
- cross-encoder reranker weight (0 disables it; moving the slider above 0 enables reranking and warns that it slows retrieval)
- retrieval backend: `msearch` or `local`
- mSearch collection, mode, and optional confidence floor
- retrieve-only mode, which shows chunks without calling the LLM
- LLM model preset or custom model id
- optional custom OpenAI-compatible LLM base URL and API key in the `LLM API` panel
- editable prompt presets stored in `data/prompt_presets.json`

## Reranking

After first-stage retrieval (`msearch` or `local`), an optional cross-encoder reranker can reorder the candidates. The cross-encoder scores each `(question, chunk)` pair jointly, which is more accurate than the bi-encoder/BM25 first stage but slower, so it only runs on a larger candidate pool (`RERANKER_CANDIDATES`) which is then truncated back to `top-k`.

It is **disabled by default**. Set the `Váha re-rankingu` slider above 0 (or `RERANKER_WEIGHT>0` with `RERANKER_ENABLED=true`) to enable it. The weight blends the reranker score with the first-stage score: `0` ignores the reranker, `1` trusts it entirely, and intermediate values mix both (each signal is min-max normalized across the candidates first). The default model is `BAAI/bge-reranker-v2-m3` (multilingual, covers Czech), run locally. Reranking happens before the conversation/token-budget step, so the chunks dropped to fit the context window are chosen from the reranked order.

### Downloading the model

The model is **never downloaded on demand** — the reranker loads with `local_files_only=True`, so a request can never trigger a multi-gigabyte download, and an end user cannot fetch it from the UI. A **developer must download it ahead of time**; until it is present, `reranker_model_available()` returns false and the rerank controls stay hidden.

Download it once (needs internet, ~2.3 GB):

```bash
# into the default Hugging Face cache (~/.cache/huggingface/hub)
python3 -c "from huggingface_hub import snapshot_download; snapshot_download('BAAI/bge-reranker-v2-m3')"
# or with the CLI:
huggingface-cli download BAAI/bge-reranker-v2-m3
```

For another server (e.g. air-gapped), download to a directory and point `RERANKER_MODEL` at it:

```bash
huggingface-cli download BAAI/bge-reranker-v2-m3 --local-dir /models/bge-reranker-v2-m3
# copy /models/bge-reranker-v2-m3 to the target machine, then set in .env:
#   RERANKER_MODEL=/models/bge-reranker-v2-m3
```

`reranker_model_available()` accepts either a populated HF cache entry or a local directory path.

When reranking is active, the response also carries the pre-rerank top-k (`baseline_chunks`) — the chunks that would have been shown without the cross-encoder. The Sources panel exposes a **Porovnat s pořadím bez re-rankingu** button that reveals a second column with that baseline ordering, so you can compare what reranking changed.

To hide the reranker's latency, the streaming endpoint (`/chat/stream`) reveals progressively: it emits a `preliminary_sources` event with the first-stage hits as soon as retrieval finishes, then runs the cross-encoder and emits the final `sources` event, which replaces them with the reranked order.

## Configuration

Important `.env` variables:

- `LLM_PROVIDER`
- `LLM_PROVIDERS`
- `LLM_UNLOCK_PASSWORD`
- `LLM_MODELS_CACHE_TTL_SECONDS`
- `LLM_PROVIDER_<ID>_NAME`
- `LLM_PROVIDER_<ID>_BASE_URL`
- `LLM_PROVIDER_<ID>_API_KEY`
- `LLM_PROVIDER_<ID>_DEFAULT_MODEL`
- `LLM_PROVIDER_<ID>_PUBLIC_MODELS`
- `LLM_PROVIDER_<ID>_MODELS`
- `LLM_PROVIDER_<ID>_MODELS_URL`
- `LLM_PROVIDER_<ID>_DISCOVER_MODELS`
- `LLM_PROVIDER_<ID>_SUPPORTS_STREAMING`
- `LLM_PROVIDER_<ID>_API_KEY_LABEL`
- `QDRANT_URL` for a remote/server Qdrant; leave empty for local disk mode
- `QDRANT_PATH`
- `QDRANT_COLLECTION`
- `EMBEDDING_MODEL`
- `CHUNK_SIZE`
- `CHUNK_OVERLAP`
- `TOP_K`
- `MIN_SCORE`
- `MIN_RELATIVE_SCORE`
- `RETRIEVAL_BACKEND`
- `RERANKER_ENABLED`
- `RERANKER_MODEL`
- `RERANKER_WEIGHT`
- `RERANKER_CANDIDATES`
- `MSEARCH_BASE_URL`
- `MSEARCH_USERNAME`
- `MSEARCH_PASSWORD`
- `MSEARCH_COLLECTION`
- `MSEARCH_MAX_RESULTS`
- `MSEARCH_MODE`
- `MSEARCH_MIN_CONFIDENCE`
- `MSEARCH_TIMEOUT`
- `DEFAULT_STYLE`
- `DEFAULT_LENGTH`
- `RAW_DATA_DIR`
- `CHUNK_CATALOG_PATH`
- `PROMPT_PRESETS_PATH`

## Basic Test Run

```bash
uv run python scripts/download_wikipedia.py --limit 20
uv run python scripts/ingest.py --path data/raw
uv run python scripts/ask.py "Jaký byl význam husitských válek?"
uvicorn app.main:app --reload
```

Then test in the browser:

- style `učitel`, length `medium`
- question `Jaký byl význam husitských válek?`
- confirm the answer is Czech and shows citations
- ask a question weakly covered by the indexed files and confirm the answer marks limited evidence

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

## Collections And Prompts

For now, `data/raw/` acts as the active indexed document collection and `app/rag/prompts.py` contains the built-in default prompts. Saved prompt presets are stored in `data/prompt_presets.json`. The Czech-history app metadata and UI assets are kept under `data/collections/czech_history/`.

Collection-specific app assets currently live under `data/collections/czech_history/`:

- random-question seed file: `questions/questions.txt`
- extended question set: `questions/questions_extended.txt`
- topic list: `topics/topics.txt`
- UFAL logo asset: `app/static/logo_ufal_110u.png`

The app can be adapted to any topic, but this is not fully configuration-driven yet. When creating a new avatar/domain, check and update the default prompts, random-question file, frontend labels, collection asset paths in `app/main.py`, example questions, and any collection-specific helper scripts. Future versions should make collections and prompts selectable, for example by using separate folders/config files per avatar.

## Notes For Future Extensions

- Configure additional providers by adding another `LLM_PROVIDER_<ID>_*` block.
- Manage context-window size more explicitly for providers with large model catalogs:
  - add a manual context-window limit in Advanced options
  - later, derive defaults from the selected model and its known maximum context length
  - for now, keep the retrieval set small, roughly Top10, and trim it to the model's context window
  - ideally use the same tokenizer as the selected model when counting tokens
- Add richer metadata extraction for your real historical archive.
- Add evaluation sets and automated citation-grounding checks.
- Add selectable collections and system prompts for different avatars.
