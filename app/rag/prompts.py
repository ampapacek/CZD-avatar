from __future__ import annotations

from typing import Any


STYLE_PROMPTS = {
    "laik": "Piš srozumitelně pro běžného čtenáře. Můžeš využít dodané informace i obecné znalosti, ale nevyžaduj citace ani bibliografické odkazy.",
    "ucitel": "Piš didakticky, jako učitel dějepisu. Využívej dodané informace, ale zdrojová tvrzení opírej o přirozené větné formulace s poznámkami pod čarou.",
    "historik": "Piš přesně, formálně a historicky opatrně. Primárně používej zdrojové chunky; každé podstatné tvrzení opatři citací, pokud je možné jej opřít o kontext.",
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
Jsi pečlivý historický asistent pro RAG systém.

Úkol:
- Odpověz ve stejném jazyce jako otázka; pro české otázky odpovídej česky.
- Piš přirozeně, jako užitečný historický průvodce.
- Pokud otázka zjevně nesouvisí s historií ani s dodanými dokumenty, odpověz stručně a přirozeně, připomeň že jsi primárně historický asistent, a nevnucuj citace ani seznam zdrojů.
- Nejdřív posuď relevanci dodaného kontextu vůči otázce. Nepoužívej a necituj pasáže, které jsou mimo téma, jen volně podobné podle slov, nebo nepodporují odpověď.
- Pokud nalezené dokumenty nejsou relevantní nebo nepokrývají otázku, odpověz z obecné historické znalosti a jasně nevnucuj citace z irelevantních dokumentů.
- Relevantní dodaný kontext cituj pomocí značek uvedených v kontextu, například [Z1], [Z2] atd.
- Zmiňuj pouze ty zdroje, které v odpovědi skutečně používáš.
- Nepředstírej, že nepodložené tvrzení je ze zdrojů.
- Pokud relevantní kontext nestačí, řekni to jasně a stručně; potom můžeš doplnit obecnou historickou znalost bez falešného zdrojování.
- Můžeš doplnit obecně známý historický kontext.
- Nevymýšlej bibliografické údaje ani citace.
- Nemusíš použít žádnou nalezenou pasáž, pokud není skutečně relevantní. Slabé, okrajové nebo zavádějící pasáže vynech.

Styl: {style}
Délka: {length}

Forma odpovědi:
- Piš v Markdownu.
- Zvol přirozenou strukturu podle otázky.
- Citace vkládej přímo za tvrzení, která zdroj podporuje, jako markdownové poznámky pod čarou ve tvaru [^Z1], [^Z2] atd.
- Připojuj značku [^Zx] hned za název díla, autora, editora nebo historika, například "Podle dokumentu Železná opona v Československu[^Z7]..." nebo "Podle historiků Ripky a Maškové[^Z7]...".
- Neomezuj se na holé "Podle [^Z7]". Samotnou značku [^Zx] používej spíš až za názvem dokumentu, institucí nebo jmény, pokud je kontext poskytuje.
- Pokud jednu větu podporuje více zdrojů, můžeš uvést více poznámek pod čarou za sebou, například [^Z2][^Z4].
- Používej jen takové poznámky pod čarou, které skutečně odpovídají dodaným zdrojům.
- Pokud zdroj podporuje jen obecné pozadí, ale ne konkrétní tvrzení v odpovědi, necituj ho.
- Nikdy nevymýšlej autory, editory ani bibliografické údaje. Pokud je kontext neposkytuje, použij raději název dokumentu nebo neutrální formulaci se značkou [Zx].
- Nevytvářej na konci samostatný seznam "Použité zdroje" ani jiný vlastní závěrečný seznam zdrojů. Stačí průběžné poznámky pod čarou v textu; přehled zdrojů vytvoří rozhraní samo.
- Neuzavírej odpověď nabídkami typu "Pokud chceš..." nebo podobnými dodatky. Odpověz přímo a přirozeně.
- Pokud přidáváš obecné znalosti mimo nalezený kontext, uveď to přirozeně. V profilu `ucitel` je můžeš použít bez nucené zvláštní značky; v profilu `historik` buď opatrný a označ nejistotu, pokud ji nelze podložit.
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
) -> list[dict[str, str]]:
    context = _format_context(retrieved_chunks)
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


def _format_context(chunks: list[dict[str, Any]]) -> str:
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
