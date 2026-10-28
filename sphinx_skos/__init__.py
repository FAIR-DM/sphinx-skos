"""Build SKOS vocabularies into a Sphinx documentation site."""

from importlib.metadata import version

from sphinx.application import Sphinx
from sphinx.util.typing import ExtensionMetadata

__version__ = version("sphinx-skos")


def setup(app: Sphinx) -> ExtensionMetadata:
    """Register the extension with Sphinx.

    Registers the ``skos_vocabularies`` and ``skos_base_uri`` settings.

    Args:
        app: The Sphinx application building the site.

    Returns:
        The extension's version and whether it is safe for parallel builds.
    """
    app.add_config_value("skos_vocabularies", [], "env", types=[list])
    app.add_config_value("skos_base_uri", "", "env", types=[str])
    return {
        "version": __version__,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
