"""The directives that turn a resource's URI into content."""

import re
from os.path import relpath
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, cast

from docutils import nodes
from rdflib import DCTERMS, OWL, RDFS
from rdflib.term import BNode, Node, URIRef
from rdflib.term import Literal as RDFLiteral
from sphinx import addnodes
from sphinx.builders.html import StandaloneHTMLBuilder
from sphinx.locale import get_translation
from sphinx.transforms.post_transforms import SphinxPostTransform
from sphinx.util import logging
from sphinx.util.docutils import SphinxDirective

from sphinx_skos.copies import COPY_FORMATS, RdfCopies
from sphinx_skos.vocabularies import (
    MAPPING_PROPERTIES,
    SKOS,
    Kind,
    Label,
    Target,
    Vocabularies,
)

if TYPE_CHECKING:
    from sphinx_skos.domain import SKOSDomain
    from sphinx_skos.pages import GeneratedPages

logger = logging.getLogger(__name__)
translate = get_translation("sphinx_skos")

# Browsers run or render these when followed, so they are shown, never linked.
UNLINKED_SCHEMES = ("javascript", "data", "vbscript")
SCHEME = re.compile(r"([A-Za-z][A-Za-z0-9+.-]*):")
IGNORED_BY_BROWSERS = re.compile(r"[\x00-\x20]")

type Facts = list[tuple[str, list[list[nodes.Node]]]]
type Properties = list[tuple[str, URIRef]]


class ResourceDirective(SphinxDirective):
    """Show the resource whose URI is the directive's argument."""

    required_arguments = 1
    optional_arguments = 0
    has_content = True
    kind: ClassVar[Kind]
    # The properties the kind's own fields show, which the other properties
    # leave out.
    shown: ClassVar[frozenset[URIRef]] = frozenset(
        {SKOS.prefLabel, SKOS.altLabel, SKOS.definition}
    )

    @property
    def vocabularies(self) -> Vocabularies:
        """The vocabularies of the build in progress."""
        return cast("SKOSDomain", self.env.domains["skos"]).vocabularies

    @property
    def pages(self) -> "GeneratedPages":
        """The generated pages of the build in progress."""
        return cast("SKOSDomain", self.env.domains["skos"]).pages

    def run(self) -> list[nodes.Node]:
        """Return a section titled with the resource, or warn why not.

        The directive's content is parsed into the section, after the fields,
        so a table of contents in it nests under the resource's title.
        """
        uri = self.arguments[0]
        vocabularies = self.vocabularies
        if vocabularies.resources.get(uri) != self.kind:
            logger.warning(
                "%s is not a %s in the vocabulary files",
                uri,
                self.kind,
                location=self.get_location(),
            )
            return []
        title = vocabularies.title(uri, self.config.language)
        section = nodes.section()
        section += nodes.title("", title)
        section["names"].append(nodes.fully_normalize_name(title))
        self.state.document.note_implicit_target(section)
        section += self.fields(uri)
        section += self.parse_content_to_nodes()
        return [section]

    def fields(self, uri: str) -> nodes.field_list:
        """Return the statements of the resource, one field for each kind of fact.

        Args:
            uri: The resource's URI.

        Returns:
            A field list with the URI, then the facts of the resource, then its
            metadata, then every other property it states. A field is there
            only where the resource has a value, except the URI, which always
            is.
        """
        subject = URIRef(uri)
        field_list = nodes.field_list(
            "", self.field(translate("URI"), [nodes.Text(uri)])
        )
        facts = [
            *self.facts(uri),
            *self.property_facts(subject, self.metadata_properties()),
        ]
        field_list += [self.field(name, *values) for name, values in facts if values]
        shown = (
            ResourceDirective.shown
            | self.shown
            | {
                predicate
                for _, predicate in (
                    *self.text_properties(),
                    *self.metadata_properties(),
                )
            }
        )
        field_list += self.other_fields(subject, shown, frozenset())
        if self.pages.uri_for(self.env.docname) == uri:
            field_list += self.download_field()
        return field_list

    def download_field(self) -> nodes.field:
        """Return the field that links a generated page's RDF files.

        Each link names its format by suffix and has no target: the builder
        that writes the page decides where the files are.

        Returns:
            A field with one link for each format.
        """
        links: list[list[nodes.Node]] = [
            [nodes.reference("", copy.label, internal=True, skos_suffix=copy.suffix)]
            for copy in COPY_FORMATS
        ]
        field = self.field(translate("Download"), *links)
        field["skos_download"] = True
        return field

    def facts(self, uri: str) -> Facts:
        """Return the facts every resource has, after its URI.

        Args:
            uri: The resource's URI.

        Returns:
            The name and the paragraphs of each fact, in the order shown.
        """
        vocabularies = self.vocabularies
        return [
            (
                translate("Preferred labels"),
                self.label_values(vocabularies.labels(uri, "prefLabel")),
            ),
            (
                translate("Alternative labels"),
                self.label_values(vocabularies.labels(uri, "altLabel")),
            ),
            (
                translate("Definitions"),
                self.label_values(vocabularies.definitions(uri)),
            ),
            *self.property_facts(URIRef(uri), self.text_properties()),
        ]

    def text_properties(self) -> Properties:
        """Return the properties that say what a resource is, shown after its labels.

        Returns:
            The name of each field and the property it shows.
        """
        return [
            (translate("Titles"), DCTERMS.title),
            (translate("Descriptions"), DCTERMS.description),
            (translate("Notations"), SKOS.notation),
            (translate("Scope notes"), SKOS.scopeNote),
            (translate("Notes"), SKOS.note),
            (translate("Examples"), SKOS.example),
            (translate("History notes"), SKOS.historyNote),
            (translate("Editorial notes"), SKOS.editorialNote),
            (translate("Change notes"), SKOS.changeNote),
        ]

    def metadata_properties(self) -> Properties:
        """Return the properties that say who made a resource, when and on what terms.

        Returns:
            The name of each field and the property it shows.
        """
        return [
            (translate("Creators"), DCTERMS.creator),
            (translate("Contributors"), DCTERMS.contributor),
            (translate("Publishers"), DCTERMS.publisher),
            (translate("Created"), DCTERMS.created),
            (translate("Issued"), DCTERMS.issued),
            (translate("Modified"), DCTERMS.modified),
            (translate("Version"), OWL.versionInfo),
            (translate("Licence"), DCTERMS.license),
            (translate("Rights"), DCTERMS.rights),
            (translate("Identifiers"), DCTERMS.identifier),
            (translate("Languages"), DCTERMS.language),
            (translate("Sources"), DCTERMS.source),
            (translate("Citations"), DCTERMS.bibliographicCitation),
            (translate("See also"), RDFS.seeAlso),
        ]

    def property_facts(self, subject: URIRef, properties: Properties) -> Facts:
        """Return a fact for each property, holding what the resource states.

        Args:
            subject: The resource's URI.
            properties: The name of each fact and the property it shows.

        Returns:
            The name and the paragraphs of each fact.
        """
        statements = self.vocabularies.statements(subject)
        return [
            (name, self.values(statements.get(predicate, []), frozenset()))
            for name, predicate in properties
        ]

    def other_fields(
        self, subject: Node, shown: frozenset[URIRef], seen: frozenset[BNode]
    ) -> list[nodes.field]:
        """Return a field for each property no other field shows.

        Each field is named by the property's prefixed name, linked to the
        property's URI.

        Args:
            subject: The resource's URI, or a blank node it reaches.
            shown: The properties left out, because other fields show them.
            seen: The blank nodes already being shown, so a cycle ends.

        Returns:
            The fields, sorted by prefixed name and then URI.
        """
        vocabularies = self.vocabularies
        statements = vocabularies.statements(subject)
        predicates = sorted(
            (predicate for predicate in statements if predicate not in shown),
            key=lambda predicate: (vocabularies.curie(predicate), str(predicate)),
        )
        return [
            self.field(
                self.uri_reference(str(predicate), vocabularies.curie(predicate)),
                *self.values(statements[predicate], seen),
            )
            for predicate in predicates
        ]

    def values(
        self, values: list[Node], seen: frozenset[BNode]
    ) -> list[list[nodes.Node]]:
        """Return the nodes that show each object of a property.

        Args:
            values: The objects.
            seen: The blank nodes already being shown, so a cycle ends.

        Returns:
            For each object in the order shown: a link for a URI, the text and
            then the language tag or datatype for a literal, and a field list
            of its own statements for a blank node.
        """
        shown = []
        for value in self.vocabularies.sort_values(values, self.config.language):
            if isinstance(value, URIRef):
                shown.append(self.link(str(value)))
            elif isinstance(value, RDFLiteral):
                shown.append(self.literal_value(value))
            elif isinstance(value, BNode) and value not in seen:
                fields = self.other_fields(value, frozenset(), seen | {value})
                shown.append([nodes.field_list("", *fields)])
        return shown

    def literal_value(self, literal: RDFLiteral) -> list[nodes.Node]:
        """Return the text of a literal, then its language tag or datatype.

        Args:
            literal: The literal.

        Returns:
            The text, followed by the tag in a text node of its own when the
            literal has one.
        """
        text = nodes.Text(str(literal))
        if literal.language:
            return [text, nodes.Text(f" ({literal.language})")]
        if literal.datatype:
            datatype = self.vocabularies.curie(str(literal.datatype))
            return [text, nodes.Text(f" ({datatype})")]
        return [text]

    def link(self, uri: str) -> list[nodes.Node]:
        """Return the nodes that show a resource and, where safe, link to it.

        Args:
            uri: The URI to show.

        Returns:
            A cross-reference to the page of the resource when it has one,
            else a link to the URI by the name the files give it, else plain
            text for a URI that runs code or carries data when followed.
        """
        name = self.vocabularies.name(uri, self.config.language)
        docname = self.pages.docname_for(uri)
        if docname is None:
            return [self.uri_reference(uri, name)]
        return [
            addnodes.pending_xref(
                "",
                nodes.Text(name),
                refdomain="std",
                reftype="doc",
                reftarget="/" + docname,
                refexplicit=True,
            )
        ]

    def uri_reference(self, uri: str, text: str) -> nodes.Node:
        """Return a link to a URI, or plain text where following it is unsafe.

        Args:
            uri: The URI to link to.
            text: The text to show.

        Returns:
            A reference, or the text alone for a URI that runs code or carries
            data when followed.
        """
        scheme = SCHEME.match(IGNORED_BY_BROWSERS.sub("", uri))
        if scheme and scheme.group(1).lower() in UNLINKED_SCHEMES:
            return nodes.Text(text)
        return nodes.reference("", text, refuri=uri)

    def links(self, uris: list[str]) -> list[list[nodes.Node]]:
        """Return the nodes of a link for each URI.

        Args:
            uris: The URIs to show.

        Returns:
            One list of nodes for each URI, from :meth:`link`.
        """
        return [self.link(uri) for uri in uris]

    def field(self, name: str | nodes.Node, *values: list[nodes.Node]) -> nodes.field:
        """Return a field with one paragraph for each value.

        Args:
            name: The field's name, already translated, or the nodes of a link.
            *values: The nodes of each paragraph. A value that is a field list
                or a bullet list is placed as it is, not in a paragraph.

        Returns:
            The field.
        """
        body = [
            value[0]
            if len(value) == 1
            and isinstance(value[0], nodes.field_list | nodes.bullet_list)
            else nodes.paragraph("", "", *value)
            for value in values
        ]
        title = name if isinstance(name, nodes.Node) else nodes.Text(name)
        return nodes.field(
            "", nodes.field_name("", "", title), nodes.field_body("", *body)
        )

    def target_links(self, targets: list[Target]) -> list[list[nodes.Node]]:
        """Return the nodes of a link for each target of a mapping link.

        Args:
            targets: The targets to show.

        Returns:
            One list of nodes for each target: a link for a URI, the text for a
            literal written where a URI belongs.
        """
        return [
            self.link(target.value) if target.is_uri else [nodes.Text(target.value)]
            for target in targets
        ]

    def label_values(self, labels: list[Label]) -> list[list[nodes.Node]]:
        """Return the paragraph content of each label, with its language.

        Args:
            labels: The labels to show.

        Returns:
            For each label its text, followed by its language tag in a text
            node of its own when it has one.
        """
        return [
            [nodes.Text(label.text), nodes.Text(f" ({label.language})")]
            if label.language
            else [nodes.Text(label.text)]
            for label in labels
        ]


class VocabularyDirective(ResourceDirective):
    """Show a vocabulary."""

    kind = "vocabulary"
    shown = frozenset({SKOS.hasTopConcept})

    def facts(self, uri: str) -> Facts:
        """Add the concepts and collections of the vocabulary.

        Args:
            uri: The vocabulary's URI.

        Returns:
            The vocabulary's facts.
        """
        vocabularies = self.vocabularies
        language = self.config.language
        return [
            *super().facts(uri),
            (
                translate("Concepts"),
                self.links(vocabularies.concepts_in(uri, language)),
            ),
            (
                translate("Collections"),
                self.links(vocabularies.collections_in(uri, language)),
            ),
            (translate("Namespace prefixes"), self.prefix_list(uri)),
        ]

    def prefix_list(self, uri: str) -> list[list[nodes.Node]]:
        """Return a bullet list of the namespace prefixes the vocabulary declares.

        Args:
            uri: The vocabulary's URI.

        Returns:
            The list as the one value of a field, or nothing when the files of
            the vocabulary declare no prefix. Each item is the prefix and a
            colon, then a link to the namespace.
        """
        prefixes = self.vocabularies.declared_prefixes(uri, self.config.language)
        if not prefixes:
            return []
        items = [
            nodes.list_item(
                "",
                nodes.paragraph(
                    "",
                    "",
                    nodes.Text(f"{prefix}: "),
                    self.uri_reference(str(namespace), str(namespace)),
                ),
            )
            for prefix, namespace in prefixes
        ]
        return [[nodes.bullet_list("", *items)]]


class ConceptDirective(ResourceDirective):
    """Show a concept."""

    kind = "concept"
    shown = frozenset(
        {
            SKOS.inScheme,
            SKOS.topConceptOf,
            SKOS.broader,
            SKOS.narrower,
            SKOS.related,
            *(SKOS[name] for name in MAPPING_PROPERTIES),
        }
    )

    def facts(self, uri: str) -> Facts:
        """Add the links of the concept.

        Args:
            uri: The concept's URI.

        Returns:
            The concept's facts.
        """
        vocabularies = self.vocabularies
        language = self.config.language
        mappings = {
            "exactMatch": translate("Exact match"),
            "closeMatch": translate("Close match"),
            "broadMatch": translate("Broad match"),
            "narrowMatch": translate("Narrow match"),
            "relatedMatch": translate("Related match"),
        }
        return [
            *super().facts(uri),
            (
                translate("Vocabulary"),
                self.links(vocabularies.vocabularies_of(uri, language)),
            ),
            (
                translate("Collections"),
                self.links(vocabularies.collections_of(uri, language)),
            ),
            (
                translate("Broader"),
                self.links(vocabularies.relations(uri, "broader", language)),
            ),
            (
                translate("Narrower"),
                self.links(vocabularies.relations(uri, "narrower", language)),
            ),
            (
                translate("Related"),
                self.links(vocabularies.relations(uri, "related", language)),
            ),
            *[
                (mappings[name], self.target_links(targets))
                for name, targets in vocabularies.mappings(uri, language)
            ],
        ]


class CollectionDirective(ResourceDirective):
    """Show a collection."""

    kind = "collection"
    shown = frozenset({SKOS.member, SKOS.memberList})

    def facts(self, uri: str) -> Facts:
        """Add the members of the collection.

        Args:
            uri: The collection's URI.

        Returns:
            The collection's facts.
        """
        members = self.vocabularies.members_of(uri, self.config.language)
        return [*super().facts(uri), (translate("Members"), self.links(members))]


PAGE_BUILDERS = ("html", "dirhtml")


class DownloadLinks(SphinxPostTransform):
    """Point the download links of a generated page at the files they name.

    The field is removed under a builder that does not write a page per
    document, because the copies are written only beside such pages. A
    vocabulary's page links its whole files under ``dirhtml`` and its own
    copies otherwise; any other page links its own copies.
    """

    default_priority: ClassVar[int] = 10

    def run(self, **kwargs: object) -> None:
        """Set the target of each download link, or remove the field.

        Args:
            **kwargs: Passed on by Sphinx, unused.
        """
        fields = [
            field
            for field in self.document.findall(nodes.field)
            if field.get("skos_download")
        ]
        # Sphinx's own post-transforms read the builder this way: the public
        # ``app`` properties are deprecated.
        builder = self.env._app.builder
        if builder.name not in PAGE_BUILDERS:
            for field in fields:
                field.parent.remove(field)
            return
        docname = self.env.current_document.docname
        domain = cast("SKOSDomain", self.env.domains["skos"])
        uri = domain.pages.uri_for(docname) or ""
        outfile = Path(cast(StandaloneHTMLBuilder, builder).get_outfilename(docname))
        if builder.name == "dirhtml" and domain.vocabularies.resources.get(uri) == (
            "vocabulary"
        ):
            files = RdfCopies.whole_paths(builder.outdir, docname)
        else:
            files = RdfCopies.paths(outfile)
        targets = {
            copy.suffix: Path(relpath(path, outfile.parent)).as_posix()
            for copy, path in zip(COPY_FORMATS, files, strict=True)
        }
        for field in fields:
            for reference in field.findall(nodes.reference):
                reference["refuri"] = targets[reference["skos_suffix"]]
