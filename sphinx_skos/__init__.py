"""Build SKOS vocabularies into a Sphinx documentation site."""

from importlib.metadata import version
from typing import cast

from sphinx.application import Sphinx
from sphinx.builders import Builder
from sphinx.environment import BuildEnvironment
from sphinx.project import Project
from sphinx.util.typing import ExtensionMetadata

from sphinx_skos.domain import SKOSDomain
from sphinx_skos.pages import MARKER, GeneratedPages
from sphinx_skos.vocabularies import Vocabularies

__version__ = version("sphinx-skos")


def find_site_documents(app: Sphinx) -> set[str]:
    """Return the documents of the site that the extension did not generate.

    Args:
        app: The Sphinx application building the site.

    Returns:
        The names of the documents in the source directory whose files do not
        start with the marker.
    """
    project = Project(app.srcdir, app.config.source_suffix)
    builder: Builder = app.builder
    exclude = [
        *app.config.exclude_patterns,
        *app.config.templates_path,
        *builder.get_asset_paths(),
    ]
    documents = project.discover(exclude, app.config.include_patterns)
    return {
        docname
        for docname in documents
        if not project.doc2path(docname, absolute=True)
        .read_text(encoding="utf-8")
        .startswith(MARKER)
    }


def generate_pages(app: Sphinx) -> None:
    """Load the vocabulary files and write the source of every page.

    Args:
        app: The Sphinx application building the site.
    """
    vocabularies = Vocabularies(app.config.skos_vocabularies, app.confdir)
    pages = GeneratedPages(
        vocabularies,
        app.config.skos_base_uri,
        app.config.source_suffix,
        find_site_documents(app),
    )
    pages.write(app.srcdir)
    pages.clean(app.srcdir, app.builder, [app.outdir, app.doctreedir])
    domain = cast(SKOSDomain, app.env.domains["skos"])
    domain.vocabularies = vocabularies
    domain.pages = pages


def find_outdated(
    app: Sphinx,
    env: BuildEnvironment,
    added: set[str],
    changed: set[str],
    removed: set[str],
) -> list[str]:
    """Name every document as outdated when the vocabulary files changed.

    A page's text names only its resource, so Sphinx cannot see that a
    vocabulary file changed. The fingerprint of the files is kept with the
    environment and compared on every build.

    Args:
        app: The Sphinx application building the site.
        env: The build environment.
        added: The documents Sphinx found new.
        changed: The documents Sphinx found changed.
        removed: The documents Sphinx found removed.

    Returns:
        Every document of the site if the fingerprint differs from the last
        build's, otherwise none.
    """
    domain = cast(SKOSDomain, env.domains["skos"])
    fingerprint = domain.vocabularies.fingerprint
    if domain.data["fingerprint"] == fingerprint:
        return []
    domain.data["fingerprint"] = fingerprint
    return sorted(env.found_docs)


def setup(app: Sphinx) -> ExtensionMetadata:
    """Register the extension with Sphinx.

    Registers the ``skos_vocabularies`` and ``skos_base_uri`` settings, the
    ``skos`` domain and the handler that writes the pages.

    Args:
        app: The Sphinx application building the site.

    Returns:
        The extension's version and whether it is safe for parallel builds.
    """
    app.add_config_value("skos_vocabularies", [], "env", types=[list])
    app.add_config_value("skos_base_uri", "", "env", types=[str])
    app.add_domain(SKOSDomain)
    app.connect("builder-inited", generate_pages)
    app.connect("env-get-outdated", find_outdated)
    return {
        "version": __version__,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
