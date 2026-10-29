from pathlib import Path

import pytest

from sphinx_skos.cli import main

BASE = "https://example.org/vocab/"
VOCABULARY = (
    "@prefix skos: <http://www.w3.org/2004/02/skos/core#> .\n"
    f"<{BASE}scheme> a skos:ConceptScheme ; skos:prefLabel 'Scheme'@en .\n"
    f"<{BASE}scheme/idea> a skos:Concept ; skos:prefLabel 'Idea'@en ;\n"
    f"    skos:inScheme <{BASE}scheme> .\n"
)
THREE_KEYS = """\
[tool.sphinx-skos]
title = "Three keys"
base-uri = "https://example.org/vocab/"
vocabularies = ["data/*.ttl"]
"""
UNREADABLE = "<https://example.org/vocab/lost> a <http://www.w3.org/2004/02/skos/core#"


def write_files(root: Path, files: dict[str, str]) -> None:
    for name, text in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)
    return tmp_path


class TestBuildCommand:
    def test_three_keys_and_one_file_build_the_whole_site(self, project: Path) -> None:
        write_files(project, {"pyproject.toml": THREE_KEYS, "data/one.ttl": VOCABULARY})

        code = main(["build", "-W"])

        site = project / "_build" / "site"
        assert code == 0
        assert (site / "index.html").is_file()
        assert (site / "vocabularies" / "scheme" / "index.html").is_file()
        assert (site / "vocabularies" / "scheme" / "idea" / "index.html").is_file()

    def test_the_output_option_names_the_directory_of_the_site(
        self, project: Path
    ) -> None:
        write_files(project, {"pyproject.toml": THREE_KEYS, "data/one.ttl": VOCABULARY})

        code = main(["build", "-o", "out"])

        assert code == 0
        assert (project / "out" / "index.html").is_file()
        assert not (project / "_build" / "site").exists()

    def test_a_prose_page_in_docs_is_built_and_linked_from_the_front_page(
        self, project: Path
    ) -> None:
        write_files(
            project,
            {
                "pyproject.toml": THREE_KEYS,
                "data/one.ttl": VOCABULARY,
                "docs/guide.rst": "Guide\n=====\n\nSome prose.\n",
            },
        )

        code = main(["build", "-W"])

        site = project / "_build" / "site"
        assert code == 0
        assert (site / "guide" / "index.html").is_file()
        assert 'href="guide/"' in (site / "index.html").read_text(encoding="utf-8")

    def test_a_value_conf_py_sets_wins_over_the_table(self, project: Path) -> None:
        write_files(
            project,
            {
                "pyproject.toml": THREE_KEYS,
                "data/one.ttl": VOCABULARY,
                "docs/conf.py": (
                    "extensions = ['sphinx_skos']\n"
                    "skos_base_uri = 'https://example.org/other/'\n"
                ),
            },
        )

        code = main(["build"])

        assert code == 0
        assert not (project / "_build" / "site" / "vocabularies" / "scheme").exists()

    def test_an_unreadable_file_fails_the_build_only_with_the_warning_option(
        self, project: Path
    ) -> None:
        write_files(
            project,
            {
                "pyproject.toml": THREE_KEYS,
                "data/one.ttl": VOCABULARY,
                "data/broken.ttl": UNREADABLE,
            },
        )

        lenient = main(["build"])
        strict = main(["build", "-W"])

        assert lenient == 0
        assert strict != 0

    def test_a_project_with_neither_table_nor_conf_py_exits_with_two(
        self, project: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        write_files(project, {"pyproject.toml": "[project]\nname = 'x'\n"})

        code = main(["build"])

        captured = capsys.readouterr()
        message = captured.out + captured.err
        assert code == 2
        assert "[tool.sphinx-skos]" in message
        assert "docs/conf.py" in message

    def test_a_subdirectory_of_a_project_has_no_table_of_its_own(
        self, project: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        write_files(project, {"pyproject.toml": THREE_KEYS, "data/one.ttl": VOCABULARY})
        (project / "data").mkdir(exist_ok=True)
        monkeypatch.chdir(project / "data")

        code = main(["build"])

        assert code == 2
        assert not (project / "data" / "_build").exists()
