from html.parser import HTMLParser
from pathlib import Path

import pytest
from docutils import nodes
import shutil
from collections.abc import Callable

from rdflib import RDF, BNode, Graph, Literal, Namespace, URIRef
from sphinx.testing.util import SphinxTestApp

BASE = "https://example.org/vocab/"
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
EX = Namespace("https://example.org/terms/")


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


def page(address: str) -> str:
    """Return the document name of the generated page at ``address``."""
    return f"vocabularies/{address}"


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

        paragraphs = field_paragraphs(app, page("facts/rich"))
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

        assert ["Plain"] in field_paragraphs(app, page("facts/rich"))

    @pytest.mark.sphinx("dirhtml", testroot="facts")
    def test_no_hidden_label_appears_on_the_page(self, app: SphinxTestApp) -> None:
        app.build()

        assert "secretword" not in page_html(app, page("facts/rich"))

    @pytest.mark.sphinx("dirhtml", testroot="facts")
    def test_both_definitions_with_their_languages_and_the_notation_appear(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        paragraphs = field_paragraphs(app, page("facts/rich"))
        for definition, tag in [
            ("Having much money.", "en"),
            ("Mit viel Geld.", "de"),
        ]:
            assert any(has_tag(p, definition, tag) for p in paragraphs)
        assert ["R1"] in paragraphs

    @pytest.mark.sphinx("dirhtml", testroot="facts")
    def test_the_uri_appears_on_the_page(self, app: SphinxTestApp) -> None:
        app.build()

        assert [BASE + "facts/rich"] in field_paragraphs(app, page("facts/rich"))
        assert [BASE + "facts/bare"] in field_paragraphs(app, page("facts/bare"))

    @pytest.mark.sphinx("dirhtml", testroot="facts")
    def test_a_resource_without_facts_shows_only_its_uri_and_type(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        assert field_links(app, BASE + "facts/bare") == [
            [],
            [str(RDF.type), str(SKOS.Concept)],
        ]

    @pytest.mark.sphinx("dirhtml", testroot="facts")
    def test_the_title_is_the_first_label_by_language_tag_then_text(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        assert app.env.titles[page("facts/reverse")].astext() == "Beta"
        assert app.env.titles[page("facts/bare")].astext() == BASE + "facts/bare"

    @pytest.mark.sphinx("dirhtml", testroot="facts")
    def test_a_label_holding_markup_is_escaped_and_makes_no_element(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        parser = ElementNames()
        html = page_html(app, page("facts/markup"))
        parser.feed(html)

        assert "&lt;b&gt;&amp;amp;&lt;/b&gt;" in html
        assert "b" not in parser.names


class TestFieldTranslation:
    @pytest.mark.sphinx("dirhtml", testroot="translation")
    def test_a_field_name_is_translated_and_a_label_equal_to_it_is_not(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        doctree = app.env.get_doctree(page("words/shared"))
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
        self.depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "dl" and (
            self.depth or "field-list" in (attributes.get("class") or "").split()
        ):
            self.depth += 1
        elif self.depth and tag == "dt":
            self.fields.append([])
        elif self.depth and tag == "a" and attributes.get("href") is not None:
            self.fields[-1].append(str(attributes["href"]))

    def handle_endtag(self, tag: str) -> None:
        if tag == "dl" and self.depth:
            self.depth -= 1


def field_links(app: SphinxTestApp, uri: str) -> list[list[str]]:
    """Return the links of each field on the page of ``uri``, but the last.

    The last field of a generated page is its download field, which has its own
    tests.
    """
    parser = FieldLinks()
    parser.feed(page_html(app, page(uri.removeprefix(BASE))))
    return parser.fields[:-1]


def href(app: SphinxTestApp, source: str, target: str) -> str:
    """Return the address the page of ``source`` links to the page of ``target`` by."""
    return app.builder.get_relative_uri(
        page(source.removeprefix(BASE)), page(target.removeprefix(BASE))
    )


def hrefs(app: SphinxTestApp, source: str, targets: list[str]) -> list[str]:
    return [href(app, source, target) for target in targets]


def graph_titles(rootdir: Path, testroot: str) -> dict[str, str]:
    """Return the English preferred label of every resource, read from the files."""
    graph = Graph()
    for path in (rootdir / testroot / "data").glob("*.ttl"):
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
        target = (
            Path(app.outdir) / "vocabularies" / "rel" / "hub" / address / "index.html"
        )
        assert target.resolve() == (
            Path(app.outdir) / "vocabularies" / "rel-other" / "mapped" / "index.html"
        )
        assert target.resolve().is_file()

    @pytest.mark.sphinx("dirhtml", testroot="relations")
    def test_a_script_uri_is_shown_but_never_linked(self, app: SphinxTestApp) -> None:
        app.build()

        hub = BASE + "rel/hub"
        html = page_html(app, page("rel/hub"))
        links = [link for fields in field_links(app, hub) for link in fields]
        assert "JaVaScript:alert(1)" in html
        assert "data:text/plain,x" in html
        assert not [link for link in links if link.lower().startswith(("java", "data"))]

    @pytest.mark.sphinx("dirhtml", testroot="relations")
    def test_a_literal_where_a_uri_was_expected_is_shown_as_text(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        assert ["plain text"] in field_paragraphs(app, page("rel/hub"))

    @pytest.mark.sphinx("dirhtml", testroot="relations")
    def test_a_concept_in_no_vocabulary_links_no_vocabulary(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        links = sum(field_links(app, BASE + "rel/loose"), [])
        vocabularies = [BASE + "rel", BASE + "rel-other"]
        assert not set(links) & set(hrefs(app, BASE + "rel/loose", vocabularies))
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

        paragraphs = field_paragraphs(app, page("rel"))
        assert any(has_tag(p, "Relations", "en") for p in paragraphs)
        assert any(has_tag(p, "The relations.", "en") for p in paragraphs)
        assert any(has_tag(p, "Describes the relations.", "en") for p in paragraphs)

    @pytest.mark.sphinx("dirhtml", testroot="relations")
    def test_the_description_is_a_field_of_its_own_beside_the_definition(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        fields = list(app.env.get_doctree(page("rel")).findall(nodes.field))
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

        assert not [
            link
            for links in field_links(app, BASE + "rel-empty")
            for link in links
            if not link.startswith("http")
        ]
        assert field_paragraphs(app, page("rel-empty"))[0] == [BASE + "rel-empty"]
        assert app.warning.getvalue() == ""


class TestCollectionPage:
    @pytest.mark.sphinx("dirhtml", testroot="relations")
    def test_it_shows_its_label(self, app: SphinxTestApp) -> None:
        app.build()

        assert any(
            has_tag(p, "Beta set", "en")
            for p in field_paragraphs(app, page("rel/col-b"))
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

        assert not [
            link
            for links in field_links(app, BASE + "rel/col-c")
            for link in links
            if link != href(app, BASE + "rel/col-c", BASE + "rel")
            and not link.startswith("http")
        ]


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
            if field.get("skos_download"):
                continue
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
        assert by_hand == shown_fields(app, page(name), BASE + name)

    @pytest.mark.sphinx("dirhtml", testroot="prose")
    def test_the_generated_pages_are_still_built(self, app: SphinxTestApp) -> None:
        app.build()

        for name in ("rel/hub", "rel", "rel/col-a"):
            assert (Path(app.outdir) / page(name) / "index.html").is_file()

    @pytest.mark.sphinx("dirhtml", testroot="prose")
    def test_only_generated_pages_have_copies_and_alternate_links(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        for name in ("rel/hub", "rel", "rel/col-a"):
            assert (Path(app.outdir) / page(name) / "index.ttl").is_file()
            assert 'rel="alternate"' in page_html(app, page(name))
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


PROPERTIES = ("prop", "prop/item", "prop/group")


def properties_graph(rootdir: Path) -> Graph:
    graph = Graph()
    graph.parse(rootdir / "test-properties" / "data" / "properties.ttl")
    return graph


def field_of(app: SphinxTestApp, docname: str, value: str) -> nodes.field:
    """Return the top-level field whose body holds a link to, or text of, ``value``."""
    doctree = app.env.get_doctree(docname)
    field_list = next(doctree.findall(nodes.field_list))
    for field in field_list.children:
        body = field[1]
        targets = [
            node.get("refuri") or node.get("reftarget")
            for node in body.findall(nodes.Element)
        ]
        texts = [str(text) for text in body.findall(nodes.Text)]
        if value in targets or value in texts:
            return field
    raise AssertionError(f"no field shows {value}")


def name_links(field: nodes.field) -> list[str]:
    """Return the addresses the field's name links to."""
    return [str(reference["refuri"]) for reference in field[0].findall(nodes.reference)]


def literal_texts(graph: Graph, node: URIRef | BNode) -> list[str]:
    """Return the text of every literal a node states, through its blank nodes."""
    texts = []
    for predicate, value in graph.predicate_objects(node):
        if predicate == SKOS.hiddenLabel:
            continue
        if isinstance(value, Literal):
            texts.append(str(value))
        elif isinstance(value, BNode):
            texts += literal_texts(graph, value)
    return texts


class TestEveryProperty:
    @pytest.mark.sphinx("dirhtml", testroot="properties")
    def test_the_site_builds_without_a_warning(self, app: SphinxTestApp) -> None:
        app.build()

        assert app.warning.getvalue() == ""

    @pytest.mark.sphinx("dirhtml", testroot="properties")
    @pytest.mark.parametrize("name", PROPERTIES)
    def test_every_literal_the_resource_states_appears_but_hidden_labels(
        self, app: SphinxTestApp, rootdir: Path, name: str
    ) -> None:
        app.build()

        expected = literal_texts(properties_graph(rootdir), URIRef(BASE + name))
        doctree = app.env.get_doctree(page(name))
        shown = {
            str(text)
            for field_list in doctree.findall(nodes.field_list)
            for text in field_list.findall(nodes.Text)
        }
        assert expected
        assert set(expected) <= shown
        assert not {"secretword", "nestedsecret"} & shown

    @pytest.mark.sphinx("dirhtml", testroot="properties")
    @pytest.mark.parametrize("name", PROPERTIES)
    def test_every_uri_the_resource_states_is_linked(
        self, app: SphinxTestApp, rootdir: Path, name: str
    ) -> None:
        app.build()

        uri = BASE + name
        graph = properties_graph(rootdir)
        links = {link for links in field_links(app, uri) for link in links}
        for value in graph.objects(URIRef(uri)):
            if not isinstance(value, URIRef):
                continue
            if str(value).startswith(BASE):
                assert href(app, uri, str(value)) in links, value
            else:
                assert str(value) in links, value

    @pytest.mark.sphinx("dirhtml", testroot="properties")
    @pytest.mark.parametrize(
        ("name", "predicate", "curie"),
        [
            ("prop", EX.custom, "ex:custom"),
            ("prop", RDF.type, "rdf:type"),
            ("prop/item", SKOS.broaderTransitive, "skos:broaderTransitive"),
            (
                "prop",
                URIRef("https://unprefixed.example/predicate"),
                "https://unprefixed.example/predicate",
            ),
        ],
    )
    def test_a_property_without_its_own_field_is_named_by_a_link_to_it(
        self, app: SphinxTestApp, name: str, predicate: URIRef, curie: str
    ) -> None:
        app.build()

        doctree = app.env.get_doctree(page(name))
        names = [
            field[0]
            for field in next(doctree.findall(nodes.field_list)).children
            if name_links(field) == [str(predicate)]
        ]
        assert [field_name.astext() for field_name in names] == [curie]

    @pytest.mark.sphinx("dirhtml", testroot="properties")
    @pytest.mark.parametrize(
        ("name", "value"),
        [
            ("prop", "https://example.org/agents/maker"),
            ("prop", "https://example.org/agents/unnamed"),
            ("prop", "https://creativecommons.org/licenses/by/4.0/"),
            ("prop", "All rights reversed."),
            ("prop", "2024-05-01"),
            ("prop", "1.2.0"),
            ("prop", "https://example.org/sources/book"),
            ("prop", "https://example.org/elsewhere"),
            ("prop", "Properties vocabulary"),
            ("prop", "PROP-1"),
            ("prop/item", "Use for items."),
            ("prop/item", "A note."),
            ("prop/item", "An example."),
            ("prop/item", "Added in 2024."),
            ("prop/item", "Check wording."),
            ("prop/item", "Renamed."),
            ("prop/group", "G1"),
            ("prop/group", "https://example.org/agents/maker"),
        ],
    )
    def test_common_metadata_has_a_field_of_its_own(
        self, app: SphinxTestApp, name: str, value: str
    ) -> None:
        app.build()

        assert name_links(field_of(app, page(name), value)) == []

    @pytest.mark.sphinx("dirhtml", testroot="properties")
    def test_each_metadata_property_has_a_separate_field(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        values = ["2024-01-02", "2024-02-03", "2024-05-01", "1.2.0", "PROP-1"]
        fields = [field_of(app, page("prop"), value).astext() for value in values]
        assert len(set(fields)) == len(values)

    @pytest.mark.sphinx("dirhtml", testroot="properties")
    def test_an_agent_the_files_name_is_shown_by_its_name_and_linked(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        field = field_of(app, page("prop"), "https://example.org/agents/maker")
        references = [
            (reference.astext(), reference["refuri"])
            for reference in field[1].findall(nodes.reference)
        ]
        assert references == [("Maker Org", "https://example.org/agents/maker")]

    @pytest.mark.sphinx("dirhtml", testroot="properties")
    def test_an_agent_the_files_do_not_name_is_shown_by_its_uri(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        unnamed = "https://example.org/agents/unnamed"
        field = field_of(app, page("prop"), unnamed)
        assert [r.astext() for r in field[1].findall(nodes.reference)] == [unnamed]

    @pytest.mark.sphinx("dirhtml", testroot="properties")
    @pytest.mark.parametrize(
        ("text", "tag"),
        [
            ("2024-05-01", "xsd:date"),
            ("42", "xsd:integer"),
            ("custom text", "de"),
        ],
    )
    def test_a_literal_shows_its_datatype_or_language(
        self, app: SphinxTestApp, text: str, tag: str
    ) -> None:
        app.build()

        assert any(has_tag(p, text, tag) for p in field_paragraphs(app, page("prop")))

    @pytest.mark.sphinx("dirhtml", testroot="properties")
    def test_a_blank_node_shows_its_own_statements_nested_in_the_field(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        field = field_of(app, page("prop"), "Ada Example")
        nested = list(field[1].findall(nodes.field_list))
        assert len(nested) == 3
        assert [n.astext().count("Example") for n in nested] == [1, 1, 1]

    @pytest.mark.sphinx("dirhtml", testroot="properties")
    def test_blank_nodes_nest_as_deep_as_the_files_state_them(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        field = field_of(app, page("prop/item"), "deep value")
        part = [
            node
            for node in field[1].findall(nodes.field_list)
            if "deep value" in node.astext()
        ]
        assert len(part) == 2
        assert name_links(next(part[1].findall(nodes.field))) == [str(EX.deepest)]

    def test_the_fields_are_in_the_same_order_on_every_build(
        self,
        make_app: Callable[..., SphinxTestApp],
        rootdir: Path,
        tmp_path: Path,
    ) -> None:
        shown = []
        for build in ("first", "second"):
            srcdir = tmp_path / build
            shutil.copytree(rootdir / "test-properties", srcdir)
            app = make_app("dirhtml", srcdir=srcdir)
            app.build()
            shown.append(
                [
                    field.astext()
                    for name in PROPERTIES
                    for field in app.env.get_doctree(page(name)).findall(nodes.field)
                ]
            )

        assert shown[0] == shown[1]


RDF_SUFFIXES = (".ttl", ".jsonld", ".rdf", ".nt")


class RdfLinks(HTMLParser):
    """Collect the ``href`` of every link to a file with an RDF suffix."""

    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        href = dict(attrs).get("href")
        if tag == "a" and href is not None and href.endswith(RDF_SUFFIXES):
            self.hrefs.append(href)


def rdf_links(page_file: Path) -> list[str]:
    """Return the links in a built page that name an RDF file."""
    parser = RdfLinks()
    parser.feed(page_file.read_text(encoding="utf-8"))
    return parser.hrefs


def vocabulary_site(rootdir: Path, tmp_path: Path, name: str = "site") -> Path:
    """Copy the test site that has several vocabularies, without its problems."""
    site = tmp_path / name
    shutil.copytree(rootdir / "test-vocabularies", site)
    shutil.rmtree(site / "problems")
    return site


def built_page(app: SphinxTestApp, address: str) -> Path:
    """Return the output file of a generated page."""
    return Path(app.builder.get_outfilename(page(address)))


def count_fields(app: SphinxTestApp, address: str) -> int:
    """Return how many fields the page has once it is resolved for the builder."""
    document = app.env.get_and_resolve_doctree(
        page(address), app.builder, tags=app.builder.tags
    )
    return len(list(document.findall(nodes.field)))


class TestDownloads:
    @pytest.mark.parametrize("theme", ["alabaster", "furo"])
    @pytest.mark.parametrize(
        "address", ["date-types/available", "date-types/by-origin"]
    )
    def test_a_concept_and_a_collection_link_their_four_copies_and_each_resolves(
        self,
        make_app: Callable[..., SphinxTestApp],
        rootdir: Path,
        tmp_path: Path,
        theme: str,
        address: str,
    ) -> None:
        site = vocabulary_site(rootdir, tmp_path)
        app = make_app("dirhtml", srcdir=site, confoverrides={"html_theme": theme})
        app.build()

        file = built_page(app, address)
        links = rdf_links(file)
        assert sorted(links) == sorted(f"index{suffix}" for suffix in RDF_SUFFIXES)
        for link in links:
            assert (file.parent / link).is_file()

    @pytest.mark.parametrize("theme", ["alabaster", "furo"])
    def test_a_vocabulary_links_its_four_whole_files_and_each_resolves(
        self,
        make_app: Callable[..., SphinxTestApp],
        rootdir: Path,
        tmp_path: Path,
        theme: str,
    ) -> None:
        site = vocabulary_site(rootdir, tmp_path)
        app = make_app("dirhtml", srcdir=site, confoverrides={"html_theme": theme})
        app.build()

        file = built_page(app, "date-types")
        links = rdf_links(file)
        assert sorted(links) == sorted(
            f"../date-types{suffix}" for suffix in RDF_SUFFIXES
        )
        for link in links:
            assert (file.parent / link).resolve().is_file()
            assert (file.parent / link).resolve().parent == Path(
                app.outdir
            ) / "vocabularies"

    @pytest.mark.sphinx("dirhtml", testroot="prose")
    def test_a_page_written_by_hand_has_no_download_links(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        for name in ("guide", "sections"):
            assert rdf_links(Path(app.outdir) / name / "index.html") == []
        assert len(rdf_links(built_page(app, "rel/hub"))) == len(RDF_SUFFIXES)

    def test_html_then_dirhtml_over_one_doctree_directory_resolves_every_link(
        self,
        make_app: Callable[..., SphinxTestApp],
        rootdir: Path,
        tmp_path: Path,
    ) -> None:
        site = vocabulary_site(rootdir, tmp_path)
        builddir = tmp_path / "build"
        make_app("html", srcdir=site, builddir=builddir).build()
        app = make_app("dirhtml", srcdir=site, builddir=builddir)
        app.build()

        for address in ("date-types", "date-types/available", "date-types/by-origin"):
            file = built_page(app, address)
            links = rdf_links(file)
            assert len(links) == len(RDF_SUFFIXES)
            for link in links:
                assert (file.parent / link).resolve().is_file()

    def test_under_html_every_page_links_its_own_copies(
        self,
        make_app: Callable[..., SphinxTestApp],
        rootdir: Path,
        tmp_path: Path,
    ) -> None:
        site = vocabulary_site(rootdir, tmp_path)
        app = make_app("html", srcdir=site)
        app.build()

        for address in ("date-types", "date-types/available"):
            file = built_page(app, address)
            links = rdf_links(file)
            assert len(links) == len(RDF_SUFFIXES)
            for link in links:
                assert (file.parent / link).is_file()

    def test_a_text_build_has_no_download_field(
        self,
        make_app: Callable[..., SphinxTestApp],
        rootdir: Path,
        tmp_path: Path,
    ) -> None:
        shown = {}
        for builder in ("text", "dirhtml"):
            site = vocabulary_site(rootdir, tmp_path, builder)
            app = make_app(builder, srcdir=site)
            app.build()
            shown[builder] = [
                count_fields(app, address)
                for address in ("date-types", "date-types/available")
            ]

        assert [html - text for html, text in zip(shown["dirhtml"], shown["text"])] == [
            1,
            1,
        ]

    @pytest.mark.sphinx("dirhtml", testroot="translation")
    def test_the_field_name_is_translated(self, app: SphinxTestApp) -> None:
        app.build()

        document = app.env.get_doctree(page("words/shared"))
        names = [name.astext() for name in document.findall(nodes.field_name)]
        assert "Herunterladen" in names
        assert "Download" not in names
