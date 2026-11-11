from __future__ import annotations

import copy
import unittest
from unittest.mock import patch

from app.rag import wp_config
from app.rag.links import public_url, rewrite_chunk_links, rewrite_url
from app.rag.wp_config import InstanceConfigError, LinkRewrite, parse_instance_config

PRIVATE = "https://storage.test/lib/repo-id/file/v1/"
PUBLIC = "https://storage.test/d/token/files/?p=/"
RULE = LinkRewrite(from_prefix=PRIVATE, to_prefix=PUBLIC)

MINIMAL = {
    "wps": [
        {
            "id": "A",
            "collections": [{"id": "a-docs", "msearch_collection_id": "id-a"}],
            "prompts": [{"id": "a-p", "name": "P", "system_prompt": "S", "user_prompt_template": "{question}"}],
        }
    ]
}


class RewriteUrlTests(unittest.TestCase):
    def test_prefix_is_swapped_and_page_fragment_kept(self) -> None:
        url = PRIVATE + "kdo-tu/Kdo%20tu%20o%208.%20kv%C4%9Btnu_%20V%20%281%29.pdf#page=11"
        self.assertEqual(
            rewrite_url(url, [RULE]),
            PUBLIC + "kdo-tu/Kdo%20tu%20o%208.%20kv%C4%9Btnu_%20V%20%281%29.pdf#page=11",
        )

    def test_path_is_reencoded_for_a_query_value(self) -> None:
        # Raw "&", "+" and spaces would break or change the ?p= value.
        url = PRIVATE + "a b/x&y+z.pdf"
        self.assertEqual(rewrite_url(url, [RULE]), PUBLIC + "a%20b/x%26y%2Bz.pdf")

    def test_no_fragment(self) -> None:
        self.assertEqual(rewrite_url(PRIVATE + "doc.pdf", [RULE]), PUBLIC + "doc.pdf")

    def test_unmatched_and_empty_urls_are_unchanged(self) -> None:
        other = "https://elsewhere.test/lib/repo-id/file/v1/doc.pdf#page=2"
        self.assertEqual(rewrite_url(other, [RULE]), other)
        self.assertEqual(rewrite_url("", [RULE]), "")
        self.assertEqual(rewrite_url(PRIVATE + "doc.pdf", []), PRIVATE + "doc.pdf")

    def test_first_matching_rule_wins(self) -> None:
        second = LinkRewrite(from_prefix=PRIVATE, to_prefix="https://other.test/")
        self.assertEqual(rewrite_url(PRIVATE + "d.pdf", [RULE, second]), PUBLIC + "d.pdf")

    def test_chunk_metadata_urls_are_rewritten_in_place(self) -> None:
        chunks = [
            {"metadata": {"url": PRIVATE + "d.pdf#page=3", "document_url": PRIVATE + "d.pdf", "source_url": None}},
            {"metadata": {"url": "https://wiki.test/x"}},
            {"text": "no metadata"},
        ]
        rewrite_chunk_links(chunks, [RULE])
        self.assertEqual(chunks[0]["metadata"]["url"], PUBLIC + "d.pdf#page=3")
        self.assertEqual(chunks[0]["metadata"]["document_url"], PUBLIC + "d.pdf")
        self.assertIsNone(chunks[0]["metadata"]["source_url"])
        self.assertEqual(chunks[1]["metadata"]["url"], "https://wiki.test/x")

    def test_public_url_uses_the_active_instance(self) -> None:
        instance = parse_instance_config({**MINIMAL, "link_rewrites": [{"from": PRIVATE, "to": PUBLIC}]})
        previous = wp_config.set_instance_config(instance)
        try:
            self.assertEqual(public_url(PRIVATE + "d.pdf"), PUBLIC + "d.pdf")
        finally:
            wp_config.set_instance_config(previous)

    def test_no_instance_means_no_rewrites(self) -> None:
        with patch.object(wp_config, "_instance", None):
            self.assertEqual(public_url(PRIVATE + "d.pdf"), PRIVATE + "d.pdf")


class LinkRewriteConfigTests(unittest.TestCase):
    def test_default_is_no_rewrites(self) -> None:
        self.assertEqual(parse_instance_config(copy.deepcopy(MINIMAL)).link_rewrites, [])

    def test_rules_are_parsed_and_trimmed(self) -> None:
        instance = parse_instance_config({**MINIMAL, "link_rewrites": [{"from": f" {PRIVATE} ", "to": PUBLIC}]})
        self.assertEqual(instance.link_rewrites, [RULE])

    def test_invalid_rules_are_errors(self) -> None:
        for bad in (
            {"from": PRIVATE},
            {"from": "", "to": PUBLIC},
            {"from": PRIVATE, "to": PUBLIC, "extra": 1},
            "not a table",
        ):
            with self.subTest(bad=bad), self.assertRaises(InstanceConfigError):
                parse_instance_config({**MINIMAL, "link_rewrites": [bad]})

    def test_duplicate_from_is_an_error(self) -> None:
        rules = [{"from": PRIVATE, "to": PUBLIC}, {"from": PRIVATE, "to": "https://x.test/"}]
        with self.assertRaises(InstanceConfigError):
            parse_instance_config({**MINIMAL, "link_rewrites": rules})


class PipelineHookTests(unittest.TestCase):
    def test_retrieved_chunks_carry_public_links(self) -> None:
        from app import main

        chunk = {"citation_id": "Z1", "text": "t", "score": 1.0, "metadata": {"url": PRIVATE + "d.pdf#page=2"}}
        instance = parse_instance_config({**MINIMAL, "link_rewrites": [{"from": PRIVATE, "to": PUBLIC}]})
        previous = wp_config.set_instance_config(instance)
        try:
            with patch.object(main.pipeline.msearch_retriever, "retrieve", return_value=[chunk]):
                candidates = main.pipeline.retrieve_candidates("q", top_k=1, retrieval_backend="msearch", rerank_enabled=False)
        finally:
            wp_config.set_instance_config(previous)
        self.assertEqual(candidates.candidates[0]["metadata"]["url"], PUBLIC + "d.pdf#page=2")


if __name__ == "__main__":
    unittest.main()
