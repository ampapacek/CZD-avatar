"""Single source of truth for WP (work package) configuration.

Each WP groups a set of built-in (read-only) prompts, the mSearch collections
it may search, and optional placeholder definitions. Shared and local prompt
presets reference a WP through `wp_id`,
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
    PlaceholderDef,
    default_system_prompt_template,
    default_user_prompt_template,
)


# WP1 persona guidance, baked into each WP1 built-in system prompt. These were
# the old global persona-style texts; they now live as WP1 content (the
# persona axis is gone — a persona is just which prompt you picked).
_WP1_PERSONA_PROMPTS = {
    "laik": """
Piš srozumitelně pro běžného čtenáře bez odborného žargonu. Relevantní dodaný kontext používej jako hlavní oporu, ale můžeš doplnit obecné znalosti, pokud odpovědi pomohou. Citace nevyžaduj u každé věty; použij je jen tehdy, když se přímo opíráš o konkrétní nalezený zdroj. Pokud kontext nestačí nebo je mimo téma, řekni to jednoduše, nevnucuj citace a odpověz opatrně z obecné znalosti. Nejistotu pojmenuj přirozeně a nevymýšlej zdroje ani bibliografické údaje.
""".strip(),
    "ucitel": """
Piš didakticky, jako učitel, který chce látku dobře vysvětlit. Začni od relevantního dodaného kontextu a tvrzení převzatá ze zdrojů cituj markdownovými poznámkami pod čarou ve tvaru [^Z1], [^Z2] atd. Obecné znalosti můžeš použít pro vysvětlení souvislostí, příkladů a důsledků, ale nesmíš předstírat, že pocházejí z nalezených dokumentů. Pokud jsou zdroje slabé, okrajové nebo nepokrývají otázku, řekni to a odděl podložené informace od obecného vysvětlení. Nejistotu formuluj jasně, bez falešné přesnosti a bez vymyšlených citací.
""".strip(),
    "historik": """
Piš přesně, formálně a opatrně. Primárně vycházej z relevantních nalezených zdrojů; každé podstatné tvrzení, které lze opřít o kontext, opatři poznámkou pod čarou ve tvaru [^Z1], [^Z2] atd. Cituj pouze zdroje, které skutečně podporují dané tvrzení, a vynech pasáže, které jsou jen slovně podobné nebo zavádějící. Obecné znalosti používej střídmě; pokud nejsou doložené dodaným kontextem, uveď to přirozeně a označ míru nejistoty. Nevymýšlej autory, editory, bibliografické údaje ani zdrojovou oporu.
""".strip(),
}

@dataclass(frozen=True)
class BuiltInPrompt:
    """A read-only prompt shipped with a WP.

    The body uses the same finalized preset shape as saved presets: a full
    ``system_prompt`` (style is already baked in, ``{length}`` stays as the one
    orthogonal placeholder) and a ``user_prompt_template``. An optional inline
    ``placeholders`` map overrides global placeholder defs wholesale (highest
    precedence in resolution).
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
    of all mSearch collections for the WP replaces them (see
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
    placeholders: dict[str, PlaceholderDef] = field(default_factory=dict)
    # When true, every collection in this WP is only retrievable through the AI
    # Ufal provider. The backend policy and the frontend selector both read this
    # flag, so the restriction lives in one place (the WP, not per-collection ids
    # that change as new collection versions are published).
    requires_aiufal: bool = False


def _wp1_prompt(persona_key: str) -> str:
    # WP1 keeps the existing history behavior: take the generic system prompt
    # template and bake the chosen persona guidance in, leaving `{length}` for
    # chat-time rendering.
    return f"{default_system_prompt_template()}\n\nStyl:\n{_WP1_PERSONA_PROMPTS[persona_key]}"


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
                label="wp1-histoedu-v2026-02",
                msearch_collection_id="64d6f521-5044-4b02-8658-380b639801af",
            ),
        ],
        default_collection_id="wp1-histoedu",
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
                label="wp2-zaplavy-v2026-6",
                msearch_collection_id="ab79b4f6-6a91-45a3-908e-edb2c771d3b0",
            ),
        ],
        default_collection_id="wp2-zaplavy",
        requires_aiufal=True,
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
                label="wp3-law-v2026-02",
                msearch_collection_id="d4be44d5-689c-4bbe-a372-b959929cd511",
            ),
        ],
        default_collection_id="wp3-law",
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
                label="wp4-v2026-03",
                msearch_collection_id="3429956e-8a21-4502-ad21-a41fddc5ef99",
            ),
        ],
        default_collection_id="wp4-default",
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


def wp_collection_prefix(wp_id: str) -> str:
    """The ``wp1``..``wp4`` token that mSearch collection names start with.

    mSearch collection names are ``wp1-histoedu-...``, ``wp2-zaplavy-...`` etc.;
    the WP ids are ``WP1-historie`` etc. Both share the same leading token, which
    is how the live collection list is grouped back onto a WP.
    """

    return (wp_id or "").split("-", 1)[0].strip().lower()


def wp_requires_aiufal(wp_id: str | None) -> bool:
    wp = get_wp_config((wp_id or "").strip())
    return bool(wp and wp.requires_aiufal)


def gated_wp_collection_prefixes() -> set[str]:
    """Collection-name prefixes (``wp2`` etc.) whose WP is AI-Ufal-only."""

    return {wp_collection_prefix(wp.id) for wp in WP_CONFIGS if wp.requires_aiufal}


def gated_msearch_collection_ids() -> set[str]:
    """Static fallback mSearch collection ids that are AI-Ufal-only.

    Live enforcement also folds in the current mSearch collections for the gated
    WP prefixes; this static set keeps the known ids gated even when the live list
    is unavailable.
    """

    return {
        collection.msearch_collection_id
        for wp in WP_CONFIGS
        if wp.requires_aiufal
        for collection in wp.collections
    }
