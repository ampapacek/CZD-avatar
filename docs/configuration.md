# Configuration and LLM providers

Run commands from the repository root. Copy `.env.example` to `.env` and configure access before starting the app. The project `.env` takes precedence over exported shell variables.

## LLM Providers

Generation uses OpenAI-compatible chat-completions APIs. You can point the app at any number of compatible providers by giving each one its own block of environment variables.

Each provider can define:

- a display name
- a base URL
- an API key
- a default model
- a static model list, or `DISCOVER_MODELS=true` to fetch models from `MODELS_URL` or the provider’s `/models` endpoint
- optional context-window discovery from `MODEL_INFO_URL` or the provider’s `/model/info` endpoint, using `model_info.context_size`
- an optional public model list for browser use without an API key
- an optional API key label for the UI

If `LLM_PROVIDER` is set, that provider is selected by default in the UI. If it is empty, the first provider in `LLM_PROVIDERS` is used.

Discovered model lists and the live mSearch collections are fetched at startup and re-fetched in the background every `DISCOVERY_REFRESH_INTERVAL_SECONDS` (default `86400`, one day), so warm requests can use cached lists. Requests during startup prewarming can still wait for discovery. A failed refresh keeps the previous lists. `LLM_MODELS_CACHE_TTL_SECONDS` and `MSEARCH_COLLECTIONS_CACHE_TTL_SECONDS` (default `172800`) are the request-side fallback for when that refresh keeps failing; the Settings dialog also has an `Obnovit seznam modelů` button that forces an immediate server-side refresh without exposing provider API keys to the browser.

If you also set `ADMIN_PASSWORD`, the browser can enter that shared admin password to unlock the full model list and to modify or delete shared prompt presets owned by another browser (creating a new shared prompt stays open). Without it, only the public models configured for the selected provider appear in the selector. Creating shared prompts currently requires no admin password.

Set `LLM_PROVIDER_<ID>_PUBLIC_MODELS=*` to make every resolved model for that provider public. If discovery succeeds, this means all discovered models. If discovery fails, it means the fallback configured models from `MODELS` plus `DEFAULT_MODEL`.

When `DISCOVER_MODELS=true`, discovered models are treated as authoritative. `MODELS` is used only as a fallback if discovery fails, so stale explicit model names do not appear while provider discovery is working.

The unlocked OpenRouter selector defaults to a compact view: latest numeric
versions of GPT, Gemini, Claude Sonnet/Haiku, and DeepSeek within each recognized
variant. GPT mini/nano, Sol/Luna/Astra/Terra, GPT-OSS sizes,
Gemini Pro/Flash/Flash Lite, Claude Sonnet/Haiku, and DeepSeek Pro/Flash/reasoning
remain separate choices. Generic DeepSeek V-series models share the Pro slot.
Equal versions prefer stable over preview and unpinned routes over dated
snapshots; newer previews can replace older stable versions. Batch/free variants,
GPT models with the `-pro` suffix, image/audio models, Codex, and unfamiliar naming schemes are omitted from this
view. Public models and the current allowed selection remain visible.
**Zobrazit v seznamu všechny modely** restores the full allowed catalogue,
including older versions and other families; it never unlocks non-public models.
The toggle applies for the current page session. This is a naming-based display
filter, not a claim that each newer model is better; discovery and model metadata
still retain the full catalogue. Other providers are unaffected.

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

## Configuration

Important `.env` variables:

- `LLM_PROVIDER`
- `LLM_PROVIDERS`
- `ADMIN_PASSWORD`
- `LLM_MODELS_CACHE_TTL_SECONDS`
- `DISCOVERY_REFRESH_INTERVAL_SECONDS` (`0` runs discovery at startup only)
- `MSEARCH_COLLECTIONS_CACHE_TTL_SECONDS`
- `LLM_PROVIDER_<ID>_NAME`
- `LLM_PROVIDER_<ID>_BASE_URL`
- `LLM_PROVIDER_<ID>_API_KEY`
- `LLM_PROVIDER_<ID>_DEFAULT_MODEL`
- `LLM_PROVIDER_<ID>_PUBLIC_MODELS`
- `LLM_PROVIDER_<ID>_MODELS`
- `LLM_PROVIDER_<ID>_MODELS_URL`
- `LLM_PROVIDER_<ID>_MODEL_INFO_URL`
- `LLM_PROVIDER_<ID>_DISCOVER_MODELS`
- `LLM_PROVIDER_<ID>_SUPPORTS_STREAMING`
- `LLM_PROVIDER_<ID>_API_KEY_LABEL`
- `MODEL_METADATA_PATH` (context windows and reasoning support per model; see `data/models.json`)
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
- `RERANKER_MAX_LENGTH`
- `RERANKER_BATCH_SIZE`
- `RERANKER_DEVICE`
- `MSEARCH_BASE_URL`
- `MSEARCH_USERNAME`
- `MSEARCH_PASSWORD`
- `MSEARCH_COLLECTION`
- `MSEARCH_MAX_RESULTS`
- `MSEARCH_MODE`
- `MSEARCH_MIN_CONFIDENCE`
- `MSEARCH_TIMEOUT`
- `CONTEXT_WINDOW_TOKENS`
- `OUTPUT_TOKEN_BUDGET_SHORT`
- `OUTPUT_TOKEN_BUDGET_MEDIUM`
- `OUTPUT_TOKEN_BUDGET_LONG`
- `MIN_PROMPT_CHUNKS`
- `TOKEN_BUDGET_SAFETY_MARGIN`
- `CONVERSATION_SUMMARY_TRIGGER_TOKENS`
- `CONVERSATION_SUMMARY_TRIGGER_MESSAGES`
- `CONVERSATION_RECENT_MESSAGES`
- `RAW_DATA_DIR`
- `CHUNK_CATALOG_PATH`
- `PROMPT_PRESETS_PATH` (gitignored mutable overlay; may be absent)
- `PLACEHOLDERS_PATH` (gitignored mutable overlay; may be absent)

`MODEL_METADATA_PATH` replaces the earlier `MODEL_CONTEXT_WINDOWS_PATH` and `MODEL_REASONING_PATH`. It is not just a rename: the two files merged into one, with `models` and `provider_defaults` sections and `context_window` / `max_context_window` / `reasoning` per entry. `data/models.json` documents the shape in its own `_comment`.

## Multiple-provider example

This example preserves the existing provider setup. Replace the model ids and credentials with values available to your accounts.

```env
LLM_PROVIDER=aiufal
LLM_MODELS_CACHE_TTL_SECONDS=172800
LLM_PROVIDERS=aiufal,openrouter,einfra

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

LLM_PROVIDER_EINFRA_NAME=e-infra
LLM_PROVIDER_EINFRA_BASE_URL=https://llm.ai.e-infra.cz/v1
LLM_PROVIDER_EINFRA_API_KEY=your_einfra_key
LLM_PROVIDER_EINFRA_DEFAULT_MODEL=mini
LLM_PROVIDER_EINFRA_PUBLIC_MODELS=*
LLM_PROVIDER_EINFRA_DISCOVER_MODELS=true

RETRIEVAL_BACKEND=msearch
MSEARCH_USERNAME=your_username
MSEARCH_PASSWORD=your_password
```

## Discovery implementation and diagnostics

Model and collection discovery run at startup and in `_discovery_loop` in `app/main.py`. Forced provider fetching runs outside `_provider_state_lock`, because `/settings` takes that lock on every call. Keep `LLM_MODELS_CACHE_TTL_SECONDS` and `MSEARCH_COLLECTIONS_CACHE_TTL_SECONDS` longer than the refresh interval; they are request-side fallback TTLs. `/llm-providers/refresh` forces both lists immediately.

The browser's `LLM API` panel can override the LLM base URL and key for the session. If credentials appear inconsistent, check the key fingerprint in startup logs; never print the key. The project `.env` intentionally takes precedence over exported environment variables.

## Reasoning and context metadata

- Reasoning: declared per model in `data/models.json` (request field, effort vocabulary, default, `mandatory`, human-only `note`), and discovered from the provider's own catalogue where one publishes it — only OpenRouter's `/api/v1/models` does, so only OpenRouter is asked (`LLM_PROVIDER_<ID>_DISCOVER_CATALOG` overrides). A hand-written entry beats discovery, because it is where a probe of what the model actually did gets recorded. Nothing is sent for a model neither declares. An empty/absent `efforts` list with `mandatory: true` is the "reasons anyway, cannot be steered" case: no control is offered, no parameter is sent, the trace is still shown collapsed. `mandatory` and a `none`/`off` effort contradict each other and the loader strips the switch — gpt-oss-120b shipped both and 400ed on every answer. Add models to the JSON, never to code.
- The effort sent when nobody touches the selector is derived, not declared: `mandatory` → the cheapest level the model accepts, optional → nothing at all (`ReasoningSupport.effective_default`). Lowering a mandatory model changes only how much it thinks; sending a level to an optional one changes whether it thinks, which would silently alter answers for users who never asked. Declare `default` only to overrule that, as the four steerable mandatory GPT-OSS routes now do with `medium`. `mistral-medium-3.5` is why the derivation is not a blanket "low": it accepts only `none`/`high`.
- Context windows come from two places. e-infra publishes `model_info.context_size` at `/model/info`; OpenRouter publishes `context_length` in the same `/models` records as its reasoning metadata, so both are read in one request. A discovered length is clamped to the provider's `context_window` in `data/models.json` (raise `max_context_window` there to lift it) — it is a capacity, not a budget, and a 1M-token window reaching the browser as the working window turns trimming off. The clamp means discovery can only ever say a model is *smaller* than the provider default assumed, which is the case that was over-packing.
- Recorded probes found that the AI Ufal Open WebUI gateway **dropped** `reasoning_effort` and `reasoning` on every endpoint (`/api`, `/api/v1`, `/openai`) — probed 2026-08-22 and again 2026-08-23, when ten parameter forms including `reasoning_effort: "bogus"` all returned 200 with a byte-identical trace. Accordingly, the AI Ufal model metadata declares no effort controls. Re-probe if the gateway is upgraded. OpenRouter and e-infra both honour the parameter; e-infra rejects a level its model does not take with a 400, so its vocabularies are probed per model.
