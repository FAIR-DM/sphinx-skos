"""The ready-made layout a site gets from the ``book`` extra."""

from html import escape
from pathlib import Path
from typing import Any, cast

from docutils import nodes
from sphinx import addnodes
from sphinx.application import Sphinx
from sphinx.builders.html import StandaloneHTMLBuilder
from sphinx.config import Config
from sphinx.locale import get_translation

from sphinx_skos.copies import COPY_FORMATS, RdfCopies
from sphinx_skos.domain import SKOSDomain

translate = get_translation("sphinx_skos")


class BookLayout:
    """Lay a site out with sphinx-book-theme when it sets no theme of its own.

    A site gets the layout when sphinx-book-theme can be imported and neither
    its ``conf.py`` nor the command line sets ``html_theme``. Every theme option
    the site sets keeps the site's value.
    """

    theme = "sphinx_book_theme"
    static_dir = Path(__file__).parent / "static"
    stylesheet = "sphinx-skos-book.css"

    @staticmethod
    def applies(config: Config) -> bool:
        """Return whether a site gets the layout.

        Args:
            config: The site's configuration.

        Returns:
            Whether sphinx-book-theme is installed and the site sets no theme.
        """
        # Sphinx keeps no public record of which settings a site made itself.
        if "html_theme" in config._raw_config or "html_theme" in config.overrides:
            return False
        try:
            import sphinx_book_theme  # noqa: F401
        except ImportError:
            return False
        return True

    @classmethod
    def configure(cls, app: Sphinx, config: Config) -> None:
        """Set the theme, its defaults and the handlers, when the site gets the layout.

        Args:
            app: The Sphinx application building the site.
            config: The site's configuration.
        """
        if not cls.applies(config):
            return
        config.html_theme = cls.theme
        config.html_theme_options = {
            "secondary_sidebar_items": [],
            **config.html_theme_options,
        }
        config.html_static_path = [*config.html_static_path, str(cls.static_dir)]
        app.add_css_file(cls.stylesheet)
        # Before Sphinx's own handler records the root document's tables of contents.
        app.connect("doctree-read", cls.list_vocabularies, priority=400)
        # After sphinx-book-theme fills in its header buttons and page title.
        app.connect("html-page-context", cls.offer_copies, priority=600)
        app.connect("html-page-context", cls.escape_title, priority=600)

    @staticmethod
    def list_vocabularies(app: Sphinx, doctree: nodes.document) -> None:
        """Add every vocabulary to the root document's table of contents, hidden.

        The theme's sidebar is built from the root document's tables of
        contents, so this puts every vocabulary in it on every page. A
        vocabulary the root document already lists is left where it is.

        Args:
            app: The Sphinx application building the site.
            doctree: The document just read.
        """
        if app.env.docname != app.config.root_doc:
            return
        domain = cast(SKOSDomain, app.env.domains["skos"])
        listed = {
            name
            for toctree in doctree.findall(addnodes.toctree)
            for name in toctree["includefiles"]
        }
        vocabularies = [
            uri
            for uri, kind in domain.vocabularies.resources.items()
            if kind == "vocabulary"
        ]
        docnames = [
            docname
            for uri in domain.vocabularies.sort_by_title(
                vocabularies, app.config.language
            )
            if (docname := domain.pages.docname_for(uri)) and docname not in listed
        ]
        if not docnames:
            return
        caption = translate("Vocabularies")
        toctree = addnodes.toctree(
            parent=app.config.root_doc,
            entries=[(None, docname) for docname in docnames],
            includefiles=docnames,
            maxdepth=-1,
            caption=caption,
            rawcaption=caption,
            glob=False,
            hidden=True,
            includehidden=False,
            numbered=0,
            titlesonly=False,
        )
        doctree += nodes.compound("", toctree, classes=["toctree-wrapper"])

    @staticmethod
    def offer_copies(
        app: Sphinx,
        pagename: str,
        templatename: str,
        context: dict[str, Any],
        doctree: Any,
    ) -> None:
        """Offer a generated page's RDF copies in its download menu.

        The copies take the place of the page source. The site's own pages keep
        the theme's menu.

        Args:
            app: The Sphinx application building the site.
            pagename: The document being written.
            templatename: The template the page is rendered with.
            context: The template context, whose ``header_buttons`` the theme
                renders.
            doctree: The document's tree.
        """
        domain = cast(SKOSDomain, app.env.domains["skos"])
        if domain.pages.uri_for(pagename) is None:
            return
        outfile = cast(StandaloneHTMLBuilder, app.builder).get_outfilename(pagename)
        copies = [
            {
                "type": "link",
                "url": path.name,
                "text": copy.suffix,
                "tooltip": copy.media_type,
                "icon": "fas fa-file-code",
                "label": f"download-{copy.suffix[1:]}-button",
            }
            for copy, path in zip(COPY_FORMATS, RdfCopies.paths(outfile), strict=True)
        ]
        for group in context.get("header_buttons", []):
            if group.get("label") == "download-buttons":
                group["buttons"] = copies + [
                    button
                    for button in group["buttons"]
                    if button.get("label") != "download-source-button"
                ]

    @staticmethod
    def escape_title(
        app: Sphinx,
        pagename: str,
        templatename: str,
        context: dict[str, Any],
        doctree: Any,
    ) -> None:
        """Escape the page title sphinx-book-theme writes into the page.

        sphinx-book-theme sets ``pagetitle`` to the title's plain text, and its
        templates write it into the page without escaping it. A title taken
        from a vocabulary's label must reach the page as text.

        Args:
            app: The Sphinx application building the site.
            pagename: The document being written.
            templatename: The template the page is rendered with.
            context: The template context, whose ``pagetitle`` the theme
                writes into the page.
            doctree: The document's tree.
        """
        if "pagetitle" in context and pagename in app.env.titles:
            context["pagetitle"] = escape(app.env.titles[pagename].astext())
