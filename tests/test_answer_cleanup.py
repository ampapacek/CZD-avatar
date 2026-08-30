"""Server-side scrub of model-emitted source lists.

Mirrors ``prepareCitationMarkdown`` in ``frontend/citations.js``; the cases here
are the contract both implementations must satisfy.
"""

from app.rag.answer_cleanup import strip_model_source_list


def test_inline_markers_survive():
    answer = "Husitské války skončily roku 1434.[^Z1] Bitva u Lipan[^Z2] byla rozhodující."
    assert strip_model_source_list(answer) == answer


def test_footnote_definitions_are_dropped():
    answer = "Věta.[^Z1]\n\n[^Z1]: Dějiny českých zemí, str. 42\n[^Z2]: Kronika, str. 7\n"
    assert strip_model_source_list(answer) == "Věta.[^Z1]"


def test_indented_continuation_of_a_definition_is_dropped():
    answer = "Věta.[^Z1]\n\n[^Z1]: Dějiny českých zemí,\n    druhý řádek popisu\n"
    assert strip_model_source_list(answer) == "Věta.[^Z1]"


def test_blank_lines_between_definitions_are_dropped():
    answer = "Věta.[^Z1]\n\n[^Z1]: První\n\n[^Z2]: Druhý\n"
    assert strip_model_source_list(answer) == "Věta.[^Z1]"


def test_prose_after_a_definition_block_is_kept():
    answer = "Věta.[^Z1]\n\n[^Z1]: Popis\nDalší odstavec textu."
    assert strip_model_source_list(answer) == "Věta.[^Z1]\n\nDalší odstavec textu."


def test_sources_heading_truncates_the_rest():
    answer = "Věta.[^Z1]\n\n## Použité zdroje\n- Dějiny českých zemí\n- Kronika\n"
    assert strip_model_source_list(answer) == "Věta.[^Z1]"


def test_sources_heading_without_markdown_marks():
    answer = "Věta.[^Z1]\n\nPoužité zdroje:\n1. Dějiny\n"
    assert strip_model_source_list(answer) == "Věta.[^Z1]"


def test_heading_match_is_anchored_not_substring():
    answer = "Použité zdroje jsou uvedeny v poznámkách pod čarou.[^Z1]"
    assert strip_model_source_list(answer) == answer


def test_crlf_input_is_normalized():
    assert strip_model_source_list("Věta.[^Z1]\r\n\r\n[^Z1]: Popis\r\n") == "Věta.[^Z1]"


def test_empty_and_none_are_safe():
    assert strip_model_source_list("") == ""
    assert strip_model_source_list(None) == ""
