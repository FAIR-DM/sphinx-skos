"""The ``sphinx-skos`` command, which builds a site from a ``pyproject.toml``."""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from sphinx.cmd.build import build_main

from sphinx_skos.settings import SiteSettings

BUILDER = "dirhtml"
GENERATED_SOURCE = Path("_build") / "source"
DEFAULT_OUTPUT = Path("_build") / "site"
DOCTREES = Path("_build") / "doctrees"
NO_SETTINGS = (
    "Nothing to build: add a [tool.sphinx-skos] table to pyproject.toml, "
    "or a docs/conf.py to this directory."
)


class SiteBuild:
    """One build of the site described by the project in a directory.

    Args:
        root: The directory that holds ``pyproject.toml``.
        output: Where the built site goes, relative to ``root``.
        fail_on_warning: Whether a warning makes the build fail.
    """

    def __init__(self, root: Path, output: Path, fail_on_warning: bool) -> None:
        self.root = root
        self.output = output
        self.fail_on_warning = fail_on_warning

    @property
    def conf_py(self) -> Path:
        """The ``conf.py`` of the project's ``docs`` directory, which may not exist."""
        return self.root / "docs" / "conf.py"

    def run(self) -> int:
        """Build the site.

        Returns:
            Sphinx's exit code, or 2 if the directory it runs from has neither a
            settings table of its own nor a ``docs/conf.py``.
        """
        has_conf_py = self.conf_py.is_file()
        found = SiteSettings.find_table(self.root)
        has_table = found is not None and found[1] == self.root.resolve()
        if not has_table and not has_conf_py:
            print(NO_SETTINGS, file=sys.stderr)
            return 2
        source = self.root / "docs"
        if not source.is_dir():
            source = self.root / GENERATED_SOURCE
            source.mkdir(parents=True, exist_ok=True)
        arguments = ["-b", BUILDER, "-d", str(self.root / DOCTREES)]
        if self.fail_on_warning:
            arguments.append("-W")
        if not has_conf_py:
            arguments += ["-C", "-D", "extensions=sphinx_skos"]
        arguments += [str(source), str(self.root / self.output)]
        return build_main(arguments)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the ``sphinx-skos`` command.

    Args:
        argv: The command line without the program name; ``sys.argv`` if omitted.

    Returns:
        The exit code of the command.
    """
    parser = argparse.ArgumentParser(prog="sphinx-skos")
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build", help="build the site")
    build.add_argument(
        "-o",
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="the directory to write the site to (default: %(default)s)",
    )
    build.add_argument(
        "-W",
        "--fail-on-warning",
        action="store_true",
        help="make a warning fail the build",
    )
    options = parser.parse_args(argv)
    return SiteBuild(Path.cwd(), options.output, options.fail_on_warning).run()
