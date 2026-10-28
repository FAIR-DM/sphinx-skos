"""The directives that turn a resource's URI into content."""

from typing import TYPE_CHECKING, ClassVar, cast

from docutils import nodes
from sphinx.util import logging
from sphinx.util.docutils import SphinxDirective

from sphinx_skos.vocabularies import Kind

if TYPE_CHECKING:
    from sphinx_skos.domain import SKOSDomain

logger = logging.getLogger(__name__)


class ResourceDirective(SphinxDirective):
    """Show the resource whose URI is the directive's argument."""

    required_arguments = 1
    optional_arguments = 0
    has_content = False
    kind: ClassVar[Kind]

    def run(self) -> list[nodes.Node]:
        """Return a section titled with the resource, or warn why not."""
        uri = self.arguments[0]
        domain = cast("SKOSDomain", self.env.domains["skos"])
        vocabularies = domain.vocabularies
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
        return [section]


class VocabularyDirective(ResourceDirective):
    """Show a vocabulary."""

    kind = "vocabulary"


class ConceptDirective(ResourceDirective):
    """Show a concept."""

    kind = "concept"


class CollectionDirective(ResourceDirective):
    """Show a collection."""

    kind = "collection"
