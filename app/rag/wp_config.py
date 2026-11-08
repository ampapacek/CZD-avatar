"""WP (work package) configuration, loaded from the instance config file.

The code knows no specific WP. Each server points ``INSTANCE_CONFIG_PATH`` at a
TOML file that lists its WPs: their built-in (read-only) prompts, the mSearch
collections they search, their prepared questions and an optional provider
restriction. What the file defines is what the server offers.
``instance.example.toml`` in the repo root documents every field.

Shared and local prompt presets reference a WP through ``wp_id``.
"""

from __future__ import annotations

import tomllib
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from app.rag.prompts import OptionDef, PlaceholderDef


INSTANCE_CONFIG_HELP = (
    "Set INSTANCE_CONFIG_PATH in .env to this server's instance config file "
    "(for example data/instances/<server>.toml). Start from instance.example.toml "
    "in the repo root; it documents every field."
)


class InstanceConfigError(ValueError):
    """The instance config file is missing or invalid."""


@dataclass(frozen=True)
class BuiltInPrompt:
    """A read-only prompt shipped with a WP.

    The body uses the same finalized preset shape as saved presets: a full
    ``system_prompt`` (``{length}`` stays as the one orthogonal placeholder) and
    a ``user_prompt_template``. An optional inline ``placeholders`` map overrides
    global placeholder defs wholesale (highest precedence in resolution).
    """

    id: str
    name: str
    system_prompt: str
    user_prompt_template: str
    placeholders: dict[str, PlaceholderDef] = field(default_factory=dict)


@dataclass(frozen=True)
class WPCollection:
    """A document collection a WP may search, mapped to an mSearch collection.

    These are the offline fallback / default selection; at runtime the live list
    of all mSearch collections whose name starts with the WP's
    ``collection_prefix`` replaces them (see
    ``MSearchRetriever.live_collections_by_prefix``).
    """

    id: str
    label: str
    msearch_collection_id: str


@dataclass(frozen=True)
class WPConfig:
    id: str
    label: str
    description: str
    builtin_prompts: list[BuiltInPrompt]
    default_prompt_id: str
    collections: list[WPCollection]
    default_collection_id: str
    # Live mSearch collections named ``<collection_prefix>-...`` belong to this WP.
    collection_prefix: str = ""
    questions: list[str] = field(default_factory=list)
    local_retrieval_enabled: bool = False
    placeholders: dict[str, PlaceholderDef] = field(default_factory=dict)
    # None: any provider. Otherwise the ids of the only LLM providers that may
    # receive this WP's collection content. Backend policy and the frontend
    # collection selector both read it.
    allowed_providers: list[str] | None = None


@dataclass(frozen=True)
class InstanceConfig:
    wps: list[WPConfig]
    # Whether the shared presets from PROMPT_PRESETS_PATH are offered.
    shared_presets: bool = True
    source: str = ""


# --- loading and validation -------------------------------------------------

_TOP_KEYS = {"shared_presets", "wps"}
_WP_KEYS = {
    "id",
    "label",
    "description",
    "collection_prefix",
    "default_prompt",
    "default_collection",
    "allowed_providers",
    "local_retrieval",
    "questions",
    "placeholders",
    "collections",
    "prompts",
}
_COLLECTION_KEYS = {"id", "label", "msearch_collection_id"}
_PROMPT_KEYS = {"id", "name", "system_prompt", "user_prompt_template", "placeholders"}
_PLACEHOLDER_KEYS = {"label", "kind", "help", "default", "options"}
_OPTION_KEYS = {"name", "label", "text"}


def load_instance_config(path: str | Path | None) -> InstanceConfig:
    """Read and validate an instance config file; raise InstanceConfigError."""

    if path is None or str(path).strip() in {"", "."}:
        raise InstanceConfigError(f"No instance config is set. {INSTANCE_CONFIG_HELP}")
    file = Path(path)
    if not file.is_file():
        raise InstanceConfigError(f"Instance config {file} was not found. {INSTANCE_CONFIG_HELP}")
    try:
        data = tomllib.loads(file.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, tomllib.TOMLDecodeError) as exc:
        raise InstanceConfigError(f"Instance config {file} could not be read: {exc}") from exc
    try:
        return parse_instance_config(data, source=str(file))
    except InstanceConfigError as exc:
        raise InstanceConfigError(f"Instance config {file}: {exc}") from exc


def parse_instance_config(data: dict[str, Any], source: str = "") -> InstanceConfig:
    _check_keys(data, _TOP_KEYS, "top level")
    shared_presets = data.get("shared_presets", True)
    if not isinstance(shared_presets, bool):
        raise InstanceConfigError("shared_presets must be true or false.")
    raw_wps = data.get("wps")
    if not isinstance(raw_wps, list) or not raw_wps:
        raise InstanceConfigError("define at least one [[wps]] table.")
    wps = [_parse_wp(raw, index) for index, raw in enumerate(raw_wps)]
    _check_unique([wp.id for wp in wps], "WP id")
    _check_unique([wp.collection_prefix for wp in wps if wp.collection_prefix], "collection_prefix")
    _check_unique([prompt.id for wp in wps for prompt in wp.builtin_prompts], "prompt id")
    return InstanceConfig(wps=wps, shared_presets=shared_presets, source=source)


def _parse_wp(raw: Any, index: int) -> WPConfig:
    where = f"wps[{index}]"
    if not isinstance(raw, dict):
        raise InstanceConfigError(f"{where} must be a table.")
    wp_id = _required_str(raw, "id", where)
    where = f"WP {wp_id}"
    _check_keys(raw, _WP_KEYS, where)
    prompts = [_parse_prompt(item, f"{where} prompts[{i}]") for i, item in enumerate(_table_list(raw, "prompts", where))]
    if not prompts:
        raise InstanceConfigError(f"{where} needs at least one [[wps.prompts]].")
    collections = [
        _parse_collection(item, f"{where} collections[{i}]")
        for i, item in enumerate(_table_list(raw, "collections", where))
    ]
    if not collections:
        raise InstanceConfigError(f"{where} needs at least one [[wps.collections]].")
    _check_unique([collection.id for collection in collections], f"{where} collection id")
    default_prompt = _optional_str(raw, "default_prompt", where) or prompts[0].id
    if default_prompt not in {prompt.id for prompt in prompts}:
        raise InstanceConfigError(f"{where} default_prompt '{default_prompt}' is not one of its prompts.")
    default_collection = _optional_str(raw, "default_collection", where) or collections[0].id
    if default_collection not in {collection.id for collection in collections}:
        raise InstanceConfigError(f"{where} default_collection '{default_collection}' is not one of its collections.")
    questions = raw.get("questions", [])
    if not isinstance(questions, list) or not all(isinstance(item, str) for item in questions):
        raise InstanceConfigError(f"{where} questions must be a list of strings.")
    allowed = raw.get("allowed_providers")
    if allowed is not None:
        if not isinstance(allowed, list) or not allowed or not all(isinstance(item, str) and item.strip() for item in allowed):
            raise InstanceConfigError(f"{where} allowed_providers must be a non-empty list of provider ids.")
        allowed = [item.strip().lower() for item in allowed]
    collection_prefix = _optional_str(raw, "collection_prefix", where).lower()
    if "-" in collection_prefix:
        raise InstanceConfigError(f"{where} collection_prefix must not contain '-' (it is the part before the first '-').")
    local_retrieval = raw.get("local_retrieval", False)
    if not isinstance(local_retrieval, bool):
        raise InstanceConfigError(f"{where} local_retrieval must be true or false.")
    return WPConfig(
        id=wp_id,
        label=_optional_str(raw, "label", where) or wp_id,
        description=_optional_str(raw, "description", where),
        builtin_prompts=prompts,
        default_prompt_id=default_prompt,
        collections=collections,
        default_collection_id=default_collection,
        collection_prefix=collection_prefix,
        questions=[item.strip() for item in questions if item.strip()],
        local_retrieval_enabled=local_retrieval,
        placeholders=_parse_placeholders(raw.get("placeholders"), where),
        allowed_providers=allowed,
    )


def _parse_prompt(raw: Any, where: str) -> BuiltInPrompt:
    if not isinstance(raw, dict):
        raise InstanceConfigError(f"{where} must be a table.")
    _check_keys(raw, _PROMPT_KEYS, where)
    prompt_id = _required_str(raw, "id", where)
    where = f"{where} ({prompt_id})"
    return BuiltInPrompt(
        id=prompt_id,
        name=_required_str(raw, "name", where),
        # Kept verbatim: no stripping, the text is what the model gets.
        system_prompt=_required_text(raw, "system_prompt", where),
        user_prompt_template=_required_text(raw, "user_prompt_template", where),
        placeholders=_parse_placeholders(raw.get("placeholders"), where),
    )


def _parse_collection(raw: Any, where: str) -> WPCollection:
    if not isinstance(raw, dict):
        raise InstanceConfigError(f"{where} must be a table.")
    _check_keys(raw, _COLLECTION_KEYS, where)
    collection_id = _required_str(raw, "id", where)
    return WPCollection(
        id=collection_id,
        label=_optional_str(raw, "label", where) or collection_id,
        msearch_collection_id=_required_str(raw, "msearch_collection_id", where),
    )


def _parse_placeholders(raw: Any, where: str) -> dict[str, PlaceholderDef]:
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise InstanceConfigError(f"{where} placeholders must be a table.")
    result: dict[str, PlaceholderDef] = {}
    for name, item in raw.items():
        item_where = f"{where} placeholder {name}"
        if not isinstance(item, dict):
            raise InstanceConfigError(f"{item_where} must be a table.")
        _check_keys(item, _PLACEHOLDER_KEYS, item_where)
        kind = _optional_str(item, "kind", item_where) or "text"
        if kind not in {"select", "text"}:
            raise InstanceConfigError(f"{item_where} kind must be 'select' or 'text'.")
        options: list[OptionDef] = []
        for i, option in enumerate(_table_list(item, "options", item_where)):
            option_where = f"{item_where} options[{i}]"
            if not isinstance(option, dict):
                raise InstanceConfigError(f"{option_where} must be a table.")
            _check_keys(option, _OPTION_KEYS, option_where)
            option_name = _required_str(option, "name", option_where)
            options.append(
                OptionDef(
                    name=option_name,
                    label=_optional_str(option, "label", option_where) or option_name,
                    text=_optional_text(option, "text", option_where),
                )
            )
        result[str(name)] = PlaceholderDef(
            label=_optional_str(item, "label", item_where) or str(name),
            kind=kind,
            help=_optional_str(item, "help", item_where) or None,
            default=_optional_text(item, "default", item_where),
            options=options if kind == "select" else [],
        )
    return result


def _check_keys(raw: dict[str, Any], allowed: set[str], where: str) -> None:
    unknown = sorted(set(raw) - allowed)
    if unknown:
        raise InstanceConfigError(f"{where}: unknown key(s) {', '.join(unknown)}.")


def _check_unique(values: list[str], what: str) -> None:
    seen: set[str] = set()
    for value in values:
        if value in seen:
            raise InstanceConfigError(f"duplicate {what} '{value}'.")
        seen.add(value)


def _table_list(raw: dict[str, Any], key: str, where: str) -> list[Any]:
    value = raw.get(key, [])
    if not isinstance(value, list):
        raise InstanceConfigError(f"{where} {key} must be a list of tables.")
    return value


def _required_str(raw: dict[str, Any], key: str, where: str) -> str:
    value = _optional_str(raw, key, where)
    if not value:
        raise InstanceConfigError(f"{where} needs a non-empty '{key}'.")
    return value


def _optional_str(raw: dict[str, Any], key: str, where: str) -> str:
    return _optional_text(raw, key, where).strip()


def _required_text(raw: dict[str, Any], key: str, where: str) -> str:
    value = _optional_text(raw, key, where)
    if not value.strip():
        raise InstanceConfigError(f"{where} needs a non-empty '{key}'.")
    return value


def _optional_text(raw: dict[str, Any], key: str, where: str) -> str:
    value = raw.get(key, "")
    if not isinstance(value, str):
        raise InstanceConfigError(f"{where} '{key}' must be a string.")
    return value


# --- the active instance ----------------------------------------------------

_instance: InstanceConfig | None = None


def set_instance_config(config: InstanceConfig | None) -> InstanceConfig | None:
    """Make ``config`` the active instance; return the previous one."""

    global _instance
    previous = _instance
    _instance = config
    return previous


def instance_config() -> InstanceConfig:
    if _instance is None:
        raise RuntimeError(f"The instance config has not been loaded. {INSTANCE_CONFIG_HELP}")
    return _instance


def load_wp_configs() -> list[WPConfig]:
    return list(instance_config().wps)


def get_wp_config(wp_id: str) -> WPConfig | None:
    return next((wp for wp in instance_config().wps if wp.id == wp_id), None)


def default_wp_id() -> str:
    return instance_config().wps[0].id


def is_valid_wp_id(wp_id: str) -> bool:
    return get_wp_config(wp_id) is not None


def resolve_wp_id(wp_id: str | None) -> str:
    """Return a valid WP id, falling back to the default for unknown/empty ids."""

    candidate = (wp_id or "").strip()
    return candidate if is_valid_wp_id(candidate) else default_wp_id()


def shared_presets_enabled() -> bool:
    return instance_config().shared_presets


def builtin_prompt_names() -> dict[str, str]:
    return {prompt.id: prompt.name for wp in instance_config().wps for prompt in wp.builtin_prompts}


def wp_public_payload() -> list[dict[str, Any]]:
    """Serialize WP configs for the API (``/settings``)."""

    return [asdict(wp) for wp in instance_config().wps]


def wp_collection_prefixes() -> set[str]:
    return {wp.collection_prefix for wp in instance_config().wps if wp.collection_prefix}


def wp_collection_prefix(wp_id: str | None) -> str:
    wp = get_wp_config((wp_id or "").strip())
    return wp.collection_prefix if wp else ""


def wp_allowed_providers(wp_id: str | None) -> list[str] | None:
    wp = get_wp_config((wp_id or "").strip())
    return wp.allowed_providers if wp else None


def restricted_collection_prefixes() -> dict[str, list[str]]:
    """Collection-name prefix -> allowed provider ids, for restricted WPs."""

    return {
        wp.collection_prefix: wp.allowed_providers
        for wp in instance_config().wps
        if wp.allowed_providers is not None and wp.collection_prefix
    }


def restricted_msearch_collection_ids() -> dict[str, list[str]]:
    """Static fallback mSearch collection id -> allowed provider ids.

    Live enforcement also folds in the current mSearch collections under the
    restricted WPs' prefixes; this keeps the configured ids restricted even when
    the live list is unavailable.
    """

    return {
        collection.msearch_collection_id: wp.allowed_providers
        for wp in instance_config().wps
        if wp.allowed_providers is not None
        for collection in wp.collections
    }
