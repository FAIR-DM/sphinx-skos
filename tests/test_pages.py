import shutil
from collections.abc import Callable
from html.parser import HTMLParser
from pathlib import Path

import pytest
from docutils import nodes
from sphinx import addnodes
from sphinx.environment.adapters.toctree import global_toctree_for_doc
from sphinx.testing.util import SphinxTestApp

from sphinx_skos.pages import MARKER

BASE = "https://example.org/vocab/"
ADDRESSES = {
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
}
DOCNAMES = {f"catalogue/{address}" for address in ADDRESSES}
INDEX = "catalogue/index"
UNUSABLE = [
    BASE,
    BASE + "date-types#fragment",
    BASE + "date-types?query=1",
    BASE + "back\\slash",
    BASE + "up/../out",
    BASE + "dot/./in",
    BASE + "empty//segment",
    BASE + "/rooted",
]
WITH_PROBLEMS = {"skos_vocabularies": ["data/*.ttl", "problems/*.ttl"]}


def generated_sources(srcdir: Path) -> list[Path]:
    """Return the files a build wrote into the source directory."""
    return sorted(
        path
        for path in srcdir.rglob("*")
        if path.is_file()
        and "_build" not in path.parts
        and path.read_text(encoding="utf-8", errors="ignore").startswith(".. ")
    )


def warnings_naming(app: SphinxTestApp, name: str) -> list[str]:
    """Return the warning lines holding ``name`` as a whole word."""
    return [line for line in app.warning.getvalue().splitlines() if f"{name} " in line]


class TestGeneratedPages:
    @pytest.mark.sphinx("dirhtml", testroot="vocabularies")
    def test_every_resource_has_a_page_at_its_address_and_nothing_else_does(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        assert app.env.found_docs - {"index", INDEX} == DOCNAMES
        for docname in DOCNAMES:
            assert (Path(app.outdir) / docname / "index.html").is_file()

    @pytest.mark.sphinx("dirhtml", testroot="vocabularies")
    def test_a_clean_site_builds_without_warnings(self, app: SphinxTestApp) -> None:
        app.build()

        assert app.warning.getvalue() == ""

    @pytest.mark.sphinx("dirhtml", testroot="vocabularies")
    def test_an_organisation_and_a_reference_have_no_page(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        assert "catalogue/organisations/acme" not in app.env.found_docs
        assert "catalogue/references/smith-2020" not in app.env.found_docs

    @pytest.mark.sphinx("dirhtml", testroot="vocabularies")
    def test_a_page_is_titled_with_its_resource(self, app: SphinxTestApp) -> None:
        app.build()

        assert (
            app.env.titles["catalogue/date-types/available"].astext() == "Available"
        )
        assert (
            app.env.titles["catalogue/date-types/markup"].astext() == "<b>&amp;</b>"
        )
        assert app.env.titles["catalogue/date-types"].astext() == "Date types"

    @pytest.mark.sphinx("dirhtml", testroot="vocabularies")
    def test_the_sites_own_pages_are_unchanged_by_the_build(
        self, app: SphinxTestApp, rootdir: Path
    ) -> None:
        app.build()

        original = rootdir / "test-vocabularies" / "index.rst"
        assert (Path(app.srcdir) / "index.rst").read_bytes() == original.read_bytes()

    @pytest.mark.sphinx("dirhtml", testroot="vocabularies")
    def test_a_generated_page_is_in_no_table_of_contents_warning(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        assert "toctree" not in app.warning.getvalue()

    @pytest.mark.sphinx("dirhtml", testroot="vocabularies")
    def test_a_site_toctree_can_list_the_index(self, app: SphinxTestApp) -> None:
        app.build()

        assert app.env.toctree_includes["index"] == [INDEX]
        assert app.warning.getvalue() == ""


class TestGeneratedDirectory:
    @pytest.mark.sphinx("dirhtml", testroot="vocabularies")
    def test_every_generated_page_is_under_the_default_directory_and_none_elsewhere(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        srcdir = Path(app.srcdir)
        generated = generated_sources(srcdir)
        assert generated
        for path in generated:
            assert path.relative_to(srcdir).parts[0] == "catalogue"

    @pytest.mark.sphinx(
        "dirhtml", testroot="vocabularies", confoverrides={"skos_directory": "terms"}
    )
    def test_a_site_can_choose_the_directory(self, app: SphinxTestApp) -> None:
        app.build()

        srcdir = Path(app.srcdir)
        generated = generated_sources(srcdir)
        assert generated
        for path in generated:
            assert path.relative_to(srcdir).parts[0] == "terms"
        assert app.env.found_docs - {"index"} == {
            f"terms/{address}" for address in {*ADDRESSES, "index"}
        }

    @pytest.mark.parametrize("directory", ["", "/abs", "a/../b"])
    def test_an_unusable_directory_is_named_and_generates_no_page(
        self,
        make_app: Callable[..., SphinxTestApp],
        rootdir: Path,
        tmp_path: Path,
        directory: str,
    ) -> None:
        site = tmp_path / "site"
        shutil.copytree(rootdir / "test-vocabularies", site)
        shutil.rmtree(site / "problems")

        app = make_app(
            "dirhtml", srcdir=site, confoverrides={"skos_directory": directory}
        )
        app.build()

        lines = [
            line
            for line in app.warning.getvalue().splitlines()
            if "skos_directory" in line
        ]
        assert len(lines) == 1
        assert generated_sources(site) == []


class TestIndexPage:
    @pytest.mark.sphinx("dirhtml", testroot="vocabularies")
    def test_the_index_links_every_vocabulary(self, app: SphinxTestApp) -> None:
        app.build()

        domain = app.env.domains["skos"]
        vocabularies = {
            domain.pages.docname_for(uri)
            for uri, kind in domain.vocabularies.resources.items()
            if kind == "vocabulary"
        }
        assert len(vocabularies) == 3
        assert vocabularies <= set(app.env.toctree_includes[INDEX])
        assert Path(app.builder.get_outfilename(INDEX)).is_file()

    @pytest.mark.sphinx("dirhtml", testroot="vocabularies")
    def test_no_generated_source_is_orphan(self, app: SphinxTestApp) -> None:
        app.build()

        generated = generated_sources(Path(app.srcdir))
        assert generated
        for path in generated:
            assert ":orphan:" not in path.read_text(encoding="utf-8")

    @pytest.mark.sphinx("dirhtml", testroot="unlisted")
    def test_a_site_that_does_not_list_the_index_gets_one_warning_naming_it(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        lines = app.warning.getvalue().splitlines()
        assert len(lines) == 1
        assert f"{INDEX}.rst" in lines[0]

    @pytest.mark.sphinx("dirhtml", testroot="relations")
    def test_a_concept_in_no_vocabulary_is_in_a_toctree_of_the_index(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        assert "catalogue/rel/loose" in app.env.toctree_includes[INDEX]
        assert app.warning.getvalue() == ""

    def test_a_resource_at_the_address_index_is_a_collision_and_the_index_is_kept(
        self, make_app: Callable[..., SphinxTestApp], rootdir: Path, tmp_path: Path
    ) -> None:
        site = tmp_path / "site"
        shutil.copytree(rootdir / "test-vocabularies", site)
        shutil.rmtree(site / "problems")
        (site / "data" / "clash.ttl").write_text(
            "@prefix skos: <http://www.w3.org/2004/02/skos/core#> .\n"
            f"<{BASE}index> a skos:Concept .\n",
            encoding="utf-8",
        )

        app = make_app("dirhtml", srcdir=site)
        app.build()

        assert len(warnings_naming(app, BASE + "index")) == 1
        source = (site / "catalogue" / "index.rst").read_text(encoding="utf-8")
        assert source.startswith(MARKER)
        assert "skos:concept" not in source


def descendants(app: SphinxTestApp, docname: str) -> set[str]:
    """Return every document below ``docname`` in the table of contents."""
    found: set[str] = set()
    pending = list(app.env.toctree_includes.get(docname, []))
    while pending:
        child = pending.pop()
        if child not in found:
            found.add(child)
            pending.extend(app.env.toctree_includes.get(child, []))
    return found


class SidebarLinks(HTMLParser):
    """Collect the ``href`` of every link in the navigation sidebar of a Furo page."""

    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "div" and (
            self.depth or "sidebar-tree" in (attributes.get("class") or "").split()
        ):
            self.depth += 1
        elif self.depth and tag == "a" and attributes.get("href") is not None:
            self.links.append(str(attributes["href"]))

    def handle_endtag(self, tag: str) -> None:
        if tag == "div" and self.depth:
            self.depth -= 1


def sidebar_links(app: SphinxTestApp, docname: str) -> list[str]:
    parser = SidebarLinks()
    parser.feed(Path(app.builder.get_outfilename(docname)).read_text(encoding="utf-8"))
    return parser.links


def addresses(app: SphinxTestApp, source: str, uris: list[str]) -> set[str]:
    """Return the addresses the page ``source`` links the pages of ``uris`` by."""
    pages = app.env.domains["skos"].pages
    return {
        app.builder.get_relative_uri(source, pages.docname_for(uri)) for uri in uris
    }


class TestVocabularyNavigation:
    @pytest.mark.sphinx("dirhtml", testroot="vocabularies")
    def test_a_vocabulary_lists_its_concepts_then_its_collections(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        domain = app.env.domains["skos"]
        vocabulary = BASE + "date-types"
        expected = [
            domain.pages.docname_for(uri)
            for uri in (
                *domain.vocabularies.concepts_in(vocabulary, app.config.language),
                *domain.vocabularies.collections_in(vocabulary, app.config.language),
            )
        ]
        assert len(expected) == 6
        assert app.env.toctree_includes["catalogue/date-types"] == expected

    @pytest.mark.sphinx("dirhtml", testroot="vocabularies")
    def test_every_concept_and_collection_is_below_its_vocabulary(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        domain = app.env.domains["skos"]
        resources = domain.vocabularies.resources
        language = app.config.language
        for vocabulary in (
            uri for uri, kind in resources.items() if kind == "vocabulary"
        ):
            below = descendants(app, domain.pages.docname_for(vocabulary))
            members = [
                *domain.vocabularies.concepts_in(vocabulary, language),
                *domain.vocabularies.collections_in(vocabulary, language),
            ]
            assert {domain.pages.docname_for(uri) for uri in members} <= below
        assert "catalogue/date-types/in-order" in descendants(app, INDEX)

    @pytest.mark.sphinx("dirhtml", testroot="vocabularies")
    def test_the_navigation_nests_each_member_inside_its_vocabulary_entry(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        domain = app.env.domains["skos"]
        vocabulary = BASE + "date-types"
        navigation = global_toctree_for_doc(
            app.env,
            "catalogue/date-types/available",
            app.builder,
            tags=app.builder.tags,
            collapse=False,
            includehidden=True,
            titles_only=True,
        )
        assert navigation is not None
        page = app.builder.get_relative_uri(
            "catalogue/date-types/available", "catalogue/date-types"
        )
        entry = next(
            item
            for item in navigation.findall(nodes.list_item)
            if any(
                reference.get("refuri") == page
                for reference in item[0].findall(nodes.reference)
            )
        )
        nested = {
            reference.get("refuri") for reference in entry.findall(nodes.reference)
        }
        members = [
            *domain.vocabularies.concepts_in(vocabulary, app.config.language),
            *domain.vocabularies.collections_in(vocabulary, app.config.language),
        ]
        for uri in members:
            target = app.builder.get_relative_uri(
                "catalogue/date-types/available", domain.pages.docname_for(uri)
            )
            assert target in nested

    @pytest.mark.sphinx("dirhtml", testroot="vocabularies")
    def test_the_sidebar_opens_the_vocabulary_of_the_page_and_no_other(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        domain = app.env.domains["skos"]
        language = app.config.language
        source = "catalogue/date-types/available"
        own = [
            uri
            for uri in domain.vocabularies.concepts_in(BASE + "date-types", language)
            if uri != BASE + "date-types/available"
        ]
        other = domain.vocabularies.concepts_in(BASE + "methods", language)
        links = set(sidebar_links(app, source))
        assert other
        assert addresses(app, source, own) <= links
        assert not addresses(app, source, other) & links

    @pytest.mark.sphinx("dirhtml", testroot="vocabularies")
    def test_the_front_page_sidebar_lists_every_vocabulary_but_no_concept(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        domain = app.env.domains["skos"]
        resources = domain.vocabularies.resources
        language = app.config.language
        vocabularies = [uri for uri, kind in resources.items() if kind == "vocabulary"]
        concepts = [
            concept
            for vocabulary in vocabularies
            for concept in domain.vocabularies.concepts_in(vocabulary, language)
        ]
        links = set(sidebar_links(app, "index"))
        assert addresses(app, "index", vocabularies) <= links
        assert not addresses(app, "index", concepts) & links

    @pytest.mark.sphinx("dirhtml", testroot="vocabularies")
    def test_the_vocabulary_page_body_shows_no_toctree(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        doctree = app.env.get_and_resolve_doctree(
            "catalogue/date-types", app.builder, tags=app.builder.tags
        )
        assert not list(doctree.findall(addnodes.toctree))
        assert not [
            node
            for node in doctree.findall(nodes.compound)
            if "toctree-wrapper" in node["classes"] and len(node.children)
        ]

    @pytest.mark.sphinx("dirhtml", testroot="vocabularies")
    def test_the_index_hides_only_resources_no_vocabulary_lists(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        listed = set(app.env.toctree_includes[INDEX])
        assert listed == {
            "catalogue/date-types",
            "catalogue/methods",
            "catalogue/instruments",
            "catalogue/methods/loose",
        }

    @pytest.mark.sphinx("dirhtml", testroot="shared")
    def test_a_concept_in_two_vocabularies_is_listed_by_both_without_warning(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        both = "catalogue/common/both"
        assert both in app.env.toctree_includes["catalogue/north"]
        assert both in app.env.toctree_includes["catalogue/south"]
        assert (
            "catalogue/common/north-only"
            not in (app.env.toctree_includes["catalogue/south"])
        )
        assert sum(docname == both for docname in app.env.found_docs) == 1
        assert app.warning.getvalue() == ""


class TestThemesAndBuilders:
    @pytest.mark.parametrize("theme", ["alabaster", "furo"])
    def test_a_site_builds_clean_with_the_same_pages_under_any_theme(
        self,
        make_app: Callable[..., SphinxTestApp],
        rootdir: Path,
        tmp_path: Path,
        theme: str,
    ) -> None:
        site = tmp_path / theme
        shutil.copytree(rootdir / "test-vocabularies", site)
        shutil.rmtree(site / "problems")

        app = make_app("dirhtml", srcdir=site, confoverrides={"html_theme": theme})
        app.build()

        assert app.warning.getvalue() == ""
        assert app.env.found_docs - {"index", INDEX} == DOCNAMES
        for docname in DOCNAMES:
            assert (Path(app.outdir) / docname / "index.html").is_file()

    @pytest.mark.sphinx("html", testroot="vocabularies")
    def test_the_html_builder_writes_each_page_at_the_file_it_gives_its_name(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        assert app.warning.getvalue() == ""
        for docname in DOCNAMES:
            assert Path(app.builder.get_outfilename(docname)).is_file()


class TestCleanUp:
    def test_a_file_without_the_marker_is_never_deleted(
        self, make_app: Callable[..., SphinxTestApp], rootdir: Path, tmp_path: Path
    ) -> None:
        site = tmp_path / "site"
        shutil.copytree(rootdir / "test-vocabularies", site)
        shutil.rmtree(site / "problems")
        own = site / "gone.rst"
        own.write_text(":orphan:\n\nMine\n====\n", encoding="utf-8")
        marked = site / "stale.rst"
        marked.write_text(f"{MARKER}\n\n:orphan:\n", encoding="utf-8")

        make_app("dirhtml", srcdir=site).build()

        assert own.is_file()
        assert not marked.exists()


class TestUpgrade:
    def build(
        self, make_app: Callable[..., SphinxTestApp], rootdir: Path, site: Path
    ) -> SphinxTestApp:
        shutil.copytree(rootdir / "test-upgrade", site)
        app = make_app("dirhtml", srcdir=site)
        app.build()
        return app

    @staticmethod
    def output(app: SphinxTestApp) -> dict[str, bytes]:
        outdir = Path(app.outdir)
        return {
            path.relative_to(outdir).as_posix(): path.read_bytes()
            for path in outdir.rglob("*")
            if path.is_file() and path.suffix != ".inv"
        }

    def test_pages_an_earlier_version_wrote_at_the_old_addresses_are_removed(
        self, make_app: Callable[..., SphinxTestApp], rootdir: Path, tmp_path: Path
    ) -> None:
        site = tmp_path / "site"

        app = self.build(make_app, rootdir, site)

        assert not (site / "thing.rst").exists()
        assert not (site / "thing" / "child.rst").exists()
        assert (site / "thing" / "kept.rst").is_file()
        assert (site / "notes.rst").is_file()
        assert {"thing", "thing/child"}.isdisjoint(app.env.found_docs)
        assert {"catalogue/thing", "catalogue/thing/child"} <= (
            app.env.found_docs
        )

    def test_the_output_is_what_a_clean_build_gives(
        self, make_app: Callable[..., SphinxTestApp], rootdir: Path, tmp_path: Path
    ) -> None:
        upgraded = self.build(make_app, rootdir, tmp_path / "upgraded")
        clean = tmp_path / "clean"
        shutil.copytree(rootdir / "test-upgrade", clean)
        (clean / "thing.rst").unlink()
        (clean / "thing" / "child.rst").unlink()
        fresh = make_app("dirhtml", srcdir=clean)
        fresh.build()

        assert self.output(upgraded) == self.output(fresh)


class TestUnusableAddresses:
    @pytest.mark.sphinx("dirhtml", testroot="vocabularies", confoverrides=WITH_PROBLEMS)
    def test_a_resource_outside_the_base_uri_is_named_and_has_no_page(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        outside = "https://elsewhere.example.com/terms/outside"
        assert outside in app.warning.getvalue()
        assert app.env.found_docs - {"index", INDEX} == DOCNAMES

    @pytest.mark.sphinx("dirhtml", testroot="vocabularies", confoverrides=WITH_PROBLEMS)
    @pytest.mark.parametrize("uri", UNUSABLE)
    def test_a_uri_with_no_usable_address_is_named_and_has_no_page(
        self, app: SphinxTestApp, uri: str
    ) -> None:
        app.build()

        lines = warnings_naming(app, uri)
        assert len(lines) == 1
        assert app.env.found_docs - {"index", INDEX} == DOCNAMES


class TestCollisions:
    @pytest.mark.sphinx("dirhtml", testroot="collision")
    def test_the_sites_own_document_is_kept(self, app: SphinxTestApp) -> None:
        app.build()

        own = (Path(app.srcdir) / "catalogue" / "own.rst").read_text(
            encoding="utf-8"
        )
        assert own.startswith(":orphan:")
        output = (Path(app.outdir) / "catalogue" / "own" / "index.html").read_text(
            encoding="utf-8"
        )
        assert "Own page of the site" in output

    @pytest.mark.sphinx("dirhtml", testroot="collision")
    def test_the_warning_names_the_address_and_the_resource(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        warnings = app.warning.getvalue()
        assert any(BASE + "own" in line for line in warnings.splitlines())

    @pytest.mark.sphinx("dirhtml", testroot="collision")
    def test_a_site_document_collides_with_an_address_ending_in_a_slash(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        lines = warnings_naming(app, BASE + "a/")
        assert len(lines) == 1
        assert "catalogue/a/index" not in app.env.found_docs

    @pytest.mark.sphinx("dirhtml", testroot="collision")
    def test_the_second_of_two_resources_at_one_address_is_named(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        lines = warnings_naming(app, BASE + "x/")
        assert len(lines) == 1
        assert "catalogue/x" in app.env.found_docs
        assert "catalogue/x/index" not in app.env.found_docs

    @pytest.mark.sphinx("dirhtml", testroot="collision")
    def test_a_resource_with_no_collision_still_has_its_page(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        assert "catalogue/fine" in app.env.found_docs


class TestHiddenSiteDocuments:
    @pytest.mark.sphinx("dirhtml", testroot="hidden")
    def test_a_site_file_hidden_by_exclude_patterns_is_not_overwritten(
        self, app: SphinxTestApp, rootdir: Path
    ) -> None:
        app.build()

        original = rootdir / "test-hidden" / "catalogue" / "hidden.rst"
        written = Path(app.srcdir) / "catalogue" / "hidden.rst"
        assert written.read_bytes() == original.read_bytes()
        assert len(warnings_naming(app, BASE + "hidden")) == 1
        assert "catalogue/shown" in app.env.found_docs


class TestSiteSourceEncoding:
    def test_a_site_source_that_is_not_utf8_does_not_stop_the_build(
        self, make_app: Callable[..., SphinxTestApp], rootdir: Path, tmp_path: Path
    ) -> None:
        site = tmp_path / "site"
        shutil.copytree(rootdir / "test-vocabularies", site)
        shutil.rmtree(site / "problems")
        (site / "latin.rst").write_bytes(
            ":orphan:\n\nCaf\xe9\n====\n".encode("latin-1")
        )

        app = make_app(
            "dirhtml", srcdir=site, confoverrides={"source_encoding": "latin-1"}
        )
        app.build()

        assert {"latin", "catalogue/date-types"} <= app.env.found_docs


class TestSourceSuffix:
    @pytest.mark.sphinx("dirhtml", testroot="suffix")
    def test_pages_use_the_suffix_of_the_sites_restructuredtext_files(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        assert {"catalogue/one", "catalogue/one/first"} <= app.env.found_docs
        assert (
            Path(app.outdir) / "catalogue" / "one" / "first" / "index.html"
        ).is_file()
        assert not list(Path(app.srcdir).rglob("*.rst"))

    @pytest.mark.sphinx(
        "dirhtml",
        testroot="suffix",
        srcdir="suffix-without-restructuredtext",
        confoverrides={"source_suffix": {".txt": "markdown"}},
    )
    def test_a_site_with_no_restructuredtext_suffix_gets_one_warning_and_no_pages(
        self, app: SphinxTestApp
    ) -> None:
        lines = [
            line
            for line in app.warning.getvalue().splitlines()
            if "source_suffix" in line
        ]
        assert len(lines) == 1
        assert generated_sources(Path(app.srcdir)) == []

    @pytest.mark.sphinx(
        "dirhtml",
        testroot="suffix",
        srcdir="suffix-without-restructuredtext-or-vocabularies",
        confoverrides={"source_suffix": {".txt": "markdown"}, "skos_vocabularies": []},
    )
    def test_a_site_with_no_vocabulary_files_needs_no_restructuredtext_suffix(
        self, app: SphinxTestApp
    ) -> None:
        assert "source_suffix" not in app.warning.getvalue()


class TestMissingBaseUri:
    @pytest.mark.sphinx("dirhtml", testroot="no-base-uri")
    def test_no_page_is_generated_and_one_warning_names_the_setting(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        lines = [
            line
            for line in app.warning.getvalue().splitlines()
            if "skos_base_uri" in line
        ]
        assert len(lines) == 1
        assert app.env.found_docs == {"index"}


class TestControlCharacters:
    @pytest.mark.sphinx("dirhtml", testroot="control-characters")
    def test_a_uri_with_a_control_character_or_space_gets_no_page_and_is_named(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        assert app.env.found_docs - {"index", INDEX} == {"catalogue/plain"}
        assert [path.name for path in generated_sources(Path(app.srcdir))] == [
            "index.rst",
            "plain.rst",
        ]
        warnings = app.warning.getvalue()
        for start in ("carriage", "line", "with", "bell"):
            assert BASE + start in warnings


class TestFrontPage:
    BOTH_SUFFIXES = {".rst": "restructuredtext", ".md": "restructuredtext"}

    @pytest.mark.sphinx("dirhtml", testroot="no-front-page")
    def test_a_site_with_no_index_gets_a_front_page_listing_its_pages(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        assert app.env.titles["index"].astext() == "Front page site"
        assert app.env.toctree_includes["index"] == [INDEX, "guide", "more/deep"]
        assert app.warning.getvalue() == ""

    @pytest.mark.sphinx("dirhtml", testroot="no-front-page")
    def test_the_front_page_lists_itself_first(self, app: SphinxTestApp) -> None:
        app.build()

        toctree = next(app.env.get_doctree("index").findall(addnodes.toctree))
        assert [target for _, target in toctree["entries"]] == [
            "self",
            INDEX,
            "guide",
            "more/deep",
        ]

    @pytest.mark.sphinx("dirhtml", testroot="generated-only")
    def test_a_site_of_generated_pages_only_gets_a_front_page(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        assert app.env.toctree_includes["index"] == [INDEX]
        assert app.warning.getvalue() == ""
        assert (Path(app.outdir) / "index.html").is_file()

    @pytest.mark.sphinx(
        "dirhtml",
        testroot="no-front-page",
        confoverrides={"project": "A *bold* `code` |sub| \\ title_"},
    )
    def test_a_project_name_holding_markup_is_shown_as_text(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        assert app.env.titles["index"].astext() == "A *bold* `code` |sub| \\ title_"
        assert app.warning.getvalue() == ""

    @pytest.mark.sphinx(
        "dirhtml",
        testroot="no-front-page",
        confoverrides={"project": "  Spread\nover  lines "},
    )
    def test_a_project_name_with_surrounding_and_inner_line_breaks_stays_one_title(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        assert app.env.titles["index"].astext() == "Spread over lines"
        assert app.warning.getvalue() == ""

    @pytest.mark.sphinx(
        "dirhtml",
        testroot="suffix",
        srcdir="suffix-with-its-own-index",
        confoverrides={"exclude_patterns": ["_build"]},
    )
    def test_a_site_with_an_index_of_its_own_keeps_it_and_gets_no_front_page(
        self, app: SphinxTestApp, rootdir: Path
    ) -> None:
        app.build()

        original = rootdir / "test-suffix" / "index.txt"
        assert (Path(app.srcdir) / "index.txt").read_bytes() == original.read_bytes()
        assert generated_sources(Path(app.srcdir)) == [
            Path(app.srcdir) / "catalogue" / "index.txt",
            Path(app.srcdir) / "catalogue" / "one" / "first.txt",
            Path(app.srcdir) / "catalogue" / "one.txt",
        ]
        assert app.warning.getvalue() == ""

    def test_an_index_of_another_suffix_than_the_pages_is_a_root_document(
        self, make_app: Callable[..., SphinxTestApp], rootdir: Path, tmp_path: Path
    ) -> None:
        site = tmp_path / "site"
        shutil.copytree(rootdir / "test-no-front-page", site)
        (site / "index.md").write_text(
            "Mine\n====\n\n.. toctree::\n\n   catalogue/index\n   guide\n   more/deep\n",
            encoding="utf-8",
        )

        app = make_app(
            "dirhtml", srcdir=site, confoverrides={"source_suffix": self.BOTH_SUFFIXES}
        )
        app.build()

        assert not (site / "index.rst").exists()
        assert app.env.titles["index"].astext() == "Mine"
        assert app.warning.getvalue() == ""

    def test_a_front_page_is_removed_once_the_site_writes_an_index_of_its_own(
        self, make_app: Callable[..., SphinxTestApp], rootdir: Path, tmp_path: Path
    ) -> None:
        site = tmp_path / "site"
        shutil.copytree(rootdir / "test-no-front-page", site)
        (site / "index.rst").write_text(f"{MARKER}\n\nFront\n=====\n", encoding="utf-8")
        (site / "index.md").write_text(
            "Mine\n====\n\n.. toctree::\n\n   catalogue/index\n   guide\n   more/deep\n",
            encoding="utf-8",
        )

        app = make_app(
            "dirhtml", srcdir=site, confoverrides={"source_suffix": self.BOTH_SUFFIXES}
        )
        app.build()

        assert not (site / "index.rst").exists()
        assert app.env.titles["index"].astext() == "Mine"
        assert app.warning.getvalue() == ""
