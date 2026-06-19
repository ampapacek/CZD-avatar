from __future__ import annotations

import string
from dataclasses import dataclass, field
from datetime import date
from typing import Any


# System placeholders are filled automatically by the server and are never
# surfaced as user-facing controls. ``{question}`` and ``{retrieved_snippets}`` are filled
# from request data; ``{current_date}`` is the server-local date.
SYSTEM_PLACEHOLDERS = frozenset({"question", "retrieved_snippets", "current_date"})


@dataclass(frozen=True)
class OptionDef:
    name: str  # internal/stored value (e.g. "short")
    label: str  # display in the dropdown (e.g. "Krátká")
    text: str  # substituted into the template


@dataclass(frozen=True)
class PlaceholderDef:
    label: str
    kind: str = "text"  # "select" | "text"
    help: str | None = None
    default: str = ""  # text default / select default option name
    options: list[OptionDef] = field(default_factory=list)  # select only


def resolve_placeholder_defs(
    names: set[str],
    *,
    inline_defs: dict[str, PlaceholderDef] | None = None,
    local_global_defs: dict[str, PlaceholderDef] | None = None,
    shared_global_defs: dict[str, PlaceholderDef] | None = None,
    code_default_defs: dict[str, PlaceholderDef] | None = None,
) -> dict[str, PlaceholderDef]:
    """Pick each placeholder def wholesale from the most specific source.

    Precedence per name: prompt-inline -> browser-local global -> shared server
    global -> built-in code default (``DEFAULT_PLACEHOLDERS``). Options are never
    merged across sources; a name is taken entirely from the first source that
    declares it. Names not declared anywhere (and not system placeholders) are
    simply absent from the result and render literally.
    """

    inline = inline_defs or {}
    local = local_global_defs or {}
    shared = shared_global_defs or {}
    code = code_default_defs or {}
    resolved: dict[str, PlaceholderDef] = {}
    for name in names:
        if name in SYSTEM_PLACEHOLDERS:
            continue
        if name in inline:
            resolved[name] = inline[name]
        elif name in local:
            resolved[name] = local[name]
        elif name in shared:
            resolved[name] = shared[name]
        elif name in code:
            resolved[name] = code[name]
    return resolved


def substitute_value(definition: PlaceholderDef, selection: str | None) -> str:
    """Compute the substituted string for a single resolved placeholder def."""

    if definition.kind == "select":
        chosen = selection if selection is not None else definition.default
        for option in definition.options:
            if option.name == chosen:
                return option.text
        # Fall back to the default option's text if the selection is unknown.
        for option in definition.options:
            if option.name == definition.default:
                return option.text
        return ""
    # "text" (and any unknown kind treated as free text)
    value = (selection or "").strip()
    return value if value else definition.default


def default_system_prompt_template() -> str:
    return """
Jsi pečlivý asistent pro RAG systém.

Úkol:
- Odpověz ve stejném jazyce jako otázka; pro české otázky odpovídej česky.
- Nejdřív posuď relevanci dodaného kontextu vůči otázce.
- Používej jen pasáže, které otázku skutečně podporují; slabé, okrajové nebo zavádějící pasáže vynech.
- Nepředstírej, že nepodložené tvrzení pochází ze zdrojů.
- Pokud relevantní kontext nestačí, řekni to jasně a odpověz opatrně z obecné znalosti.
- Nevymýšlej bibliografické údaje ani citace.

Délka: {length}

Forma odpovědi:
- Piš v Markdownu.
- Zvol přirozenou strukturu podle otázky.
- Pokud cituješ nalezený kontext, používej značky uvedené v kontextu jako markdownové poznámky pod čarou ve tvaru [^Z1], [^Z2] atd. Pokud jedno tvrzení opíráš o více zdrojů, piš každou poznámku zvlášť bez mezer, např. [^Z1][^Z5]; neslučuj více ID do jedné poznámky jako [^Z1, ^Z5] nebo [^Z1, Z5].
- Zmiňuj pouze zdroje, které v odpovědi skutečně používáš.
- Nevytvářej na konci samostatný seznam "Použité zdroje" ani jiný vlastní závěrečný seznam zdrojů. Přehled zdrojů vytvoří rozhraní samo.
- Neuzavírej odpověď nabídkami typu "Pokud chceš..." nebo podobnými dodatky. Odpověz přímo a přirozeně.
""".strip()


def default_user_prompt_template() -> str:
    return """
Otázka:
{question}

Vlastní instrukce uživatele (může být prázdné):
{custom_instructions}

Nalezený kontext:
{retrieved_snippets}
""".strip()


def build_messages(
    question: str,
    retrieved_chunks: list[dict[str, Any]],
    placeholder_defs: dict[str, PlaceholderDef] | None = None,
    selections: dict[str, str] | None = None,
    conversation_history: list[dict[str, str]] | None = None,
    system_prompt: str | None = None,
    user_prompt_template: str | None = None,
    context_text: str | None = None,
) -> list[dict[str, str]]:
    context = format_context(retrieved_chunks) if context_text is None else context_text
    context_for_prompt = context if context else "Nebyly nalezeny žádné relevantní pasáže."
    system_template = (system_prompt or "").strip() or default_system_prompt_template()
    user_template = (user_prompt_template or "").strip() or default_user_prompt_template()

    system_values = {"retrieved_snippets": context_for_prompt}
    user_values = {"question": question, "retrieved_snippets": context_for_prompt}

    system = _render_prompt_template(
        system_template,
        placeholder_defs or {},
        selections or {},
        system_values,
    )
    user = _render_prompt_template(
        user_template,
        placeholder_defs or {},
        selections or {},
        user_values,
    )

    messages: list[dict[str, str]] = [{"role": "system", "content": system}]
    for turn in (conversation_history or [])[-8:]:
        role = turn.get("role")
        content = (turn.get("content") or "").strip()
        if role not in {"user", "assistant"} or not content:
            continue
        messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": user})
    return messages


class _UnknownPlaceholder(str):
    def __new__(cls, key: str) -> "_UnknownPlaceholder":
        value = super().__new__(cls, f"{{{key}}}")
        value.key = key
        return value

    def __format__(self, format_spec: str) -> str:
        if not format_spec:
            return str(self)
        return f"{{{self.key}:{format_spec}}}"


class _PromptTemplateValues(dict):
    def __missing__(self, key: str) -> _UnknownPlaceholder:
        # An undeclared placeholder (a token with no def anywhere and not a
        # system placeholder) renders literally; it is never an error.
        return _UnknownPlaceholder(key)


def _render_prompt_template(
    template: str,
    placeholder_defs: dict[str, PlaceholderDef],
    selections: dict[str, str],
    system_values: dict[str, str],
) -> str:
    values: dict[str, str] = {"current_date": date.today().isoformat()}
    values.update(system_values)
    for name, definition in placeholder_defs.items():
        values[name] = substitute_value(definition, selections.get(name))
    try:
        formatter = string.Formatter()
        return formatter.vformat(template, (), _PromptTemplateValues(values)).strip()
    except (IndexError, ValueError):
        return template.strip()


def template_placeholder_names(template: str) -> set[str]:
    """Return the set of ``{name}`` tokens referenced by a template."""

    names: set[str] = set()
    formatter = string.Formatter()
    try:
        for _literal, field_name, _format_spec, _conversion in formatter.parse(template):
            if field_name:
                names.add(field_name.split(".")[0].split("[")[0])
    except (IndexError, ValueError):
        return names
    return names


def format_context(chunks: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for index, chunk in enumerate(chunks, start=1):
        citation_id = chunk.get("citation_id") or f"Z{index}"
        metadata = chunk.get("metadata", {})
        title = metadata.get("title") or "Neznámý dokument"
        source_path = metadata.get("source_path") or ""
        source_name = metadata.get("source_name")
        source_citation = metadata.get("source_citation")
        page = metadata.get("page_number")
        page_label = f", str. {page}" if page else ""
        header_parts = [f"[{citation_id}] {title}{page_label} ({source_path})"]
        if source_name:
            header_parts.append(f"Zdroj: {source_name}")
        if source_citation:
            header_parts.append(f"Citace zdroje: {source_citation}")
        lines.append(" | ".join(header_parts))
        lines.append(chunk.get("text", "").strip())
        lines.append("")
    return "\n".join(lines).strip()
