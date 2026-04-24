from __future__ import annotations

from typing import Any


STYLE_PROMPTS = {
    "laik": "Piš srozumitelně pro běžného čtenáře. Vysvětluj pojmy jednoduše a nepoužívej zbytečný odborný žargon.",
    "ucitel": "Piš didakticky, jako učitel dějepisu. Zdůrazni souvislosti, příčiny, důsledky a formuluj odpověď vhodně pro studenty.",
    "historik": "Piš přesně, formálně a historicky opatrně. Rozlišuj jistá tvrzení, interpretace a mezery v pramenech.",
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


def build_messages(
    question: str,
    retrieved_chunks: list[dict[str, Any]],
    style: str,
    length: str,
    custom_instructions: str | None = None,
    conversation_history: list[dict[str, str]] | None = None,
) -> list[dict[str, str]]:
    context = _format_context(retrieved_chunks)
    custom = custom_instructions.strip() if custom_instructions else "Žádné."
    system = f"""
Jsi pečlivý historický asistent pro RAG systém.

Úkol:
- Odpověz ve stejném jazyce jako otázka; pro české otázky odpovídej česky.
- Piš přirozeně, jako užitečný historický průvodce.
- Pokud otázka zjevně nesouvisí s historií ani s dodanými dokumenty, odpověz stručně a přirozeně, připomeň že jsi primárně historický asistent, a nevnucuj citace ani seznam zdrojů.
- Využívej dodaný kontext a vždy jej cituj pomocí značek [Z1], [Z2] atd.
- Zmiňuj pouze ty zdroje, které v odpovědi skutečně používáš.
- Nepředstírej, že nepodložené tvrzení je ze zdrojů.
- Pokud kontext nestačí, řekni to jasně a stručně.
- Můžeš doplnit obecně známý historický kontext.
- Nevymýšlej bibliografické údaje ani citace.
- Nemusíš použít všechny nalezené pasáže. Slabé nebo okrajové pasáže vynech.

Styl: {STYLE_PROMPTS[style]}
Délka: {LENGTH_PROMPTS[length]}
Vlastní instrukce uživatele: {custom}

Forma odpovědi:
- Piš v Markdownu.
- Zvol přirozenou strukturu podle otázky.
- Citace vkládej přímo za tvrzení, která zdroj podporuje, jako markdownové poznámky pod čarou ve tvaru [^Z1], [^Z2] atd.
- Připojuj značku [^Zx] hned za název díla, autora, editora nebo historika, například "Podle dokumentu Železná opona v Československu[^Z7]..." nebo "Podle historiků Ripky a Maškové[^Z7]...".
- Neomezuj se na holé "Podle [^Z7]". Samotnou značku [^Zx] používej spíš až za názvem dokumentu, institucí nebo jmény, pokud je kontext poskytuje.
- Pokud jednu větu podporuje více zdrojů, můžeš uvést více poznámek pod čarou za sebou, například [^Z2][^Z4].
- Používej jen takové poznámky pod čarou, které skutečně odpovídají dodaným zdrojům.
- Nikdy nevymýšlej autory, editory ani bibliografické údaje. Pokud je kontext neposkytuje, použij raději název dokumentu nebo neutrální formulaci se značkou [Zx].
- Nevytvářej na konci samostatný seznam "Použité zdroje" ani jiný vlastní závěrečný seznam zdrojů. Stačí průběžné poznámky pod čarou v textu; přehled zdrojů vytvoří rozhraní samo.
- Neuzavírej odpověď nabídkami typu "Pokud chceš..." nebo podobnými dodatky. Odpověz přímo a přirozeně.
- Pokud přidáváš obecné znalosti mimo nalezený kontext, uveď to přirozenou větou, ne jako zdrojované tvrzení.
""".strip()
    user = f"""
Otázka:
{question}

Nalezený kontext:
{context if context else "Nebyly nalezeny žádné relevantní pasáže."}
""".strip()
    messages: list[dict[str, str]] = [{"role": "system", "content": system}]
    for turn in (conversation_history or [])[-8:]:
        role = turn.get("role")
        content = (turn.get("content") or "").strip()
        if role not in {"user", "assistant"} or not content:
            continue
        messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": user})
    return messages


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
