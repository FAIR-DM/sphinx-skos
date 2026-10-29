"""Build SKOS vocabularies into a Sphinx documentation site."""

from importlib.metadata import version
from typing import Any, cast

from sphinx.application import Sphinx
from sphinx.builders import Builder
from sphinx.builders.html import StandaloneHTMLBuilder
from sphinx.environment import BuildEnvironment
from sphinx.project import Project
from sphinx.util.typing import ExtensionMetadata

from sphinx_skos.copies import RdfCopies
from sphinx_skos.domain import SKOSDomain
from sphinx_skos.pages import GeneratedPages
from sphinx_skos.vocabularies import Vocabularies

__version__ = version("sphinx-skos")


def find_site_documents(app: Sphinx) -> set[str]:
    """Return the documents of the site that the extension did not generate.

    Args:
        app: The Sphinx application building the site.

    Returns:
        The names of the documents in the source directory whose files the
        extension did not write.
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
        if not GeneratedPages.is_generated(project.doc2path(docname, absolute=True))
    }


def generate_pages(app: Sphinx) -> None:
    """Load the vocabulary files and write the source of every page.

    Args:
        app: The Sphinx application building the site.
    """
    vocabularies = Vocabularies(
        app.config.skos_vocabularies, app.confdir, app.config.skos_base_uri
    )
    pages = GeneratedPages(
        vocabularies,
        app.config.skos_base_uri,
        app.config.skos_directory,
        app.config.source_suffix,
        find_site_documents(app),
    )
    pages.write(app.srcdir)
    pages.clean(app.srcdir, app.builder, [app.outdir, app.doctreedir])
    domain = cast(SKOSDomain, app.env.domains["skos"])
    domain.vocabularies = vocabularies
    domain.pages = pages


def write_copies(
    app: Sphinx,
    pagename: str,
    templatename: str,
    context: dict[str, Any],
    doctree: Any,
) -> None:
    """Write the RDF copies of a generated page and name them in its head.

    Pages the extension did not generate, and builders that do not write HTML,
    are left alone.

    Args:
        app: The Sphinx application building the site.
        pagename: The document being written.
        templatename: The template the page is rendered with.
        context: The template context, whose ``metatags`` end up in the head.
        doctree: The document's tree.
    """
    if app.builder.format != "html":
        return
    domain = cast(SKOSDomain, app.env.domains["skos"])
    uri = domain.pages.uri_for(pagename)
    if uri is None:
        return
    outfile = cast(StandaloneHTMLBuilder, app.builder).get_outfilename(pagename)
    RdfCopies(domain.vocabularies).write(uri, outfile)
    context["metatags"] = context.get("metatags", "") + RdfCopies.alternate_links(
        outfile
    )


def find_outdated(
    app: Sphinx,
    env: BuildEnvironment,
    added: set[str],
    changed: set[str],
    removed: set[str],
) -> list[str]:
    """Name every document as outdated when the vocabulary files or the extension changed.

    A page's text names only its resource, so Sphinx cannot see that a
    vocabulary file changed, or that another version of the extension would
    render it differently. The fingerprint of the files and the extension's
    version are kept with the environment and compared on every build.

    Args:
        app: The Sphinx application building the site.
        env: The build environment.
        added: The documents Sphinx found new.
        changed: The documents Sphinx found changed.
        removed: The documents Sphinx found removed.

    Returns:
        Every document of the site if the fingerprint or the version differs
        from the last build's, otherwise none.
    """
    domain = cast(SKOSDomain, env.domains["skos"])
    fingerprint = domain.vocabularies.fingerprint
    if (domain.data["fingerprint"], domain.data.get("version")) == (
        fingerprint,
        __version__,
    ):
        return []
    domain.data["fingerprint"] = fingerprint
    domain.data["version"] = __version__
    return sorted(env.found_docs)


def setup(app: Sphinx) -> ExtensionMetadata:
    """Register the extension with Sphinx.

    Registers the ``skos_vocabularies``, ``skos_base_uri`` and ``skos_directory``
    settings, the ``skos`` domain and the handlers that write the pages and
    their RDF copies.

    Args:
        app: The Sphinx application building the site.

    Returns:
        The extension's version and whether it is safe for parallel builds.
    """
    app.add_config_value("skos_vocabularies", [], "env", types=[list])
    app.add_config_value("skos_base_uri", "", "env", types=[str])
    app.add_config_value("skos_directory", "vocabularies", "env", types=[str])
    app.add_domain(SKOSDomain)
    app.connect("builder-inited", generate_pages)
    app.connect("env-get-outdated", find_outdated)
    app.connect("html-page-context", write_copies)
    return {
        "version": __version__,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
