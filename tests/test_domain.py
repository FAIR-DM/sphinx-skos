import shutil
from collections.abc import Callable
from pathlib import Path

from sphinx import addnodes
from sphinx.testing.util import SphinxTestApp

from sphinx_skos.domain import SKOSDomain
from sphinx_skos.pages import MARKER

type MakeApp = Callable[..., SphinxTestApp]

ADDED = """\
@base <https://example.org/vocab/> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .

<added> a skos:ConceptScheme ;
    skos:prefLabel "Added"@en .

<added/first> a skos:Concept ;
    skos:inScheme <added> ;
    skos:prefLabel "First"@en .
"""


def copy_site(rootdir: Path, tmp_path: Path) -> Path:
    """Copy the test site into a directory of its own and return it."""
    site = tmp_path / "site"
    shutil.copytree(rootdir / "test-vocabularies", site)
    shutil.rmtree(site / "problems")
    return site


def build(make_app: MakeApp, site: Path, builder: str = "dirhtml") -> SphinxTestApp:
    """Build the site into its own build directory and return the application."""
    app = make_app(builder, srcdir=site)
    app.build()
    return app


def output_files(app: SphinxTestApp) -> set[str]:
    """Return the path of every file the build wrote, relative to the output."""
    outdir = Path(app.outdir)
    return {
        str(path.relative_to(outdir))
        for path in outdir.rglob("*")
        if path.is_file() and ".doctrees" not in path.parts
    }


def doctrees(app: SphinxTestApp, docnames: set[str]) -> dict[str, str]:
    """Return the pseudo-XML of each document's doctree, without the site's path."""
    return {
        docname: app.env.get_doctree(docname).pformat().replace(str(app.srcdir), "")
        for docname in sorted(docnames)
    }


def clean_build(
    make_app: MakeApp, site: Path, tmp_path: Path
) -> tuple[set[str], dict[str, str]]:
    """Build a copy of the site's current files from nothing."""
    fresh = tmp_path / "fresh"
    shutil.rmtree(fresh, ignore_errors=True)

    def skip(directory: str, names: list[str]) -> set[str]:
        return {
            name
            for name in names
            if name == "_build"
            or (Path(directory) / name).is_file()
            and (Path(directory) / name).read_text(encoding="utf-8").startswith(MARKER)
        }

    shutil.copytree(site, fresh, ignore=skip)
    app = build(make_app, fresh)
    return output_files(app), doctrees(app, app.env.found_docs)


class TestRebuild:
    def test_a_domain_keeps_the_fingerprint_of_the_files_it_built(
        self, make_app: MakeApp, rootdir: Path, tmp_path: Path
    ) -> None:
        app = build(make_app, copy_site(rootdir, tmp_path))

        domain = app.env.domains["skos"]
        assert isinstance(domain, SKOSDomain)
        assert domain.data["fingerprint"] == domain.vocabularies.fingerprint != ""

    def test_an_edited_label_shows_on_its_page_as_in_a_clean_build(
        self, make_app: MakeApp, rootdir: Path, tmp_path: Path
    ) -> None:
        site = copy_site(rootdir, tmp_path)
        build(make_app, site)
        path = site / "vocabularies" / "methods.ttl"
        path.write_text(
            path.read_text(encoding="utf-8").replace("Survey", "Poll"),
            encoding="utf-8",
        )

        app = build(make_app, site)

        assert app.env.titles["methods/survey"].astext() == "Poll"
        files, trees = clean_build(make_app, site, tmp_path)
        assert output_files(app) == files
        assert doctrees(app, app.env.found_docs) == trees

    def test_a_removed_resource_leaves_no_source_page_or_copy(
        self, make_app: MakeApp, rootdir: Path, tmp_path: Path
    ) -> None:
        site = copy_site(rootdir, tmp_path)
        build(make_app, site)
        path = site / "vocabularies" / "methods.ttl"
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                '<methods/loose> a skos:Concept ;\n    skos:prefLabel "Loose"@en .\n',
                "",
            ),
            encoding="utf-8",
        )

        app = build(make_app, site)

        assert not (site / "methods" / "loose.rst").exists()
        assert not (Path(app.outdir) / "methods" / "loose").exists()
        assert not (Path(app.outdir) / "_sources" / "methods" / "loose.rst.txt").exists()
        assert "methods/loose" not in app.env.found_docs
        files, trees = clean_build(make_app, site, tmp_path)
        assert output_files(app) == files
        assert doctrees(app, app.env.found_docs) == trees

    def test_a_site_that_drops_every_vocabulary_file_keeps_no_generated_page(
        self, make_app: MakeApp, rootdir: Path, tmp_path: Path
    ) -> None:
        site = copy_site(rootdir, tmp_path)
        build(make_app, site)
        conf = site / "conf.py"
        conf.write_text(
            conf.read_text(encoding="utf-8") + "\nskos_vocabularies = []\n",
            encoding="utf-8",
        )

        app = build(make_app, site)

        assert not (site / "methods" / "loose.rst").exists()
        assert "example.org" not in app.warning.getvalue()
        files, trees = clean_build(make_app, site, tmp_path)
        assert output_files(app) == files

    def test_a_file_added_gives_its_resources_pages_as_in_a_clean_build(
        self, make_app: MakeApp, rootdir: Path, tmp_path: Path
    ) -> None:
        site = copy_site(rootdir, tmp_path)
        build(make_app, site)
        (site / "vocabularies" / "added.ttl").write_text(ADDED, encoding="utf-8")

        app = build(make_app, site)

        assert {"added", "added/first"} <= app.env.found_docs
        files, trees = clean_build(make_app, site, tmp_path)
        assert output_files(app) == files
        assert doctrees(app, app.env.found_docs) == trees

    def test_an_unchanged_rebuild_rewrites_no_generated_source(
        self, make_app: MakeApp, rootdir: Path, tmp_path: Path
    ) -> None:
        site = copy_site(rootdir, tmp_path)
        build(make_app, site)
        sources = sorted((site / "date-types").glob("*.rst"))
        before = {path: path.stat().st_mtime_ns for path in sources}

        build(make_app, site)

        assert sources
        assert {path: path.stat().st_mtime_ns for path in sources} == before


class TestRebuildLinks:
    def test_an_edited_label_shows_on_a_page_in_another_file_that_links_to_it(
        self, make_app: MakeApp, rootdir: Path, tmp_path: Path
    ) -> None:
        site = tmp_path / "site"
        shutil.copytree(rootdir / "test-linked", site)
        build(make_app, site)
        path = site / "vocabularies" / "b.ttl"
        path.write_text(
            path.read_text(encoding="utf-8").replace("Before", "After"),
            encoding="utf-8",
        )

        app = build(make_app, site)

        links = list(app.env.get_doctree("link/from").findall(addnodes.pending_xref))
        assert [link.astext() for link in links] == ["After"]
        files, trees = clean_build(make_app, site, tmp_path)
        assert output_files(app) == files
        assert doctrees(app, app.env.found_docs) == trees
