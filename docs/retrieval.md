# Retrieval and reranking

The supported setup uses the private mSearch service from MAMA AI. mSearch is also part of WP collection configuration, discovery, AI-Ufal gating, and `/settings`; retrieval backends do not share a general plugin interface.

## Retrieval Controls

The web UI lets you tune retrieval while testing:

- `top-k` from 0 to 50 (`0` disables retrieval entirely)
- embedding vs. BM25 weighting
- minimum combined score
- minimum score relative to the best retrieved chunk
- cross-encoder reranker weight (0 disables it; moving the slider above 0 enables reranking and warns that it slows retrieval)
- retrieval backend: `msearch` or `local`
- mSearch collection, mode, and optional confidence floor
- retrieve-only mode, which shows chunks without calling the LLM
- LLM model preset or custom model id
- context-window size, with known model defaults from `data/models.json`
- optional custom OpenAI-compatible LLM base URL and API key in the `LLM API` panel
- editable prompts (see [Prompts and placeholders](prompts.md#prompts-and-placeholders))

## Reranking

After first-stage retrieval (`msearch` or `local`), an optional cross-encoder reranker can reorder the candidates. The cross-encoder scores each `(question, chunk)` pair jointly, which can improve ordering compared with the bi-encoder/BM25 first stage but is slower, so it only runs on a larger candidate pool (`RERANKER_CANDIDATES`) which is then truncated back to `top-k`.

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

## Local retrieval reference

The local Qdrant + BM25 implementation and ingestion scripts remain as reference code. This workflow is not currently maintained or verified end to end. The following instructions describe the existing implementation:

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

The legacy Czech Wikipedia downloader provides test data for the local Czech-history reference workflow. Its default seed file is not included in a clean checkout; supply your own with `--questions`.

```bash
uv run python scripts/download_wikipedia.py --questions path/to/questions.txt --limit 100
```

By default, the script reads the legacy downloader seed file at `data/collections/czech_history/questions/questions.txt`, searches Czech Wikipedia, and saves Markdown files with metadata into `data/raw/wikipedia/`. You can point it at another seed file with `--questions`; the app's own random/prepared questions now live separately under `data/questions/`.

## Retrieval implementation notes

- The default mSearch mode is hybrid. It can return very short keyword snippets; check whether they provide enough evidence for grounded answers.
- The local reference stack uses local or remote Qdrant, sentence-transformers embeddings, and hybrid dense + BM25 retrieval (default weights 0.7/0.3).
