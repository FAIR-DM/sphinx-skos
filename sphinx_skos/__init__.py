"""Build SKOS vocabularies into a Sphinx documentation site."""

from importlib.metadata import version

from sphinx.application import Sphinx
from sphinx.util.typing import ExtensionMetadata

__version__ = version("sphinx-skos")


def setup(app: Sphinx) -> ExtensionMetadata:
    """Register the extension with Sphinx.

    Args:
        app: The Sphinx application building the site.

    Returns:
        The extension's version and whether it is safe for parallel builds.
    """
    return {
        "version": __version__,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
