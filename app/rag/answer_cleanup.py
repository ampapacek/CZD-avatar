"""Post-generation cleanup of model-emitted source lists.

The system prompt asks the model to use inline ``[^Z1]`` citation markers and to
leave the closing source overview to the interface. Models nevertheless append
markdown footnote *definitions* (``[^Z1]: ...``) and/or a ``Použité zdroje:``
section, because most markdown renderers need a matching definition for the
anchor to resolve. Those bodies are model-written paraphrases, not chunk
metadata, so they read as fabricated bibliographic support.

The browser already hides them at render time. This module applies the same rule
server-side so the stored answer — history, shared history, batch experiment
output — matches what the user actually saw.

Keep this in sync with ``prepareCitationMarkdown`` in ``frontend/citations.js``;
the two implementations must produce the same text for the same input.
"""

from __future__ import annotations

import re

# ``[^Z1]:`` at the start of a line — a markdown footnote definition for one of
# our citation ids. The id shape mirrors the frontend's CITATION_PATTERN.
FOOTNOTE_DEFINITION_PATTERN = re.compile(r"^\[\^[A-Z]{1,3}\d+\]:")

# A closing "Použité zdroje" heading, with or without markdown heading marks.
SOURCES_HEADING_PATTERN = re.compile(r"^(?:#{1,6}\s*)?Použité zdroje:?\s*$", re.IGNORECASE)

# A definition body may wrap onto indented continuation lines; blank lines
# between consecutive definitions are part of the block too.
CONTINUATION_PATTERN = re.compile(r"^(?: {2,}|\t)")


def strip_model_source_list(answer: str) -> str:
    """Drop model-written footnote definitions and any closing source section.

    Inline ``[^Zn]`` markers inside the prose are left untouched — only the
    definition lines and everything after a ``Použité zdroje`` heading go away.
    """

    lines = str(answer or "").replace("\r\n", "\n").replace("\r", "\n").split("\n")
    retained: list[str] = []
    skipping_definition = False

    for line in lines:
        if SOURCES_HEADING_PATTERN.match(line.strip()):
            break
        if FOOTNOTE_DEFINITION_PATTERN.match(line):
            skipping_definition = True
            continue
        if skipping_definition and (CONTINUATION_PATTERN.match(line) or not line.strip()):
            continue
        skipping_definition = False
        retained.append(line)

    return "\n".join(retained).strip()
