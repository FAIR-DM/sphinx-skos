"""The directives that turn a resource's URI into content."""

import re
from typing import TYPE_CHECKING, ClassVar, cast

from docutils import nodes
from sphinx import addnodes
from sphinx.locale import get_translation
from sphinx.util import logging
from sphinx.util.docutils import SphinxDirective

from sphinx_skos.vocabularies import Kind, Label, Target, Vocabularies

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


class ResourceDirective(SphinxDirective):
    """Show the resource whose URI is the directive's argument."""

    required_arguments = 1
    optional_arguments = 0
    has_content = False
    kind: ClassVar[Kind]

    @property
    def vocabularies(self) -> Vocabularies:
        """The vocabularies of the build in progress."""
        return cast("SKOSDomain", self.env.domains["skos"]).vocabularies

    @property
    def pages(self) -> "GeneratedPages":
        """The generated pages of the build in progress."""
        return cast("SKOSDomain", self.env.domains["skos"]).pages

    def run(self) -> list[nodes.Node]:
        """Return a section titled with the resource, or warn why not."""
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
        return [section]

    def fields(self, uri: str) -> nodes.field_list:
        """Return the facts of the resource, one field for each kind of fact.

        Args:
            uri: The resource's URI.

        Returns:
            A field list with a field only where the resource has a value,
            except the URI, which is always there.
        """
        field_list = nodes.field_list(
            "", self.field(translate("URI"), [nodes.Text(uri)])
        )
        field_list += [
            self.field(name, *values) for name, values in self.facts(uri) if values
        ]
        return field_list

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
        ]

    def link(self, uri: str) -> list[nodes.Node]:
        """Return the nodes that show a resource and, where safe, link to it.

        Args:
            uri: The URI to show.

        Returns:
            A cross-reference to the page of the resource when it has one,
            else a link to the URI, else plain text for a URI that runs code or
            carries data when followed.
        """
        scheme = SCHEME.match(IGNORED_BY_BROWSERS.sub("", uri))
        if scheme and scheme.group(1).lower() in UNLINKED_SCHEMES:
            return [nodes.Text(uri)]
        docname = self.pages.docname_for(uri)
        if docname is None:
            return [nodes.reference("", uri, refuri=uri)]
        title = self.vocabularies.title(uri, self.config.language)
        return [
            addnodes.pending_xref(
                "",
                nodes.Text(title),
                refdomain="std",
                reftype="doc",
                reftarget="/" + docname,
                refexplicit=True,
            )
        ]

    def links(self, uris: list[str]) -> list[list[nodes.Node]]:
        """Return the nodes of a link for each URI.

        Args:
            uris: The URIs to show.

        Returns:
            One list of nodes for each URI, from :meth:`link`.
        """
        return [self.link(uri) for uri in uris]

    def field(self, name: str, *values: list[nodes.Node]) -> nodes.field:
        """Return a field with one paragraph for each value.

        Args:
            name: The field's name, already translated.
            *values: The nodes of each paragraph.

        Returns:
            The field.
        """
        paragraphs = [nodes.paragraph("", "", *value) for value in values]
        return nodes.field(
            "", nodes.field_name("", name), nodes.field_body("", *paragraphs)
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


class ConceptDirective(ResourceDirective):
    """Show a concept."""

    kind = "concept"

    def facts(self, uri: str) -> Facts:
        """Add the notations and the links of the concept.

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
                translate("Notations"),
                [[nodes.Text(text)] for text in vocabularies.notations(uri)],
            ),
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
