import shutil
from collections.abc import Callable
from html.parser import HTMLParser
from pathlib import Path

import pytest
from rdflib import RDF, BNode, Graph, Namespace, URIRef
from rdflib.compare import isomorphic
from sphinx.testing.util import SphinxTestApp

type MakeApp = Callable[..., SphinxTestApp]

BASE = "https://example.org/vocab/"
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
ADDRESSES = [
    "date-types",
    "date-types/available",
    "date-types/created",
    "date-types/issued",
    "date-types/markup",
    "date-types/by-origin",
    "date-types/in-order",
    "methods",
    "instruments",
    "methods/survey",
    "methods/loose",
]
FORMATS = {".ttl": "turtle", ".jsonld": "json-ld", ".rdf": "xml", ".nt": "nt"}
MEDIA_TYPES = {
    ".ttl": "text/turtle",
    ".jsonld": "application/ld+json",
    ".rdf": "application/rdf+xml",
    ".nt": "application/n-triples",
}


class AlternateLinks(HTMLParser):
    """Collect the alternate links in a page's head."""

    def __init__(self) -> None:
        super().__init__()
        self.links: list[dict[str, str | None]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "link" and values.get("rel") == "alternate":
            self.links.append(values)


def alternate_links(page: Path) -> list[dict[str, str | None]]:
    """Return the alternate links of a built page."""
    parser = AlternateLinks()
    parser.feed(page.read_text(encoding="utf-8"))
    return parser.links


def copy_names(outdir: Path) -> list[str]:
    """Return the sorted paths of every RDF copy under a built site."""
    return sorted(
        path.relative_to(outdir).as_posix()
        for path in outdir.rglob("*")
        if path.suffix in FORMATS
    )


def read_files(rootdir: Path) -> Graph:
    """Read the test site's vocabulary files into one graph."""
    graph = Graph()
    for path in sorted((rootdir / "test-vocabularies" / "vocabularies").glob("*.ttl")):
        graph.parse(path, format="turtle")
    return graph


def expected_own_rdf(files: Graph, uri: str) -> Graph:
    """Collect a subject's triples and those of the blank nodes they reach."""
    expected = Graph()
    pending = [URIRef(uri)]
    seen = set(pending)
    while pending:
        subject = pending.pop()
        for triple in files.triples((subject, None, None)):
            expected.add(triple)
            node = triple[2]
            if isinstance(node, BNode) and node not in seen:
                seen.add(node)
                pending.append(node)
    return expected


def copy_file(app: SphinxTestApp, address: str, suffix: str) -> Path:
    """Return where a page's copy in one format is written."""
    page = Path(app.builder.get_outfilename(address))
    return page.with_suffix(suffix)


def read_copy(app: SphinxTestApp, address: str, suffix: str) -> Graph:
    """Parse a page's copy in one format."""
    graph = Graph()
    graph.parse(copy_file(app, address, suffix), format=FORMATS[suffix])
    return graph


def member_list(graph: Graph, collection: str) -> list[URIRef]:
    """Walk an ordered collection's list in a copy."""
    node = graph.value(URIRef(collection), SKOS.memberList)
    members = []
    while node is not None and node != RDF.nil:
        members.append(graph.value(node, RDF.first))
        node = graph.value(node, RDF.rest)
    return members


class TestRdfCopies:
    @pytest.mark.sphinx("dirhtml", testroot="vocabularies")
    def test_every_page_has_four_copies_in_its_directory_under_dirhtml(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        for address in ADDRESSES:
            for suffix in FORMATS:
                assert (Path(app.outdir) / address / f"index{suffix}").is_file()

    @pytest.mark.sphinx("html", testroot="vocabularies")
    def test_every_page_has_four_copies_beside_its_file_under_html(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        for address in ADDRESSES:
            for suffix in FORMATS:
                assert (Path(app.outdir) / f"{address}{suffix}").is_file()

    @pytest.mark.parametrize("builder", ["dirhtml", "html"])
    def test_every_copy_is_the_resources_own_rdf_from_the_files(
        self,
        make_app: MakeApp,
        rootdir: Path,
        tmp_path: Path,
        builder: str,
    ) -> None:
        site = tmp_path / "site"
        shutil.copytree(rootdir / "test-vocabularies", site)
        shutil.rmtree(site / "problems")
        app = make_app(builder, srcdir=site)
        app.build()
        files = read_files(rootdir)

        for address in ADDRESSES:
            expected = expected_own_rdf(files, BASE + address)
            assert len(expected) > 0
            for suffix in FORMATS:
                assert isomorphic(expected, read_copy(app, address, suffix))

    @pytest.mark.sphinx("dirhtml", testroot="vocabularies")
    def test_an_ordered_collections_copy_holds_its_members_complete_and_in_order(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        for suffix in FORMATS:
            graph = read_copy(app, "date-types/in-order", suffix)
            assert member_list(graph, BASE + "date-types/in-order") == [
                URIRef(BASE + "date-types/issued"),
                URIRef(BASE + "date-types/created"),
                URIRef(BASE + "date-types/available"),
            ]

    @pytest.mark.sphinx("dirhtml", testroot="vocabularies")
    def test_a_concepts_copy_holds_nothing_stated_about_it_by_other_resources(
        self, app: SphinxTestApp
    ) -> None:
        app.build()
        concept = URIRef(BASE + "date-types/available")
        narrower = URIRef(BASE + "date-types/created")
        collection = URIRef(BASE + "date-types/by-origin")
        files = app.env.domains["skos"].vocabularies.graph
        assert (narrower, SKOS.broader, concept) in files
        assert (collection, SKOS.member, concept) in files

        for suffix in FORMATS:
            graph = read_copy(app, "date-types/available", suffix)
            assert (None, SKOS.narrower, None) not in graph
            assert (None, SKOS.member, concept) not in graph
            assert (narrower, None, None) not in graph
            assert set(graph.subjects()) == {concept}

    @pytest.mark.sphinx("dirhtml", testroot="vocabularies")
    def test_a_copy_uses_the_prefixes_of_the_vocabulary_files(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        graph = read_copy(app, "date-types/available", ".ttl")

        assert str(dict(graph.namespaces())["skos"]) == str(SKOS)

    def test_a_removed_resources_copies_are_gone_after_a_rebuild(
        self, make_app: MakeApp, rootdir: Path, tmp_path: Path
    ) -> None:
        site = tmp_path / "site"
        shutil.copytree(rootdir / "test-vocabularies", site)
        shutil.rmtree(site / "problems")
        app = make_app("dirhtml", srcdir=site)
        app.build()
        assert copy_file(app, "methods/loose", ".ttl").is_file()
        path = site / "vocabularies" / "methods.ttl"
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                '<methods/loose> a skos:Concept ;\n    skos:prefLabel "Loose"@en .\n',
                "",
            ),
            encoding="utf-8",
        )

        rebuilt = make_app("dirhtml", srcdir=site)
        rebuilt.build()

        for suffix in FORMATS:
            assert not copy_file(rebuilt, "methods/loose", suffix).exists()
        assert not (Path(rebuilt.outdir) / "methods" / "loose").exists()


class TestAlternateLinks:
    @pytest.mark.parametrize("theme", ["alabaster", "furo"])
    def test_every_generated_page_names_each_copy_in_its_head(
        self, make_app: MakeApp, rootdir: Path, tmp_path: Path, theme: str
    ) -> None:
        site = tmp_path / theme
        shutil.copytree(rootdir / "test-vocabularies", site)
        shutil.rmtree(site / "problems")
        app = make_app("dirhtml", srcdir=site, confoverrides={"html_theme": theme})
        app.build()

        for address in ADDRESSES:
            page = Path(app.builder.get_outfilename(address))
            links = alternate_links(page)
            assert {link["type"]: link["href"] for link in links} == {
                media_type: f"index{suffix}"
                for suffix, media_type in MEDIA_TYPES.items()
            }
            assert len(links) == len(MEDIA_TYPES)
            for link in links:
                assert (page.parent / str(link["href"])).is_file()

    @pytest.mark.sphinx("html", testroot="vocabularies")
    def test_under_html_each_link_names_the_copy_beside_the_file(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        page = Path(app.builder.get_outfilename("date-types/available"))
        assert {link["href"] for link in alternate_links(page)} == {
            f"available{suffix}" for suffix in FORMATS
        }

    @pytest.mark.sphinx("dirhtml", testroot="vocabularies")
    def test_a_page_the_site_wrote_names_no_copy(self, app: SphinxTestApp) -> None:
        app.build()

        assert alternate_links(Path(app.builder.get_outfilename("index"))) == []

    def test_two_builds_of_unchanged_files_give_the_same_copies(
        self, make_app: MakeApp, rootdir: Path, tmp_path: Path
    ) -> None:
        names = []
        for name in ("first", "second"):
            site = tmp_path / name
            shutil.copytree(rootdir / "test-vocabularies", site)
            shutil.rmtree(site / "problems")
            app = make_app("dirhtml", srcdir=site)
            app.build()
            names.append(copy_names(Path(app.outdir)))

        assert names[0] == names[1]
        assert len(names[0]) == len(ADDRESSES) * len(FORMATS)
