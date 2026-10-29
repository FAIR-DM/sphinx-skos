import posixpath
import shutil
import sys
from collections.abc import Callable
from html.parser import HTMLParser
from pathlib import Path

import pytest
from sphinx.testing.util import SphinxTestApp

VOCABULARIES = {"methods", "instruments"}
SITE_PAGES = {"guide"}
GENERATED = "methods"
COPIES = {"index.ttl", "index.jsonld", "index.rdf", "index.nt"}

type MakeApp = Callable[..., SphinxTestApp]


class ElementNames(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.names: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.names.append(tag)


class PageLinks(HTMLParser):
    """Collect the links in the sidebar and in the download menu of a page."""

    def __init__(self) -> None:
        super().__init__()
        self.sidebar: list[str] = []
        self.downloads: list[str] = []
        self.depth = 0
        self.in_sidebar_at: int | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        classes = (attributes.get("class") or "").split()
        if tag == "nav":
            self.depth += 1
            if "bd-docs-nav" in classes:
                self.in_sidebar_at = self.depth
        if tag != "a" or attributes.get("href") is None:
            return
        href = attributes["href"] or ""
        if self.in_sidebar_at is not None:
            self.sidebar.append(href)
        if any(name.startswith("btn-download-") for name in classes):
            self.downloads.append(href)

    def handle_endtag(self, tag: str) -> None:
        if tag == "nav":
            if self.in_sidebar_at == self.depth:
                self.in_sidebar_at = None
            self.depth -= 1


def page_links(app: SphinxTestApp, docname: str) -> PageLinks:
    """Parse the built page of a document under ``dirhtml``."""
    parser = PageLinks()
    page = Path(app.outdir) / ("" if docname == "index" else docname) / "index.html"
    parser.feed(page.read_text(encoding="utf-8"))
    return parser


def linked_documents(docname: str, hrefs: list[str]) -> list[str]:
    """Return the documents that a page's relative ``dirhtml`` links point to."""
    page_dir = "" if docname == "index" else docname
    documents = []
    for href in hrefs:
        path = href.split("#")[0]
        if "://" in path:
            continue
        if not path:
            documents.append(docname)
            continue
        target = posixpath.normpath(posixpath.join(page_dir, path)).strip("/")
        documents.append("index" if target in {"", "."} else target)
    return documents


def page_html(app: SphinxTestApp, docname: str) -> str:
    page = Path(app.outdir) / ("" if docname == "index" else docname) / "index.html"
    return page.read_text(encoding="utf-8")


@pytest.fixture
def make_site(make_app: MakeApp, rootdir: Path, tmp_path: Path) -> Callable[..., SphinxTestApp]:
    """Return a factory building a copy of the book test site under ``dirhtml``."""
    site = tmp_path / "site"
    shutil.copytree(rootdir / "test-book", site)

    def build(**confoverrides: object) -> SphinxTestApp:
        app = make_app("dirhtml", srcdir=site, confoverrides=confoverrides)
        app.build()
        return app

    return build


class TestBookLayout:
    @pytest.mark.sphinx("dirhtml", testroot="book")
    def test_a_site_with_no_theme_is_built_clean_with_sphinx_book_theme(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        assert app.config.html_theme == "sphinx_book_theme"
        assert app.warning.getvalue() == ""

    @pytest.mark.sphinx("dirhtml", testroot="book")
    def test_the_sidebar_links_every_vocabulary_and_the_sites_pages_on_every_page(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        for docname in ["index", "guide", "methods", "methods/survey"]:
            linked = set(linked_documents(docname, page_links(app, docname).sidebar))
            assert VOCABULARIES | SITE_PAGES <= linked, docname

    @pytest.mark.sphinx("dirhtml", testroot="book")
    def test_a_vocabulary_the_root_document_lists_is_linked_once(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        linked = linked_documents("guide", page_links(app, "guide").sidebar)
        assert linked.count("instruments") == 1

    @pytest.mark.sphinx("dirhtml", testroot="book")
    def test_a_title_holding_markup_is_escaped_and_makes_no_element(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        parser = ElementNames()
        parser.feed(page_html(app, "methods/markup"))

        assert parser.names.count("title") == 1
        assert "b" not in parser.names

    @pytest.mark.sphinx("dirhtml", testroot="book")
    def test_no_page_has_a_right_hand_sidebar(self, app: SphinxTestApp) -> None:
        app.build()

        for docname in ["index", "guide", "methods", "methods/survey"]:
            assert "bd-sidebar-secondary" not in page_html(app, docname), docname

    @pytest.mark.sphinx("dirhtml", testroot="book")
    def test_a_generated_pages_download_menu_links_its_rdf_copies_not_its_source(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        downloads = page_links(app, GENERATED).downloads
        assert COPIES <= set(downloads)
        assert not [href for href in downloads if "_sources" in href]
        for name in COPIES:
            assert (Path(app.outdir) / GENERATED / name).is_file()

    @pytest.mark.sphinx("dirhtml", testroot="book")
    def test_a_sites_own_page_keeps_its_source_in_the_download_menu(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        downloads = page_links(app, "guide").downloads
        assert [href for href in downloads if href.endswith("_sources/guide.rst")]

    def test_a_theme_option_the_site_sets_wins(
        self, make_site: Callable[..., SphinxTestApp]
    ) -> None:
        app = make_site(html_theme_options={"secondary_sidebar_items": ["page-toc"]})

        assert app.config.html_theme_options["secondary_sidebar_items"] == ["page-toc"]
        assert "bd-sidebar-secondary" in page_html(app, "guide")

    @pytest.mark.parametrize("theme", ["sphinx_book_theme", "alabaster"])
    def test_a_site_that_sets_its_theme_gets_none_of_the_defaults(
        self, make_site: Callable[..., SphinxTestApp], theme: str
    ) -> None:
        app = make_site(html_theme=theme)

        assert app.config.html_theme == theme
        assert app.env.toctree_includes["index"] == ["guide", "instruments"]
        assert not list(Path(app.outdir, "_static").glob("sphinx-skos*"))
        assert app.warning.getvalue() == ""

    def test_a_site_that_sets_sphinx_book_theme_keeps_its_download_menu(
        self, make_site: Callable[..., SphinxTestApp]
    ) -> None:
        app = make_site(html_theme="sphinx_book_theme")

        downloads = page_links(app, GENERATED).downloads
        assert [href for href in downloads if "_sources" in href]
        assert not COPIES & set(downloads)

    def test_without_sphinx_book_theme_the_site_is_built_as_before(
        self,
        make_site: Callable[..., SphinxTestApp],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setitem(sys.modules, "sphinx_book_theme", None)

        app = make_site()

        assert app.config.html_theme != "sphinx_book_theme"
        assert app.env.toctree_includes["index"] == ["guide", "instruments"]
        assert not list(Path(app.outdir, "_static").glob("sphinx-skos*"))

    def test_a_rebuild_after_installing_sphinx_book_theme_matches_a_clean_build(
        self,
        make_site: Callable[..., SphinxTestApp],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        with monkeypatch.context() as without:
            without.setitem(sys.modules, "sphinx_book_theme", None)
            make_site()

        app = make_site()

        linked = set(linked_documents("guide", page_links(app, "guide").sidebar))
        assert VOCABULARIES <= linked

    def test_a_removed_resource_leaves_no_source_copy_after_a_rebuild(
        self, make_site: Callable[..., SphinxTestApp]
    ) -> None:
        app = make_site()
        assert (Path(app.outdir) / "_sources" / "methods" / "survey.rst").is_file()
        vocabulary = Path(app.srcdir) / "vocabularies" / "methods.ttl"
        text = vocabulary.read_text(encoding="utf-8")
        vocabulary.write_text(
            text.replace("<methods/survey> a skos:Concept", "<methods/survey> a <thing>"),
            encoding="utf-8",
        )

        app = make_site()

        assert not list((Path(app.outdir) / "_sources").rglob("survey*"))
