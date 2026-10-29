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
    def find_table(confdir: str | Path) -> tuple[dict[str, Any], Path] | None:
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
            table = document.get("tool", {}).get("sphinx-skos")
            return None if table is None else (table, candidate)
        return None

    @classmethod
    def apply(cls, app: Sphinx, config: Config) -> None:
        """Set the settings the site left unset and choose its default theme.

        A title from the table names the site in the theme too, through
        ``html_title``, unless the site sets that itself. A logo path is read
        from the directory of the table's file.

        Args:
            app: The Sphinx application building the site.
            config: The site's configuration.
        """
        found = cls.find_table(app.confdir)
        if found is not None:
            table, directory = found
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
