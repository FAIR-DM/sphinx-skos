"""Load the vocabulary files into one graph and read SKOS resources from it."""

import glob
import hashlib
import os
from collections.abc import Sequence
from pathlib import Path
from typing import Literal, NamedTuple

from rdflib import RDF, Graph, Namespace
from rdflib.term import Literal as RDFLiteral
from rdflib.term import URIRef
from sphinx.util import logging

logger = logging.getLogger(__name__)

SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")

type Kind = Literal["vocabulary", "concept", "collection"]
type LabelProperty = Literal["prefLabel", "altLabel"]

# The first kind a URI is typed with wins, in this order.
KIND_TYPES: tuple[tuple[Kind, tuple[URIRef, ...]], ...] = (
    ("vocabulary", (SKOS.ConceptScheme,)),
    ("collection", (SKOS.Collection, SKOS.OrderedCollection)),
    ("concept", (SKOS.Concept,)),
)


class Label(NamedTuple):
    """A piece of text and the language it is written in.

    Attributes:
        text: The text.
        language: The language tag, or an empty string when there is none.
    """

    text: str
    language: str


class Vocabularies:
    """The vocabulary files of a site, merged into one graph.

    Args:
        patterns: Glob patterns naming vocabulary files. A relative pattern is
            read from ``confdir``.
        confdir: The directory holding the site's ``conf.py``.

    Attributes:
        patterns: The glob patterns the files were found with.
        graph: Every statement of every file that could be read.
        fingerprint: A SHA-256 digest of the path and bytes of each file read.
        resources: The kind of each vocabulary, concept and collection, by URI.
    """

    patterns: list[str]
    graph: Graph
    fingerprint: str
    resources: dict[str, Kind]

    def __init__(self, patterns: Sequence[str], confdir: str | Path) -> None:
        self.patterns = list(patterns)
        self.graph = Graph()
        digest = hashlib.sha256()
        for path in self.find_files(patterns, confdir):
            data = path.read_bytes() if path.is_file() else None
            if data is not None and self.load(path, data):
                digest.update(str(path).encode())
                digest.update(data)
        self.fingerprint = digest.hexdigest()
        self.resources = self.find_resources()

    @staticmethod
    def find_files(patterns: Sequence[str], confdir: str | Path) -> list[Path]:
        """Return the files the patterns match, each pattern's matches sorted.

        A pattern matching nothing is named in a warning. A file matched twice
        is returned once.

        Args:
            patterns: Glob patterns, relative ones to be read from ``confdir``.
            confdir: The directory holding the site's ``conf.py``.

        Returns:
            The matched paths, in pattern order.
        """
        found: dict[Path, None] = {}
        for pattern in patterns:
            matches = sorted(glob.glob(os.path.join(confdir, pattern), recursive=True))
            if not matches:
                logger.warning("skos_vocabularies matches no file: %s", pattern)
            for match in matches:
                found.setdefault(Path(match), None)
        return list(found)

    def load(self, path: Path, data: bytes) -> bool:
        """Add one file's statements to the graph if the file is Turtle.

        A file that fails to parse adds nothing and is named in a warning.

        Args:
            path: The file, for the warning and for relative URIs in it.
            data: The file's bytes.

        Returns:
            Whether the file was added.
        """
        single = Graph()
        try:
            single.parse(data=data, format="turtle", publicID=path.as_uri())
        except Exception as error:
            logger.warning("Cannot read vocabulary file %s: %s", path, error)
            return False
        self.graph += single
        return True

    def find_resources(self) -> dict[str, Kind]:
        """Return every typed vocabulary, concept and collection by URI.

        Returns:
            Each resource's URI mapped to its kind.
        """
        resources: dict[str, Kind] = {}
        for kind, types in reversed(KIND_TYPES):
            for type_ in types:
                for subject in self.graph.subjects(RDF.type, type_):
                    if isinstance(subject, URIRef):
                        resources[str(subject)] = kind
        return resources

    def title(self, uri: str, language: str) -> str:
        """Return the title of a resource.

        The title is the preferred label in ``language``. Failing that it is
        the first preferred label by language tag, then text. Failing that it
        is the URI.

        Args:
            uri: The resource's URI.
            language: The site's ``language`` setting.

        Returns:
            The text to title the resource's page and links to it with.
        """
        labels = self.labels(uri, "prefLabel")
        for label in labels:
            if label.language.lower() == language.lower():
                return label.text
        return labels[0].text if labels else uri

    def labels(self, uri: str, property_: LabelProperty) -> list[Label]:
        """Return the preferred or alternative labels of a resource.

        Hidden labels are never returned.

        Args:
            uri: The resource's URI.
            property_: Which labels to read, ``"prefLabel"`` or ``"altLabel"``.

        Returns:
            The labels, sorted by language tag and then text.
        """
        return self.read_literals(uri, SKOS[property_])

    def definitions(self, uri: str) -> list[Label]:
        """Return the definitions of a resource.

        Args:
            uri: The resource's URI.

        Returns:
            The definitions, sorted by language tag and then text.
        """
        return self.read_literals(uri, SKOS.definition)

    def notations(self, uri: str) -> list[str]:
        """Return the notations of a resource.

        Args:
            uri: The resource's URI.

        Returns:
            The notations, sorted.
        """
        return sorted(label.text for label in self.read_literals(uri, SKOS.notation))

    def read_literals(self, uri: str, predicate: URIRef) -> list[Label]:
        """Return the literal objects of one property of a resource.

        Args:
            uri: The resource's URI.
            predicate: The property to read.

        Returns:
            The literals, sorted by language tag and then text.
        """
        return sorted(
            (
                Label(str(value), value.language or "")
                for value in self.graph.objects(URIRef(uri), predicate)
                if isinstance(value, RDFLiteral)
            ),
            key=lambda label: (label.language, label.text),
        )
