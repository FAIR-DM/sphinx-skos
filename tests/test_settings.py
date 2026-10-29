from collections.abc import Callable, Mapping
from importlib.metadata import requires
from pathlib import Path
from typing import Any

import pytest
from packaging.requirements import Requirement
from sphinx.testing.util import SphinxTestApp

BASE = "https://example.org/vocab/"
VOCABULARY = (
    "@prefix skos: <http://www.w3.org/2004/02/skos/core#> .\n"
    f"<{BASE}scheme> a skos:ConceptScheme ; skos:prefLabel 'Scheme'@en .\n"
    f"<{BASE}scheme/idea> a skos:Concept ; skos:prefLabel 'Idea'@en ;\n"
    f"    skos:inScheme <{BASE}scheme> .\n"
)
TABLE = """\
[tool.sphinx-skos]
title = "From the table"
base-uri = "https://example.org/vocab/"
vocabularies = ["data/*.ttl"]
directory = "terms"
"""
ROOT_DOCUMENT = "From the table\n==============\n"

Build = Callable[..., SphinxTestApp]


def write_files(root: Path, files: Mapping[str, str]) -> None:
    for name, text in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


@pytest.fixture
def build_site(make_app: Callable[..., SphinxTestApp], tmp_path: Path) -> Build:
    """Write a project and return the app for its ``docs`` directory."""

    def build(
        files: Mapping[str, str], overrides: Mapping[str, Any] | None = None
    ) -> SphinxTestApp:
        write_files(tmp_path, {"docs/index.rst": ROOT_DOCUMENT, **files})
        return make_app(
            "dirhtml", srcdir=tmp_path / "docs", confoverrides=dict(overrides or {})
        )

    return build


class TestTableSettings:
    def test_a_table_beside_a_conf_py_that_sets_nothing_supplies_every_setting(
        self, build_site: Build, tmp_path: Path
    ) -> None:
        app = build_site(
            {
                "pyproject.toml": TABLE,
                "docs/conf.py": "extensions = ['sphinx_skos']\n",
                "data/one.ttl": VOCABULARY,
            }
        )

        assert app.config.project == "From the table"
        assert app.config.skos_base_uri == BASE
        assert app.config.skos_directory == "terms"
        assert app.config.skos_vocabularies == [str(tmp_path / "data/*.ttl")]

    def test_a_relative_pattern_is_read_from_the_directory_of_the_table(
        self, build_site: Build
    ) -> None:
        app = build_site(
            {
                "pyproject.toml": TABLE,
                "docs/conf.py": "extensions = ['sphinx_skos']\n",
                "data/one.ttl": VOCABULARY,
            }
        )

        app.build()

        assert {"terms/scheme", "terms/scheme/idea"} <= app.env.found_docs

    def test_values_set_in_conf_py_win_over_the_table(self, build_site: Build) -> None:
        app = build_site(
            {
                "pyproject.toml": TABLE,
                "docs/conf.py": (
                    "extensions = ['sphinx_skos']\n"
                    "project = 'From conf'\n"
                    "skos_base_uri = 'https://example.org/other/'\n"
                ),
                "data/one.ttl": VOCABULARY,
            }
        )

        assert app.config.project == "From conf"
        assert app.config.skos_base_uri == "https://example.org/other/"
        assert app.config.skos_directory == "terms"

    def test_a_value_passed_on_the_command_line_wins_over_the_table(
        self, build_site: Build
    ) -> None:
        app = build_site(
            {
                "pyproject.toml": TABLE,
                "docs/conf.py": "extensions = ['sphinx_skos']\n",
            },
            {"skos_directory": "elsewhere"},
        )

        assert app.config.skos_directory == "elsewhere"

    def test_a_value_conf_py_sets_to_the_default_still_wins(
        self, build_site: Build
    ) -> None:
        app = build_site(
            {
                "pyproject.toml": TABLE,
                "docs/conf.py": (
                    "extensions = ['sphinx_skos']\nskos_directory = 'catalogue'\n"
                ),
            }
        )

        assert app.config.skos_directory == "catalogue"

    def test_an_unknown_key_is_named_in_a_warning(self, build_site: Build) -> None:
        app = build_site(
            {
                "pyproject.toml": TABLE + "mystery-key = 1\n",
                "docs/conf.py": "extensions = ['sphinx_skos']\n",
            }
        )

        lines = [
            line
            for line in app.warning.getvalue().splitlines()
            if "mystery-key" in line
        ]
        assert len(lines) == 1

    def test_a_pyproject_without_a_table_hides_the_table_of_an_ancestor(
        self, build_site: Build
    ) -> None:
        app = build_site(
            {
                "pyproject.toml": TABLE,
                "docs/pyproject.toml": "[project]\nname = 'unrelated'\n",
                "docs/conf.py": "extensions = ['sphinx_skos']\n",
            }
        )

        assert app.config.skos_base_uri == ""
        assert app.config.skos_vocabularies == []
        assert app.config.project != "From the table"

    def test_the_title_also_names_the_site_in_the_theme(
        self, build_site: Build
    ) -> None:
        app = build_site(
            {
                "pyproject.toml": TABLE,
                "docs/conf.py": "extensions = ['sphinx_skos']\n",
            }
        )

        assert app.config.html_title == "From the table"

    def test_an_html_title_set_in_conf_py_wins_over_the_title(
        self, build_site: Build
    ) -> None:
        app = build_site(
            {
                "pyproject.toml": TABLE,
                "docs/conf.py": (
                    "extensions = ['sphinx_skos']\nhtml_title = 'Own title'\n"
                ),
            }
        )

        assert app.config.project == "From the table"
        assert app.config.html_title == "Own title"

    def test_a_title_that_does_not_name_the_project_leaves_the_html_title(
        self, build_site: Build
    ) -> None:
        app = build_site(
            {
                "pyproject.toml": TABLE,
                "docs/conf.py": (
                    "extensions = ['sphinx_skos']\nproject = 'From conf'\n"
                ),
            }
        )

        assert "From the table" not in app.config.html_title

    def test_a_logo_is_read_from_the_directory_of_the_table_and_published(
        self, build_site: Build, tmp_path: Path
    ) -> None:
        app = build_site(
            {
                "pyproject.toml": TABLE + 'logo = "brand/logo.svg"\n',
                "docs/conf.py": "extensions = ['sphinx_skos']\n",
                "brand/logo.svg": "<svg xmlns='http://www.w3.org/2000/svg'/>\n",
            }
        )

        app.build()

        assert app.config.html_logo == str(tmp_path / "brand/logo.svg")
        assert (Path(app.outdir) / "_static" / "logo.svg").is_file()

    def test_a_logo_set_in_conf_py_wins_over_the_table(
        self, build_site: Build
    ) -> None:
        app = build_site(
            {
                "pyproject.toml": TABLE + 'logo = "brand/logo.svg"\n',
                "docs/conf.py": (
                    "extensions = ['sphinx_skos']\nhtml_logo = 'own.svg'\n"
                ),
                "docs/own.svg": "<svg xmlns='http://www.w3.org/2000/svg'/>\n",
            }
        )

        assert app.config.html_logo == "own.svg"

    def test_a_site_with_no_pyproject_keeps_its_own_settings(
        self, build_site: Build
    ) -> None:
        app = build_site(
            {"docs/conf.py": "extensions = ['sphinx_skos']\nproject = 'Mine'\n"}
        )

        assert app.config.project == "Mine"
        assert app.config.skos_directory == "catalogue"


class TestTheme:
    CONF = "extensions = ['sphinx_skos']\n"

    def test_a_site_that_sets_no_theme_is_built_with_furo(
        self, build_site: Build
    ) -> None:
        app = build_site({"docs/conf.py": self.CONF})

        assert app.config.html_theme == "furo"
        assert app.builder.theme.name == "furo"  # type: ignore[attr-defined]

    def test_a_theme_set_in_conf_py_is_kept(
        self, build_site: Build
    ) -> None:
        app = build_site({"docs/conf.py": self.CONF + "html_theme = 'classic'\n"})

        assert app.config.html_theme == "classic"
        assert app.builder.theme.name == "classic"  # type: ignore[attr-defined]

    def test_a_theme_passed_on_the_command_line_is_kept(
        self, build_site: Build
    ) -> None:
        app = build_site({"docs/conf.py": self.CONF}, {"html_theme": "classic"})

        assert app.config.html_theme == "classic"

    def test_a_theme_option_the_site_sets_is_kept(self, build_site: Build) -> None:
        app = build_site(
            {
                "docs/conf.py": self.CONF
                + "html_theme_options = {'sidebar_hide_name': True}\n"
            }
        )

        assert app.config.html_theme == "furo"
        assert app.config.html_theme_options == {"sidebar_hide_name": True}

    def test_the_extension_adds_no_static_path_stylesheet_or_theme_option(
        self, build_site: Build
    ) -> None:
        app = build_site({"docs/conf.py": self.CONF})

        assert app.config.html_static_path == []
        assert app.config.html_css_files == []
        assert app.config.html_js_files == []
        assert app.config.html_theme_options == {}


class TestDependencies:
    def test_furo_is_a_requirement_without_an_extra(self) -> None:
        requirements = [Requirement(line) for line in requires("sphinx-skos") or []]

        furo = [requirement for requirement in requirements if requirement.name == "furo"]
        assert len(furo) == 1
        assert furo[0].marker is None
