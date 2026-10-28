from html.parser import HTMLParser
from pathlib import Path

import pytest
from docutils import nodes
from rdflib import Graph, Namespace, URIRef
from sphinx.testing.util import SphinxTestApp

BASE = "https://example.org/vocab/"
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")


def field_paragraphs(app: SphinxTestApp, docname: str) -> list[list[str]]:
    """Return the text nodes of every paragraph in the page's field list."""
    doctree = app.env.get_doctree(docname)
    return [
        [str(text) for text in paragraph.children if isinstance(text, nodes.Text)]
        for field_list in doctree.findall(nodes.field_list)
        for paragraph in field_list.findall(nodes.paragraph)
    ]


def has_tag(paragraph: list[str], text: str, tag: str) -> bool:
    """Whether the paragraph is ``text`` with ``tag`` in the text node after it."""
    return (
        len(paragraph) == 2
        and paragraph[0] == text
        and paragraph[1].strip(" ()") == tag
    )


def page_html(app: SphinxTestApp, address: str) -> str:
    return (Path(app.outdir) / address / "index.html").read_text(encoding="utf-8")


class ElementNames(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.names: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.names.append(tag)


class TestConceptFacts:
    @pytest.mark.sphinx("dirhtml", testroot="facts")
    def test_every_preferred_and_alternative_label_appears_with_its_language(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        paragraphs = field_paragraphs(app, "facts/rich")
        for label, tag in [
            ("Rich", "en"),
            ("Reich", "de"),
            ("Wealthy", "en"),
            ("Vermögend", "de"),
        ]:
            assert any(has_tag(p, label, tag) for p in paragraphs), label

    @pytest.mark.sphinx("dirhtml", testroot="facts")
    def test_a_label_with_no_language_shows_no_tag(self, app: SphinxTestApp) -> None:
        app.build()

        assert ["Plain"] in field_paragraphs(app, "facts/rich")

    @pytest.mark.sphinx("dirhtml", testroot="facts")
    def test_no_hidden_label_appears_on_the_page(self, app: SphinxTestApp) -> None:
        app.build()

        assert "secretword" not in page_html(app, "facts/rich")

    @pytest.mark.sphinx("dirhtml", testroot="facts")
    def test_both_definitions_with_their_languages_and_the_notation_appear(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        paragraphs = field_paragraphs(app, "facts/rich")
        for definition, tag in [
            ("Having much money.", "en"),
            ("Mit viel Geld.", "de"),
        ]:
            assert any(has_tag(p, definition, tag) for p in paragraphs)
        assert ["R1"] in paragraphs

    @pytest.mark.sphinx("dirhtml", testroot="facts")
    def test_the_uri_appears_on_the_page(self, app: SphinxTestApp) -> None:
        app.build()

        assert [BASE + "facts/rich"] in field_paragraphs(app, "facts/rich")
        assert [BASE + "facts/bare"] in field_paragraphs(app, "facts/bare")

    @pytest.mark.sphinx("dirhtml", testroot="facts")
    def test_a_resource_without_facts_shows_only_its_uri(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        assert field_paragraphs(app, "facts/bare") == [[BASE + "facts/bare"]]

    @pytest.mark.sphinx("dirhtml", testroot="facts")
    def test_the_title_is_the_first_label_by_language_tag_then_text(
        self, app: SphinxTestApp, rootdir: Path
    ) -> None:
        graph = Graph().parse(rootdir / "test-facts/vocabularies/facts.ttl")
        labels = sorted(
            (label.language or "", str(label))
            for label in graph.objects(URIRef(BASE + "facts/reverse"), SKOS.prefLabel)
        )
        app.build()

        assert app.env.titles["facts/reverse"].astext() == labels[0][1]
        assert app.env.titles["facts/bare"].astext() == BASE + "facts/bare"

    @pytest.mark.sphinx("dirhtml", testroot="facts")
    def test_a_label_holding_markup_is_escaped_and_makes_no_element(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        parser = ElementNames()
        html = page_html(app, "facts/markup")
        parser.feed(html)

        assert "&lt;b&gt;&amp;amp;&lt;/b&gt;" in html
        assert "b" not in parser.names

