import shutil
from collections.abc import Callable
from pathlib import Path

import pytest
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
WITH_PROBLEMS = {"skos_vocabularies": ["vocabularies/*.ttl", "problems/*.ttl"]}


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

        assert app.env.found_docs - {"index"} == ADDRESSES
        for address in ADDRESSES:
            assert (Path(app.outdir) / address / "index.html").is_file()

    @pytest.mark.sphinx("dirhtml", testroot="vocabularies")
    def test_a_clean_site_builds_without_warnings(self, app: SphinxTestApp) -> None:
        app.build()

        assert app.warning.getvalue() == ""

    @pytest.mark.sphinx("dirhtml", testroot="vocabularies")
    def test_an_organisation_and_a_reference_have_no_page(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        assert "organisations/acme" not in app.env.found_docs
        assert "references/smith-2020" not in app.env.found_docs

    @pytest.mark.sphinx("dirhtml", testroot="vocabularies")
    def test_a_page_is_titled_with_its_resource(self, app: SphinxTestApp) -> None:
        app.build()

        assert app.env.titles["date-types/available"].astext() == "Available"
        assert app.env.titles["date-types/markup"].astext() == "<b>&amp;</b>"
        assert app.env.titles["date-types"].astext() == "Date types"

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
    def test_a_site_toctree_can_list_a_vocabulary_by_its_address(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        assert app.env.toctree_includes["index"] == ["date-types"]
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
        assert app.env.found_docs - {"index"} == ADDRESSES
        for address in ADDRESSES:
            assert (Path(app.outdir) / address / "index.html").is_file()

    @pytest.mark.sphinx("html", testroot="vocabularies")
    def test_the_html_builder_writes_each_page_at_the_file_it_gives_its_name(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        assert app.warning.getvalue() == ""
        for address in ADDRESSES:
            assert Path(app.builder.get_outfilename(address)).is_file()


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


class TestUnusableAddresses:
    @pytest.mark.sphinx("dirhtml", testroot="vocabularies", confoverrides=WITH_PROBLEMS)
    def test_a_resource_outside_the_base_uri_is_named_and_has_no_page(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        outside = "https://elsewhere.example.com/terms/outside"
        assert outside in app.warning.getvalue()
        assert app.env.found_docs - {"index"} == ADDRESSES

    @pytest.mark.sphinx("dirhtml", testroot="vocabularies", confoverrides=WITH_PROBLEMS)
    @pytest.mark.parametrize("uri", UNUSABLE)
    def test_a_uri_with_no_usable_address_is_named_and_has_no_page(
        self, app: SphinxTestApp, uri: str
    ) -> None:
        app.build()

        lines = warnings_naming(app, uri)
        assert len(lines) == 1
        assert app.env.found_docs - {"index"} == ADDRESSES


class TestCollisions:
    @pytest.mark.sphinx("dirhtml", testroot="collision")
    def test_the_sites_own_document_is_kept(self, app: SphinxTestApp) -> None:
        app.build()

        own = (Path(app.srcdir) / "own.rst").read_text(encoding="utf-8")
        assert own.startswith(":orphan:")
        output = (Path(app.outdir) / "own" / "index.html").read_text(encoding="utf-8")
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
        assert "a/index" not in app.env.found_docs

    @pytest.mark.sphinx("dirhtml", testroot="collision")
    def test_the_second_of_two_resources_at_one_address_is_named(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        lines = warnings_naming(app, BASE + "x/")
        assert len(lines) == 1
        assert "x" in app.env.found_docs
        assert "x/index" not in app.env.found_docs

    @pytest.mark.sphinx("dirhtml", testroot="collision")
    def test_a_resource_with_no_collision_still_has_its_page(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        assert "fine" in app.env.found_docs


class TestHiddenSiteDocuments:
    @pytest.mark.sphinx("dirhtml", testroot="hidden")
    def test_a_site_file_hidden_by_exclude_patterns_is_not_overwritten(
        self, app: SphinxTestApp, rootdir: Path
    ) -> None:
        app.build()

        original = rootdir / "test-hidden" / "hidden.rst"
        assert (Path(app.srcdir) / "hidden.rst").read_bytes() == original.read_bytes()
        assert len(warnings_naming(app, BASE + "hidden")) == 1
        assert "shown" in app.env.found_docs


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

        assert {"latin", "date-types"} <= app.env.found_docs


class TestSourceSuffix:
    @pytest.mark.sphinx("dirhtml", testroot="suffix")
    def test_pages_use_the_suffix_of_the_sites_restructuredtext_files(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        assert {"one", "one/first"} <= app.env.found_docs
        assert (Path(app.outdir) / "one" / "first" / "index.html").is_file()
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

        assert app.env.found_docs - {"index"} == {"plain"}
        assert [path.name for path in generated_sources(Path(app.srcdir))] == [
            "plain.rst"
        ]
        warnings = app.warning.getvalue()
        for start in ("carriage", "line", "with", "bell"):
            assert BASE + start in warnings
