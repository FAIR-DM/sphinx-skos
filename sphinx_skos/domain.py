"""The ``skos`` domain: the directives and the build's vocabulary state."""

from collections.abc import Set
from typing import Any, ClassVar

from sphinx.domains import Domain

from sphinx_skos.directives import (
    CollectionDirective,
    ConceptDirective,
    VocabularyDirective,
)
from sphinx_skos.pages import GeneratedPages
from sphinx_skos.vocabularies import Vocabularies


class SKOSDomain(Domain):
    """Hold the three directives and the vocabularies of the current build.

    The domain's data holds the fingerprint of the vocabulary files the
    environment was last read with, which Sphinx keeps with the environment.
    """

    name = "skos"
    label = "SKOS"
    directives: ClassVar = {
        "vocabulary": VocabularyDirective,
        "concept": ConceptDirective,
        "collection": CollectionDirective,
    }
    initial_data: ClassVar = {"fingerprint": ""}

    vocabularies: Vocabularies
    pages: GeneratedPages

    def clear_doc(self, docname: str) -> None:
        """Forget nothing: the domain keeps no data per document.

        Args:
            docname: The document being read again or removed.
        """

    def merge_domaindata(self, docnames: Set[str], otherdata: dict[str, Any]) -> None:
        """Merge nothing: the domain keeps no data per document.

        Args:
            docnames: The documents a parallel reader read.
            otherdata: The reader's copy of the domain's data.
        """
