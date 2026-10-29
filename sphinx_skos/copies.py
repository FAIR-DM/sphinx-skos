"""Write the RDF copies beside a page and name them in the page's head."""

from html import escape
from pathlib import Path
from typing import NamedTuple

from sphinx_skos.vocabularies import Vocabularies


class CopyFormat(NamedTuple):
    """One format an RDF copy is written in.

    Attributes:
        suffix: The file suffix that replaces the page's ``.html``.
        rdflib_format: The name rdflib serialises the format with.
        media_type: The media type of the format.
    """

    suffix: str
    rdflib_format: str
    media_type: str


COPY_FORMATS = (
    CopyFormat(".ttl", "turtle", "text/turtle"),
    CopyFormat(".jsonld", "json-ld", "application/ld+json"),
    CopyFormat(".rdf", "xml", "application/rdf+xml"),
    CopyFormat(".nt", "nt", "application/n-triples"),
)


class RdfCopies:
    """The RDF copies of a resource, written beside its page.

    A copy is named after the page's output file with its suffix replaced, so
    its address depends only on the page address and the format.

    Args:
        vocabularies: The site's vocabulary files.
    """

    def __init__(self, vocabularies: Vocabularies) -> None:
        self.vocabularies = vocabularies

    @staticmethod
    def paths(outfile: str | Path) -> list[Path]:
        """Return where the copies of a page are, whether or not they exist.

        Args:
            outfile: The page's output file.

        Returns:
            One path for each format, beside the page.
        """
        page = Path(outfile)
        return [page.with_suffix(copy.suffix) for copy in COPY_FORMATS]

    @staticmethod
    def whole_paths(outdir: str | Path, docname: str) -> list[Path]:
        """Return where the whole-vocabulary files of a page are.

        Args:
            outdir: The builder's output directory.
            docname: The vocabulary's document name.

        Returns:
            One path for each format, named after the page's directory and
            sitting beside it, whether or not the files exist.
        """
        stem = docname.removesuffix("/index")
        return [Path(outdir) / f"{stem}{copy.suffix}" for copy in COPY_FORMATS]

    def write_whole(
        self, uri: str, outdir: str | Path, docname: str, language: str
    ) -> None:
        """Write the graph of a vocabulary's files in every format.

        Args:
            uri: The vocabulary's URI.
            outdir: The builder's output directory.
            docname: The vocabulary's document name.
            language: The site's ``language`` setting.
        """
        graph = self.vocabularies.vocabulary_graph(uri, language)
        for copy, path in zip(
            COPY_FORMATS, self.whole_paths(outdir, docname), strict=True
        ):
            path.parent.mkdir(parents=True, exist_ok=True)
            graph.serialize(
                destination=path, format=copy.rdflib_format, encoding="utf-8"
            )

    def write(self, uri: str, outfile: str | Path) -> None:
        """Write a resource's own RDF in every format beside its page.

        Args:
            uri: The resource's URI.
            outfile: The page's output file.
        """
        graph = self.vocabularies.own_rdf(uri)
        for copy, path in zip(COPY_FORMATS, self.paths(outfile), strict=True):
            path.parent.mkdir(parents=True, exist_ok=True)
            graph.serialize(
                destination=path, format=copy.rdflib_format, encoding="utf-8"
            )

    @staticmethod
    def alternate_links(outfile: str | Path) -> str:
        """Return the head elements that name a page's copies.

        Args:
            outfile: The page's output file.

        Returns:
            One ``<link rel="alternate">`` element for each copy, each ending
            in a newline.
        """
        return "".join(
            f'<link rel="alternate" type="{escape(copy.media_type, quote=True)}" '
            f'href="{escape(path.name, quote=True)}">\n'
            for copy, path in zip(COPY_FORMATS, RdfCopies.paths(outfile), strict=True)
        )
