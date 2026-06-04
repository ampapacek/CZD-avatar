from __future__ import annotations

from typing import Any


STYLE_PROMPTS = {
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


LENGTH_PROMPTS = {
    "short": "Odpověz stručně, přibližně 1-2 odstavce.",
    "medium": "Odpověz středně dlouze, přibližně 3-5 kratších odstavců nebo několik přehledných bodů.",
    "long": "Odpověz podrobněji, ale stále přehledně. Uveď hlavní nuance, pokud je podporuje kontext.",
}


def available_styles() -> list[str]:
    return list(STYLE_PROMPTS)


def available_lengths() -> list[str]:
    return list(LENGTH_PROMPTS)


def default_system_prompt_template() -> str:
    return """
Jsi pečlivý asistent pro RAG systém.

Úkol:
- Odpověz ve stejném jazyce jako otázka; pro české otázky odpovídej česky.
- Nejdřív posuď relevanci dodaného kontextu vůči otázce.
- Používej jen pasáže, které otázku skutečně podporují; slabé, okrajové nebo zavádějící pasáže vynech.
- Nepředstírej, že nepodložené tvrzení pochází ze zdrojů.
- Pokud relevantní kontext nestačí, řekni to jasně a postupuj podle zvoleného profilu.
- Nevymýšlej bibliografické údaje ani citace.

Styl: {style}
Délka: {length}

Forma odpovědi:
- Piš v Markdownu.
- Zvol přirozenou strukturu podle otázky.
- Pokud cituješ nalezený kontext, používej značky uvedené v kontextu jako markdownové poznámky pod čarou ve tvaru [^Z1], [^Z2] atd.
- Zmiňuj pouze zdroje, které v odpovědi skutečně používáš.
- Nevytvářej na konci samostatný seznam "Použité zdroje" ani jiný vlastní závěrečný seznam zdrojů. Přehled zdrojů vytvoří rozhraní samo.
- Neuzavírej odpověď nabídkami typu "Pokud chceš..." nebo podobnými dodatky. Odpověz přímo a přirozeně.
""".strip()


def default_system_prompt(style: str, length: str) -> str:
    return _render_system_prompt_template(default_system_prompt_template(), style=style, length=length)


def default_user_prompt_template() -> str:
    return """
Otázka:
{question}

Vlastní instrukce uživatele:
{custom_instructions}

Nalezený kontext:
{context}
""".strip()


def build_messages(
    question: str,
    retrieved_chunks: list[dict[str, Any]],
    style: str,
    length: str,
    custom_instructions: str | None = None,
    conversation_history: list[dict[str, str]] | None = None,
    system_prompt: str | None = None,
    user_prompt_template: str | None = None,
    style_prompts: dict[str, str] | None = None,
    length_prompts: dict[str, str] | None = None,
    context_text: str | None = None,
) -> list[dict[str, str]]:
    context = format_context(retrieved_chunks) if context_text is None else context_text
    context_for_prompt = context if context else "Nebyly nalezeny žádné relevantní pasáže."
    custom = custom_instructions.strip() if custom_instructions else "Žádné."
    system_template = (system_prompt or "").strip() or default_system_prompt_template()
    system = _render_system_prompt_template(
        system_template,
        style=style,
        length=length,
        style_prompts=style_prompts,
        length_prompts=length_prompts,
    )
    template = (user_prompt_template or "").strip() or default_user_prompt_template()
    user = _render_user_prompt_template(
        template,
        question=question,
        context=context_for_prompt,
        custom_instructions=custom,
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


def _render_system_prompt_template(
    template: str,
    style: str,
    length: str,
    style_prompts: dict[str, str] | None = None,
    length_prompts: dict[str, str] | None = None,
) -> str:
    resolved_style_prompts = {**STYLE_PROMPTS, **(style_prompts or {})}
    resolved_length_prompts = {**LENGTH_PROMPTS, **(length_prompts or {})}
    try:
        return template.format(
            style=resolved_style_prompts[style],
            length=resolved_length_prompts[length],
            style_key=style,
            length_key=length,
        ).strip()
    except (KeyError, ValueError):
        return template.strip()


def _render_user_prompt_template(template: str, question: str, context: str, custom_instructions: str) -> str:
    try:
        return template.format(
            question=question,
            context=context,
            custom_instructions=custom_instructions,
        ).strip()
    except (KeyError, ValueError):
        return template.strip()


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
