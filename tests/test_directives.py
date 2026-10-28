from html.parser import HTMLParser
from pathlib import Path

import pytest
from docutils import nodes
from rdflib import Graph, Namespace
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
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        assert app.env.titles["facts/reverse"].astext() == "Beta"
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


class TestFieldTranslation:
    @pytest.mark.sphinx("dirhtml", testroot="translation")
    def test_a_field_name_is_translated_and_a_label_equal_to_it_is_not(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        doctree = app.env.get_doctree("words/shared")
        names = [name.astext() for name in doctree.findall(nodes.field_name)]
        bodies = [str(text) for text in doctree.findall(nodes.Text)]
        assert "Bevorzugte Bezeichnungen" in names
        assert "Preferred labels" not in names
        assert "Preferred labels" in bodies


class FieldLinks(HTMLParser):
    """Collect the ``href`` of every link, one list for each field."""

    def __init__(self) -> None:
        super().__init__()
        self.fields: list[list[str]] = []
        self.inside = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "dl" and "field-list" in (attributes.get("class") or "").split():
            self.inside = True
        elif self.inside and tag == "dt":
            self.fields.append([])
        elif self.inside and tag == "a" and attributes.get("href") is not None:
            self.fields[-1].append(str(attributes["href"]))

    def handle_endtag(self, tag: str) -> None:
        if tag == "dl":
            self.inside = False


def field_links(app: SphinxTestApp, uri: str) -> list[list[str]]:
    """Return the links of each field on the page of ``uri``."""
    parser = FieldLinks()
    parser.feed(page_html(app, uri.removeprefix(BASE)))
    return parser.fields


def href(app: SphinxTestApp, source: str, target: str) -> str:
    """Return the address the page of ``source`` links to the page of ``target`` by."""
    return app.builder.get_relative_uri(
        source.removeprefix(BASE), target.removeprefix(BASE)
    )


def hrefs(app: SphinxTestApp, source: str, targets: list[str]) -> list[str]:
    return [href(app, source, target) for target in targets]


def graph_titles(rootdir: Path, testroot: str) -> dict[str, str]:
    """Return the English preferred label of every resource, read from the files."""
    graph = Graph()
    for path in (rootdir / testroot / "vocabularies").glob("*.ttl"):
        graph.parse(path)
    return {str(s): str(o) for s, o in graph.subject_objects(SKOS.prefLabel)}


def computed_order(titles: dict[str, str], uris: list[str]) -> list[str]:
    """Order URIs by title, then URI, as the vocabulary promises."""
    return sorted(uris, key=lambda uri: (titles.get(uri, uri), uri))


def rel(*names: str) -> list[str]:
    return [BASE + name for name in names]


class TestConceptLinks:
    @pytest.mark.sphinx("dirhtml", testroot="relations")
    def test_the_site_builds_without_a_warning(self, app: SphinxTestApp) -> None:
        app.build()

        assert app.warning.getvalue() == ""

    @pytest.mark.sphinx("dirhtml", testroot="relations")
    def test_both_collections_the_concept_is_a_member_of_are_linked(
        self, app: SphinxTestApp, rootdir: Path
    ) -> None:
        hub = BASE + "rel/hub"
        titles = graph_titles(rootdir, "test-relations")
        expected = hrefs(
            app, hub, computed_order(titles, rel("rel/col-a", "rel/col-b"))
        )
        app.build()

        assert expected in field_links(app, hub)

    @pytest.mark.sphinx("dirhtml", testroot="relations")
    def test_the_vocabulary_of_the_concept_is_linked(self, app: SphinxTestApp) -> None:
        app.build()

        hub = BASE + "rel/hub"
        assert [href(app, hub, BASE + "rel")] in field_links(app, hub)

    @pytest.mark.sphinx("dirhtml", testroot="relations")
    def test_a_concept_stated_as_top_concept_either_way_links_its_vocabulary(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        for concept in ("rel/top", "rel/top2"):
            uri = BASE + concept
            assert [href(app, uri, BASE + "rel")] in field_links(app, uri)

    @pytest.mark.sphinx("dirhtml", testroot="relations")
    def test_broader_stated_on_either_concept_is_linked_in_the_computed_order(
        self, app: SphinxTestApp, rootdir: Path
    ) -> None:
        hub = BASE + "rel/hub"
        titles = graph_titles(rootdir, "test-relations")
        expected = hrefs(app, hub, computed_order(titles, rel("rel/pb1", "rel/pb2")))
        app.build()

        assert expected in field_links(app, hub)

    @pytest.mark.sphinx("dirhtml", testroot="relations")
    def test_narrower_stated_on_either_concept_is_linked_in_the_computed_order(
        self, app: SphinxTestApp, rootdir: Path
    ) -> None:
        hub = BASE + "rel/hub"
        titles = graph_titles(rootdir, "test-relations")
        expected = hrefs(app, hub, computed_order(titles, rel("rel/n1", "rel/n2")))
        app.build()

        assert expected in field_links(app, hub)

    @pytest.mark.sphinx("dirhtml", testroot="relations")
    def test_related_stated_on_either_concept_is_linked_in_the_computed_order(
        self, app: SphinxTestApp, rootdir: Path
    ) -> None:
        hub = BASE + "rel/hub"
        titles = graph_titles(rootdir, "test-relations")
        expected = hrefs(app, hub, computed_order(titles, rel("rel/r1", "rel/r2")))
        app.build()

        assert expected in field_links(app, hub)

    @pytest.mark.sphinx("dirhtml", testroot="relations")
    def test_the_other_side_of_a_relation_links_back_to_the_concept(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        r2 = BASE + "rel/r2"
        assert [href(app, r2, BASE + "rel/hub")] in field_links(app, r2)

    @pytest.mark.sphinx("dirhtml", testroot="relations")
    def test_a_mapping_to_a_page_and_one_outside_each_sit_in_their_own_field(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        hub = BASE + "rel/hub"
        outside = "https://elsewhere.example/outside"
        exact = [href(app, hub, BASE + "rel-other/mapped"), outside]
        fields = field_links(app, hub)
        assert exact in fields

    @pytest.mark.sphinx("dirhtml", testroot="relations")
    def test_the_link_to_a_page_reaches_that_page(self, app: SphinxTestApp) -> None:
        app.build()

        hub = BASE + "rel/hub"
        address = href(app, hub, BASE + "rel-other/mapped")
        target = Path(app.outdir) / "rel" / "hub" / address / "index.html"
        assert target.resolve() == (
            Path(app.outdir) / "rel-other" / "mapped" / "index.html"
        )
        assert target.resolve().is_file()

    @pytest.mark.sphinx("dirhtml", testroot="relations")
    def test_a_script_uri_is_shown_but_never_linked(self, app: SphinxTestApp) -> None:
        app.build()

        hub = BASE + "rel/hub"
        html = page_html(app, "rel/hub")
        links = [link for fields in field_links(app, hub) for link in fields]
        assert "JaVaScript:alert(1)" in html
        assert "data:text/plain,x" in html
        assert not [link for link in links if link.lower().startswith(("java", "data"))]

    @pytest.mark.sphinx("dirhtml", testroot="relations")
    def test_a_literal_where_a_uri_was_expected_is_shown_as_text(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        assert ["plain text"] in field_paragraphs(app, "rel/hub")

    @pytest.mark.sphinx("dirhtml", testroot="relations")
    def test_a_concept_in_no_vocabulary_links_no_vocabulary(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        assert not any(field_links(app, BASE + "rel/loose"))
        assert app.warning.getvalue() == ""


class TestConceptLinksOutsideTheBaseUri:
    @pytest.mark.sphinx("dirhtml", testroot="outside")
    def test_a_resource_outside_the_base_uri_is_linked_to_its_uri(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        links = field_links(app, BASE + "out/inside")
        assert ["https://elsewhere.example/typed"] in links


class TestVocabularyPage:
    @pytest.mark.sphinx("dirhtml", testroot="relations")
    def test_it_shows_its_label_definition_and_description(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        paragraphs = field_paragraphs(app, "rel")
        assert any(has_tag(p, "Relations", "en") for p in paragraphs)
        assert any(has_tag(p, "The relations.", "en") for p in paragraphs)
        assert any(has_tag(p, "Describes the relations.", "en") for p in paragraphs)

    @pytest.mark.sphinx("dirhtml", testroot="relations")
    def test_the_description_is_a_field_of_its_own_beside_the_definition(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        fields = list(app.env.get_doctree("rel").findall(nodes.field))
        holding = [
            field
            for text in ("The relations.", "Describes the relations.")
            for field in fields
            if text in field.astext()
        ]
        assert len(holding) == 2
        assert holding[0] is not holding[1]

    @pytest.mark.sphinx("dirhtml", testroot="relations")
    def test_every_concept_in_it_is_linked_in_the_computed_order(
        self, app: SphinxTestApp, rootdir: Path
    ) -> None:
        titles = graph_titles(rootdir, "test-relations")
        concepts = rel(
            "rel/hub",
            "rel/r2",
            "rel/pb2",
            "rel/n2",
            "rel/r1",
            "rel/n1",
            "rel/pb1",
            "rel/top",
            "rel/top2",
        )
        expected = hrefs(app, BASE + "rel", computed_order(titles, concepts))
        app.build()

        assert expected in field_links(app, BASE + "rel")

    @pytest.mark.sphinx("dirhtml", testroot="relations")
    def test_every_collection_in_it_is_linked_whether_it_says_so_or_a_member_does(
        self, app: SphinxTestApp, rootdir: Path
    ) -> None:
        titles = graph_titles(rootdir, "test-relations")
        collections = rel("rel/col-a", "rel/col-b", "rel/col-c")
        expected = hrefs(app, BASE + "rel", computed_order(titles, collections))
        app.build()

        assert expected in field_links(app, BASE + "rel")

    @pytest.mark.sphinx("dirhtml", testroot="relations")
    def test_a_vocabulary_with_no_concept_or_collection_builds_clean(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        assert not any(field_links(app, BASE + "rel-empty"))
        assert field_paragraphs(app, "rel-empty")[0] == [BASE + "rel-empty"]
        assert app.warning.getvalue() == ""


class TestCollectionPage:
    @pytest.mark.sphinx("dirhtml", testroot="relations")
    def test_it_shows_its_label(self, app: SphinxTestApp) -> None:
        app.build()

        assert any(
            has_tag(p, "Beta set", "en") for p in field_paragraphs(app, "rel/col-b")
        )

    @pytest.mark.sphinx("dirhtml", testroot="relations")
    def test_an_ordered_collection_links_its_members_in_list_order(
        self, app: SphinxTestApp
    ) -> None:
        collection = BASE + "rel/col-a"
        expected = hrefs(app, collection, rel("rel/r1", "rel/pb2", "rel/hub"))
        app.build()

        assert expected in field_links(app, collection)

    @pytest.mark.sphinx("dirhtml", testroot="relations")
    def test_an_unordered_collection_links_its_members_in_the_computed_order(
        self, app: SphinxTestApp, rootdir: Path
    ) -> None:
        collection = BASE + "rel/col-b"
        titles = graph_titles(rootdir, "test-relations")
        members = rel("rel/hub", "rel/pb2", "rel/n2")
        expected = hrefs(app, collection, computed_order(titles, members))
        app.build()

        assert expected != hrefs(app, collection, members)
        assert expected in field_links(app, collection)

    @pytest.mark.sphinx("dirhtml", testroot="relations")
    def test_a_collection_with_no_member_builds_clean(self, app: SphinxTestApp) -> None:
        app.build()

        assert not any(field_links(app, BASE + "rel/col-c"))


def shown_fields(app: SphinxTestApp, docname: str, uri: str) -> list[tuple[str, ...]]:
    """Return each field of the directive for ``uri`` in a document, as data.

    A field is its text, then the address of each link in it.
    """
    doctree = app.env.get_doctree(docname)
    shown = []
    for section in doctree.findall(nodes.section):
        field_list = next(
            (
                child
                for child in section.children
                if isinstance(child, nodes.field_list)
            ),
            None,
        )
        if field_list is None or field_list[0].astext().split("\n\n")[-1] != uri:
            continue
        for field in field_list.findall(nodes.field):
            addresses = [
                str(node.get("reftarget") or node.get("refuri"))
                for node in field.findall(nodes.Element)
                if node.get("reftarget") or node.get("refuri")
            ]
            shown.append((field.astext(), *addresses))
        break
    return shown


class TestHandWrittenDirectives:
    @pytest.mark.sphinx("dirhtml", testroot="prose")
    def test_the_site_builds_without_a_warning(self, app: SphinxTestApp) -> None:
        app.build()

        assert app.warning.getvalue() == ""

    @pytest.mark.sphinx("dirhtml", testroot="prose")
    @pytest.mark.parametrize("name", ["rel/hub", "rel", "rel/col-a"])
    def test_each_resource_shows_the_fields_and_links_of_its_generated_page(
        self, app: SphinxTestApp, name: str
    ) -> None:
        app.build()

        by_hand = shown_fields(app, "guide", BASE + name)
        assert len(by_hand) > 1
        assert by_hand == shown_fields(app, name, BASE + name)

    @pytest.mark.sphinx("dirhtml", testroot="prose")
    def test_the_generated_pages_are_still_built(self, app: SphinxTestApp) -> None:
        app.build()

        for name in ("rel/hub", "rel", "rel/col-a"):
            assert (Path(app.outdir) / name / "index.html").is_file()

    @pytest.mark.sphinx("dirhtml", testroot="prose")
    def test_only_generated_pages_have_copies_and_alternate_links(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        for name in ("rel/hub", "rel", "rel/col-a"):
            assert (Path(app.outdir) / name / "index.ttl").is_file()
            assert 'rel="alternate"' in page_html(app, name)
        for name in ("guide", "sections"):
            assert not list((Path(app.outdir) / name).glob("index.[!h]*"))
            assert 'rel="alternate"' not in page_html(app, name)

    @pytest.mark.sphinx("dirhtml", testroot="prose")
    def test_the_prose_page_keeps_its_own_content(self, app: SphinxTestApp) -> None:
        app.build()

        assert "This page is the site" in page_html(app, "guide")

    @pytest.mark.sphinx("dirhtml", testroot="prose")
    def test_a_directive_under_a_titled_section_and_twice_in_one_page_build_clean(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        document = app.env.get_doctree("sections")
        ids = [
            identifier
            for node in document.findall(nodes.Element)
            for identifier in node["ids"]
        ]
        assert len(ids) == len(set(ids))
        assert len(list(document.findall(nodes.field_list))) == 2


class TestHandWrittenDirectivesThatCannotShow:
    @pytest.mark.sphinx("dirhtml", testroot="prose-faulty", freshenv=True)
    @pytest.mark.parametrize(
        ("page", "uri"),
        [
            ("unknown", BASE + "rel/nothing-here"),
            ("wrongkind", BASE + "rel"),
            ("missing", None),
        ],
    )
    def test_each_warns_naming_the_page_and_any_uri(
        self, app: SphinxTestApp, page: str, uri: str | None
    ) -> None:
        app.build()

        warnings = [
            line
            for line in app.warning.getvalue().splitlines()
            if f"{page}.rst" in line
        ]
        assert len(warnings) == 1
        if uri is not None:
            assert uri in warnings[0]

    @pytest.mark.sphinx("dirhtml", testroot="prose-faulty", freshenv=True)
    def test_the_three_faults_are_the_only_warnings(self, app: SphinxTestApp) -> None:
        app.build()

        lines = app.warning.getvalue().splitlines()
        assert len([line for line in lines if ".rst:" in line]) == 3
