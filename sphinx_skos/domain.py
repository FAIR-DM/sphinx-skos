"""The ``skos`` domain: the directives and the build's vocabulary state."""

from typing import ClassVar

from sphinx.domains import Domain

from sphinx_skos.directives import (
    CollectionDirective,
    ConceptDirective,
    VocabularyDirective,
)
from sphinx_skos.pages import GeneratedPages
from sphinx_skos.vocabularies import Vocabularies


class SKOSDomain(Domain):
    """Hold the three directives and the vocabularies of the current build."""

    name = "skos"
    label = "SKOS"
    directives: ClassVar = {
        "vocabulary": VocabularyDirective,
        "concept": ConceptDirective,
        "collection": CollectionDirective,
    }

    vocabularies: Vocabularies
    pages: GeneratedPages
