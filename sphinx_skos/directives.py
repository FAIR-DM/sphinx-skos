"""The directives that turn a resource's URI into content."""

from typing import TYPE_CHECKING, ClassVar, cast

from docutils import nodes
from sphinx.locale import get_translation
from sphinx.util import logging
from sphinx.util.docutils import SphinxDirective

from sphinx_skos.vocabularies import Kind, Label, Vocabularies

if TYPE_CHECKING:
    from sphinx_skos.domain import SKOSDomain

logger = logging.getLogger(__name__)
translate = get_translation("sphinx_skos")


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
        return nodes.field_list("", self.field(translate("URI"), [nodes.Text(uri)]))

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

    def fields(self, uri: str) -> nodes.field_list:
        """Add the labels, definitions and notations of the concept.

        Args:
            uri: The concept's URI.

        Returns:
            The concept's field list.
        """
        field_list = super().fields(uri)
        vocabularies = self.vocabularies
        facts: list[tuple[str, list[list[nodes.Node]]]] = [
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
            (
                translate("Notations"),
                [[nodes.Text(text)] for text in vocabularies.notations(uri)],
            ),
        ]
        field_list += [self.field(name, *values) for name, values in facts if values]
        return field_list


class CollectionDirective(ResourceDirective):
    """Show a collection."""

    kind = "collection"
