"""Single source of truth for WP (work package) configuration.

Each WP groups a set of built-in (read-only) prompts, the mSearch collections
it may search, its own length definitions, and optional placeholder
definitions. Shared and local prompt presets reference a WP through `wp_id`,
so the UI can later show only the prompts and collections relevant to the
selected WP.

This is intentionally a Python module rather than a JSON/YAML file: the prompt
bodies are long multi-line Czech text that is far easier to read, edit, and
unit-test as source than as escaped strings, and it matches how ``prompts.py``
already holds prompt text.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from app.rag.prompts import (
    LENGTH_PROMPTS,
    STYLE_PROMPTS,
    default_system_prompt_template,
    default_user_prompt_template,
)


@dataclass(frozen=True)
class BuiltInPrompt:
    """A read-only prompt shipped with a WP.

    The body uses the same finalized preset shape as saved presets: a full
    ``system_prompt`` (style is already baked in, ``{length}`` stays as the one
    orthogonal placeholder) and a ``user_prompt_template``.
    """

    id: str
    name: str
    system_prompt: str
    user_prompt_template: str
    length_prompts: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class WPCollection:
    """A document collection a WP may search, mapped to an mSearch collection."""

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
    length_prompts: dict[str, str]
    placeholders: dict[str, str] = field(default_factory=dict)


def _wp1_prompt(style_key: str) -> str:
    # WP1 keeps the existing history behavior: take the generic system prompt
    # template and bake the chosen style guidance in, leaving `{length}` for
    # chat-time rendering.
    return default_system_prompt_template().replace("{style}", STYLE_PROMPTS[style_key])


def _generic_prompt(domain: str) -> str:
    return f"""
Jsi pečlivý asistent pro RAG systém v oblasti: {domain}.

Úkol:
- Odpověz ve stejném jazyce jako otázka; pro české otázky odpovídej česky.
- Nejdřív posuď relevanci dodaného kontextu vůči otázce.
- Používej jen pasáže, které otázku skutečně podporují; slabé, okrajové nebo zavádějící pasáže vynech.
- Tvrzení převzatá ze zdrojů cituj markdownovými poznámkami pod čarou ve tvaru [^Z1], [^Z2] atd.
- Nepředstírej, že nepodložené tvrzení pochází ze zdrojů.
- Pokud relevantní kontext nestačí, řekni to jasně a odpověz opatrně z obecné znalosti.
- Nevymýšlej bibliografické údaje ani citace.

Délka: {{length}}

Forma odpovědi:
- Piš v Markdownu.
- Zvol přirozenou strukturu podle otázky.
- Zmiňuj pouze zdroje, které v odpovědi skutečně používáš.
- Nevytvářej na konci samostatný seznam "Použité zdroje"; přehled zdrojů vytvoří rozhraní samo.
- Odpověz přímo a přirozeně, bez závěrečných nabídek typu "Pokud chceš...".
""".strip()


WP_CONFIGS: list[WPConfig] = [
    WPConfig(
        id="WP1-historie",
        label="WP1 – Historie",
        description="Historický avatar: české dějiny a historicko-vzdělávací obsah.",
        builtin_prompts=[
            BuiltInPrompt(
                id="wp1-ucitel",
                name="Učitel",
                system_prompt=_wp1_prompt("ucitel"),
                user_prompt_template=default_user_prompt_template(),
            ),
            BuiltInPrompt(
                id="wp1-historik",
                name="Historik",
                system_prompt=_wp1_prompt("historik"),
                user_prompt_template=default_user_prompt_template(),
            ),
            BuiltInPrompt(
                id="wp1-laik",
                name="Laik",
                system_prompt=_wp1_prompt("laik"),
                user_prompt_template=default_user_prompt_template(),
            ),
        ],
        default_prompt_id="wp1-ucitel",
        collections=[
            WPCollection(
                id="wp1-histoedu",
                label="WP1: histoedu",
                msearch_collection_id="64d6f521-5044-4b02-8658-380b639801af",
            ),
        ],
        default_collection_id="wp1-histoedu",
        length_prompts=dict(LENGTH_PROMPTS),
    ),
    WPConfig(
        id="WP2-média",
        label="WP2 – Média",
        description="Mediální avatar.",
        builtin_prompts=[
            BuiltInPrompt(
                id="wp2-vychozi",
                name="Výchozí",
                system_prompt=_generic_prompt("média a mediální studia"),
                user_prompt_template=default_user_prompt_template(),
            ),
        ],
        default_prompt_id="wp2-vychozi",
        collections=[
            WPCollection(
                id="wp2-zaplavy",
                label="WP2: zaplavy",
                msearch_collection_id="35a4a85e-4d6e-42a3-a3ff-e1f151ffbd09",
            ),
        ],
        default_collection_id="wp2-zaplavy",
        length_prompts=dict(LENGTH_PROMPTS),
    ),
    WPConfig(
        id="WP3-právo",
        label="WP3 – Právo",
        description="Právní avatar.",
        builtin_prompts=[
            BuiltInPrompt(
                id="wp3-vychozi",
                name="Výchozí",
                system_prompt=_generic_prompt("právo"),
                user_prompt_template=default_user_prompt_template(),
            ),
        ],
        default_prompt_id="wp3-vychozi",
        collections=[
            WPCollection(
                id="wp3-law",
                label="WP3: law",
                msearch_collection_id="d4be44d5-689c-4bbe-a372-b959929cd511",
            ),
        ],
        default_collection_id="wp3-law",
        length_prompts=dict(LENGTH_PROMPTS),
    ),
    WPConfig(
        id="WP4-adiktologie",
        label="WP4 – Adiktologie",
        description="Adiktologický avatar.",
        builtin_prompts=[
            BuiltInPrompt(
                id="wp4-vychozi",
                name="Výchozí",
                system_prompt=_generic_prompt("adiktologie"),
                user_prompt_template=default_user_prompt_template(),
            ),
        ],
        default_prompt_id="wp4-vychozi",
        collections=[
            WPCollection(
                id="wp4-default",
                label="WP4",
                msearch_collection_id="3429956e-8a21-4502-ad21-a41fddc5ef99",
            ),
        ],
        default_collection_id="wp4-default",
        length_prompts=dict(LENGTH_PROMPTS),
    ),
]


def load_wp_configs() -> list[WPConfig]:
    return list(WP_CONFIGS)


def get_wp_config(wp_id: str) -> WPConfig | None:
    return next((wp for wp in WP_CONFIGS if wp.id == wp_id), None)


def default_wp_id() -> str:
    return WP_CONFIGS[0].id


def is_valid_wp_id(wp_id: str) -> bool:
    return get_wp_config(wp_id) is not None


def resolve_wp_id(wp_id: str | None) -> str:
    """Return a valid WP id, falling back to the default for unknown/empty ids."""

    candidate = (wp_id or "").strip()
    return candidate if is_valid_wp_id(candidate) else default_wp_id()


def wp_public_payload() -> list[dict[str, Any]]:
    """Serialize WP configs for the API (and the future WP selector)."""

    return [asdict(wp) for wp in WP_CONFIGS]
