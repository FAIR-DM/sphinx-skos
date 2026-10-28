"""Load the vocabulary files into one graph and read SKOS resources from it."""

import glob
import hashlib
import os
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Literal, NamedTuple

from rdflib import DCTERMS, RDF, Graph, Namespace
from rdflib.term import Literal as RDFLiteral
from rdflib.term import URIRef
from sphinx.util import logging

logger = logging.getLogger(__name__)

SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")

type Kind = Literal["vocabulary", "concept", "collection"]
type LabelProperty = Literal["prefLabel", "altLabel"]
type RelationProperty = Literal["broader", "narrower", "related"]

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


# A relation as (the property that states it, the property that states it
# from the other concept).
RELATIONS: dict[RelationProperty, tuple[URIRef, URIRef]] = {
    "broader": (SKOS.broader, SKOS.narrower),
    "narrower": (SKOS.narrower, SKOS.broader),
    "related": (SKOS.related, SKOS.related),
}
MAPPING_PROPERTIES = (
    "exactMatch",
    "closeMatch",
    "broadMatch",
    "narrowMatch",
    "relatedMatch",
)


class Target(NamedTuple):
    """What a mapping link points at.

    Attributes:
        value: The URI, or the text of a literal written where a URI belongs.
        is_uri: Whether ``value`` is a URI.
    """

    value: str
    is_uri: bool


class Vocabularies:
    """The vocabulary files of a site, merged into one graph.

    Args:
        patterns: Glob patterns naming vocabulary files. A relative pattern is
            read from ``confdir``.
        confdir: The directory holding the site's ``conf.py``.
        base_uri: The ``skos_base_uri`` setting. A relative IRI in a file is
            resolved against it. When it is empty, relative IRIs stay relative.

    Attributes:
        patterns: The glob patterns the files were found with.
        base_uri: The base URI relative IRIs are resolved against.
        graph: Every statement of every file that could be read.
        fingerprint: A SHA-256 digest of the path and bytes of each file read.
        resources: The kind of each vocabulary, concept and collection, by URI.
    """

    patterns: list[str]
    base_uri: str
    graph: Graph
    fingerprint: str
    resources: dict[str, Kind]

    def __init__(
        self, patterns: Sequence[str], confdir: str | Path, base_uri: str = ""
    ) -> None:
        self.patterns = list(patterns)
        self.base_uri = base_uri
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
            path: The file, for the warning.
            data: The file's bytes.

        Returns:
            Whether the file was added.
        """
        single = Graph()
        try:
            single.parse(data=data, format="turtle", publicID=self.base_uri or None)
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

    def own_rdf(self, uri: str) -> Graph:
        """Return a resource's own RDF.

        That is every triple with the resource as subject, and the triples of
        the blank nodes those reach. Statements other resources make about it
        are left out.

        Args:
            uri: The resource's URI.

        Returns:
            A graph holding those triples and the files' namespace prefixes.
        """
        own = Graph()
        for prefix, namespace in self.graph.namespaces():
            own.bind(prefix, namespace)
        return self.graph.cbd(URIRef(uri), target_graph=own, include_reifications=False)

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

    def descriptions(self, uri: str) -> list[Label]:
        """Return the ``dcterms:description`` texts of a resource.

        Args:
            uri: The resource's URI.

        Returns:
            The descriptions, sorted by language tag and then text.
        """
        return self.read_literals(uri, DCTERMS.description)

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

    def sort_by_title(self, uris: Iterable[str], language: str) -> list[str]:
        """Return URIs once each, ordered by title and then URI.

        Args:
            uris: The URIs to order.
            language: The site's ``language`` setting.

        Returns:
            The distinct URIs, in the order every list of resources is shown in.
        """
        return sorted(set(uris), key=lambda uri: (self.title(uri, language), uri))

    def uri_objects(self, subject: str, predicate: URIRef) -> set[str]:
        """Return the URIs a resource's property points at.

        Args:
            subject: The resource's URI.
            predicate: The property to read.

        Returns:
            The objects that are URIs. Literals and blank nodes are left out.
        """
        return {
            str(value)
            for value in self.graph.objects(URIRef(subject), predicate)
            if isinstance(value, URIRef)
        }

    def uri_subjects(self, predicate: URIRef, object_: str) -> set[str]:
        """Return the URIs whose property points at a resource.

        Args:
            predicate: The property to read.
            object_: The URI pointed at.

        Returns:
            The subjects that are URIs.
        """
        return {
            str(value)
            for value in self.graph.subjects(predicate, URIRef(object_))
            if isinstance(value, URIRef)
        }

    def vocabularies_of(self, concept: str, language: str) -> list[str]:
        """Return the vocabularies a concept is in.

        A concept is in a vocabulary when it states ``skos:inScheme`` or
        ``skos:topConceptOf`` for it, or the vocabulary states
        ``skos:hasTopConcept`` for the concept.

        Args:
            concept: The concept's URI.
            language: The site's ``language`` setting.

        Returns:
            The vocabularies' URIs, sorted by title and then URI.
        """
        return self.sort_by_title(
            self.uri_objects(concept, SKOS.inScheme)
            | self.uri_objects(concept, SKOS.topConceptOf)
            | self.uri_subjects(SKOS.hasTopConcept, concept),
            language,
        )

    def listed_members(self, collection: str) -> list[str]:
        """Return the members an ordered collection lists, in list order.

        A list that comes back round to itself is read up to that point and the
        collection is named in a warning.

        Args:
            collection: The collection's URI.

        Returns:
            The listed URIs, each once. Empty without a ``skos:memberList``.
        """
        node = self.graph.value(URIRef(collection), SKOS.memberList)
        members: dict[str, None] = {}
        seen = set()
        while node is not None and node != RDF.nil:
            if node in seen:
                logger.warning("The member list of %s comes back round", collection)
                break
            seen.add(node)
            item = self.graph.value(node, RDF.first)
            if isinstance(item, URIRef):
                members.setdefault(str(item), None)
            node = self.graph.value(node, RDF.rest)
        return list(members)

    def all_members(self, collection: str) -> set[str]:
        """Return every concept a collection names, listed or not.

        Args:
            collection: The collection's URI.

        Returns:
            The URIs named by ``skos:member`` or ``skos:memberList``.
        """
        return set(self.listed_members(collection)) | self.uri_objects(
            collection, SKOS.member
        )

    def collections_of(self, concept: str, language: str) -> list[str]:
        """Return the collections that name a concept as a member.

        Args:
            concept: The concept's URI.
            language: The site's ``language`` setting.

        Returns:
            The collections' URIs, sorted by title and then URI.
        """
        return self.sort_by_title(
            (
                uri
                for uri, kind in self.resources.items()
                if kind == "collection" and concept in self.all_members(uri)
            ),
            language,
        )

    def relations(
        self, concept: str, property_: RelationProperty, language: str
    ) -> list[str]:
        """Return the concepts related to a concept, whichever one states it.

        Args:
            concept: The concept's URI.
            property_: ``"broader"``, ``"narrower"`` or ``"related"``.
            language: The site's ``language`` setting.

        Returns:
            The concepts' URIs, sorted by title and then URI.
        """
        own, inverse = RELATIONS[property_]
        return self.sort_by_title(
            self.uri_objects(concept, own) | self.uri_subjects(inverse, concept),
            language,
        )

    def mappings(self, concept: str, language: str) -> list[tuple[str, list[Target]]]:
        """Return the mapping links a concept states, for each property used.

        Args:
            concept: The concept's URI.
            language: The site's ``language`` setting.

        Returns:
            Each mapping property the concept uses, in the order SKOS lists
            them, with its targets: URIs sorted by title and then URI, then any
            literals sorted by text.
        """
        found = []
        for name in MAPPING_PROPERTIES:
            values = list(self.graph.objects(URIRef(concept), SKOS[name]))
            uris = self.sort_by_title(
                (str(value) for value in values if isinstance(value, URIRef)),
                language,
            )
            texts = sorted(
                {str(value) for value in values if isinstance(value, RDFLiteral)}
            )
            targets = [Target(uri, True) for uri in uris]
            targets += [Target(text, False) for text in texts]
            if targets:
                found.append((name, targets))
        return found

    def concepts_in(self, vocabulary: str, language: str) -> list[str]:
        """Return the concepts in a vocabulary.

        Args:
            vocabulary: The vocabulary's URI.
            language: The site's ``language`` setting.

        Returns:
            The concepts that state ``skos:inScheme`` or ``skos:topConceptOf``
            for the vocabulary or that it names with ``skos:hasTopConcept``,
            sorted by title and then URI.
        """
        named = (
            self.uri_subjects(SKOS.inScheme, vocabulary)
            | self.uri_subjects(SKOS.topConceptOf, vocabulary)
            | self.uri_objects(vocabulary, SKOS.hasTopConcept)
        )
        return self.sort_by_title(
            (uri for uri in named if self.resources.get(uri) == "concept"), language
        )

    def collections_in(self, vocabulary: str, language: str) -> list[str]:
        """Return the collections in a vocabulary.

        Args:
            vocabulary: The vocabulary's URI.
            language: The site's ``language`` setting.

        Returns:
            The collections that state ``skos:inScheme`` for the vocabulary or
            have a member that is a concept in it, sorted by title and then URI.
        """
        concepts = set(self.concepts_in(vocabulary, language))
        stated = self.uri_subjects(SKOS.inScheme, vocabulary)
        return self.sort_by_title(
            (
                uri
                for uri, kind in self.resources.items()
                if kind == "collection"
                and (uri in stated or concepts & self.all_members(uri))
            ),
            language,
        )

    def members_of(self, collection: str, language: str) -> list[str]:
        """Return the members of a collection.

        Args:
            collection: The collection's URI.
            language: The site's ``language`` setting.

        Returns:
            The members of an ordered collection in list order, followed by any
            other ``skos:member``. Members of an unordered collection are
            sorted by title and then URI.
        """
        listed = self.listed_members(collection)
        others = self.uri_objects(collection, SKOS.member) - set(listed)
        return [*listed, *self.sort_by_title(others, language)]
