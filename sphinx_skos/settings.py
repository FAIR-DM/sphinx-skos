"""Read the site's settings from the ``[tool.sphinx-skos]`` table of a pyproject.toml."""

import tomllib
from pathlib import Path
from typing import Any

from sphinx.application import Sphinx
from sphinx.config import Config
from sphinx.util import logging

logger = logging.getLogger(__name__)

TABLE_SETTINGS = {
    "title": "project",
    "base-uri": "skos_base_uri",
    "vocabularies": "skos_vocabularies",
    "logo": "html_logo",
    "directory": "skos_directory",
}
THEME = "furo"
REPOSITORY_KEYS = ("repository", "source", "source code", "homepage")
GITHUB_ICON = (
    '<svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 16 16">'
    '<path fill-rule="evenodd" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17'
    ".55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15"
    "-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78"
    "-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64"
    "-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51"
    ".56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0"
    ' .21.15.46.55.38A8.013 8.013 0 0 0 16 8c0-4.42-3.58-8-8-8z"></path></svg>'
)


class SiteSettings:
    """The settings a site takes from its ``pyproject.toml``, and its default theme."""

    @staticmethod
    def set_by_site(config: Config, name: str) -> bool:
        """Say whether the site's ``conf.py`` or the command line set a value.

        Sphinx has no public way to tell a value the site set from one it left
        at the default, and comparing with the default cannot tell a site that
        sets the default itself, such as ``html_theme = "alabaster"``. What
        ``conf.py`` set is kept in ``_raw_config`` and what ``-D`` set in
        ``overrides``, so this is the one place that reads the private one.

        Args:
            config: The site's configuration, as soon as it has been read.
            name: The name of a setting.

        Returns:
            Whether ``conf.py`` or ``-D`` set it.
        """
        return name in config.overrides or name in config._raw_config

    @staticmethod
    def find_document(confdir: str | Path) -> tuple[dict[str, Any], Path] | None:
        """Read the nearest ``pyproject.toml``.

        Args:
            confdir: The directory that holds the site's ``conf.py``.

        Returns:
            The whole document and the directory of its file, or ``None`` if
            there is no file or it cannot be read.
        """
        directory = Path(confdir).resolve()
        for candidate in (directory, *directory.parents):
            path = candidate / "pyproject.toml"
            if not path.is_file():
                continue
            try:
                document = tomllib.loads(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as error:
                logger.warning("%s cannot be read: %s", path, error)
                return None
            return document, candidate
        return None

    @classmethod
    def find_table(cls, confdir: str | Path) -> tuple[dict[str, Any], Path] | None:
        """Find the settings table of the nearest ``pyproject.toml``.

        The search stops at the first ``pyproject.toml`` it finds, whether or
        not that file has the table, so a site never takes settings from an
        unrelated project further up.

        Args:
            confdir: The directory that holds the site's ``conf.py``.

        Returns:
            The table and the directory of its file, or ``None`` if the
            nearest file has no table or there is no file.
        """
        found = cls.find_document(confdir)
        if found is None:
            return None
        document, directory = found
        table = document.get("tool", {}).get("sphinx-skos")
        return None if table is None else (table, directory)

    @staticmethod
    def repository_url(document: dict[str, Any]) -> str | None:
        """Find the repository's address among a project's URLs.

        Args:
            document: A ``pyproject.toml`` document.

        Returns:
            The first of ``Repository``, ``Source``, ``Source Code`` and
            ``Homepage`` in ``[project.urls]``, in any case, whose value is an
            ``http`` or ``https`` URL, or ``None``.
        """
        urls = document.get("project", {}).get("urls", {})
        if not isinstance(urls, dict):
            return None
        by_key = {str(key).casefold(): value for key, value in urls.items()}
        for key in REPOSITORY_KEYS:
            value = by_key.get(key)
            if isinstance(value, str) and value.startswith(("http://", "https://")):
                return value
        return None

    @classmethod
    def apply(cls, app: Sphinx, config: Config) -> None:
        """Set the settings the site left unset and choose its default theme.

        A title from the table names the site in the theme too, through
        ``html_title``, unless the site sets that itself. A logo path is read
        from the directory of the table's file. Under Furo, the repository
        named in the project's URLs is linked from the footer, unless the
        site sets ``footer_icons`` itself.

        Args:
            app: The Sphinx application building the site.
            config: The site's configuration.
        """
        found = cls.find_document(app.confdir)
        document, directory = found if found is not None else ({}, Path())
        table = document.get("tool", {}).get("sphinx-skos")
        if table is not None:
            for key, value in table.items():
                name = TABLE_SETTINGS.get(key)
                if name is None:
                    logger.warning("Unknown key %s in [tool.sphinx-skos]", key)
                elif not cls.set_by_site(config, name):
                    if key == "vocabularies" and isinstance(value, list):
                        value = [str(directory / str(item)) for item in value]
                    if key == "logo":
                        value = str(directory / str(value))
                    setattr(config, name, value)
                    if key == "title" and not cls.set_by_site(config, "html_title"):
                        config.html_title = value
        if not cls.set_by_site(config, "html_theme"):
            config.html_theme = THEME
        url = cls.repository_url(document)
        options = config.html_theme_options
        if url and config.html_theme == THEME and "footer_icons" not in options:
            icon = {"name": "GitHub", "url": url, "html": GITHUB_ICON, "class": ""}
            config.html_theme_options = {**options, "footer_icons": [icon]}
