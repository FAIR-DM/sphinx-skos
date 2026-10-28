from pathlib import Path

import pytest
from rdflib import Namespace, URIRef
from sphinx.testing.util import SphinxTestApp

from sphinx_skos.vocabularies import Label, Vocabularies

BASE = "https://example.org/vocab/"
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")


class TestVocabulariesLoading:
    @pytest.mark.sphinx("dirhtml", testroot="basic")
    def test_the_settings_default_to_nothing_listed_and_no_base_uri(
        self, app: SphinxTestApp
    ) -> None:
        assert app.config.skos_vocabularies == []
        assert app.config.skos_base_uri == ""

    @pytest.mark.sphinx("dirhtml", testroot="vocabularies")
    def test_a_relative_pattern_is_read_from_the_configuration_directory(
        self, app: SphinxTestApp
    ) -> None:
        vocabularies = Vocabularies(app.config.skos_vocabularies, app.confdir)

        assert BASE + "date-types" in vocabularies.resources
        assert BASE + "methods" in vocabularies.resources
        assert app.warning.getvalue() == ""

    @pytest.mark.sphinx("dirhtml", testroot="vocabularies")
    def test_an_absolute_pattern_is_read_where_it_points(
        self, app: SphinxTestApp, tmp_path: Path
    ) -> None:
        elsewhere = tmp_path / "elsewhere.ttl"
        elsewhere.write_text(f"<{BASE}remote> a <{SKOS}Concept> .\n", encoding="utf-8")

        vocabularies = Vocabularies([str(elsewhere)], app.confdir)

        assert vocabularies.resources == {BASE + "remote": "concept"}

    @pytest.mark.sphinx("dirhtml", testroot="vocabularies")
    def test_every_typed_resource_in_both_files_is_a_resource_of_its_kind(
        self, app: SphinxTestApp
    ) -> None:
        vocabularies = Vocabularies(app.config.skos_vocabularies, app.confdir)

        assert vocabularies.resources == {
            BASE + "date-types": "vocabulary",
            BASE + "methods": "vocabulary",
            BASE + "instruments": "vocabulary",
            BASE + "date-types/available": "concept",
            BASE + "date-types/created": "concept",
            BASE + "date-types/issued": "concept",
            BASE + "date-types/markup": "concept",
            BASE + "methods/survey": "concept",
            BASE + "methods/loose": "concept",
            BASE + "date-types/by-origin": "collection",
            BASE + "date-types/in-order": "collection",
        }

    @pytest.mark.sphinx("dirhtml", testroot="vocabularies")
    def test_an_organisation_and_a_reference_are_not_resources(
        self, app: SphinxTestApp
    ) -> None:
        vocabularies = Vocabularies(app.config.skos_vocabularies, app.confdir)

        assert BASE + "organisations/acme" not in vocabularies.resources
        assert BASE + "references/smith-2020" not in vocabularies.resources

    @pytest.mark.sphinx("dirhtml", testroot="vocabularies")
    def test_a_resource_in_two_files_has_the_statements_of_both(
        self, app: SphinxTestApp
    ) -> None:
        vocabularies = Vocabularies(app.config.skos_vocabularies, app.confdir)
        created = URIRef(BASE + "date-types/created")

        alt_labels = {
            str(o) for o in vocabularies.graph.objects(created, SKOS.altLabel)
        }
        pref_labels = {
            str(o) for o in vocabularies.graph.objects(created, SKOS.prefLabel)
        }

        assert alt_labels == {"Made"}
        assert pref_labels == {"Created"}
        assert (created, SKOS.definition, None) in vocabularies.graph

    @pytest.mark.sphinx("dirhtml", testroot="vocabularies")
    def test_a_resource_of_two_kinds_is_a_vocabulary_then_a_collection_then_a_concept(
        self, app: SphinxTestApp, tmp_path: Path
    ) -> None:
        mixed = tmp_path / "mixed.ttl"
        mixed.write_text(
            f"<{BASE}a> a <{SKOS}Concept>, <{SKOS}Collection> .\n"
            f"<{BASE}b> a <{SKOS}Collection>, <{SKOS}ConceptScheme> .\n",
            encoding="utf-8",
        )

        vocabularies = Vocabularies([str(mixed)], app.confdir)

        assert vocabularies.resources == {
            BASE + "a": "collection",
            BASE + "b": "vocabulary",
        }


class TestVocabulariesProblems:
    @pytest.mark.sphinx("dirhtml", testroot="unreadable")
    def test_a_pattern_matching_nothing_is_named_in_a_warning(
        self, app: SphinxTestApp
    ) -> None:
        Vocabularies(app.config.skos_vocabularies, app.confdir)

        assert "vocabularies/absent-*.ttl" in app.warning.getvalue()

    @pytest.mark.sphinx("dirhtml", testroot="unreadable")
    def test_a_file_that_is_not_turtle_is_named_in_a_warning(
        self, app: SphinxTestApp
    ) -> None:
        Vocabularies(app.config.skos_vocabularies, app.confdir)

        assert "broken.ttl" in app.warning.getvalue()
        assert "good.ttl" not in app.warning.getvalue()

    @pytest.mark.sphinx("dirhtml", testroot="unreadable")
    def test_every_other_file_is_still_loaded(self, app: SphinxTestApp) -> None:
        vocabularies = Vocabularies(app.config.skos_vocabularies, app.confdir)

        assert vocabularies.resources == {BASE + "good": "vocabulary"}

    @pytest.mark.sphinx("dirhtml", testroot="unreadable")
    def test_a_file_that_fails_part_way_adds_none_of_its_triples(
        self, app: SphinxTestApp, tmp_path: Path
    ) -> None:
        partial = tmp_path / "partial.ttl"
        partial.write_text(
            f"<{BASE}kept> a <{SKOS}Concept> .\n<{BASE}lost> a <{SKOS}Concept> ;\n",
            encoding="utf-8",
        )

        vocabularies = Vocabularies([str(partial)], app.confdir)

        assert vocabularies.resources == {}
        assert len(vocabularies.graph) == 0


class TestVocabulariesFingerprint:
    @pytest.mark.sphinx("dirhtml", testroot="vocabularies")
    def test_the_same_files_give_the_same_fingerprint(self, app: SphinxTestApp) -> None:
        first = Vocabularies(app.config.skos_vocabularies, app.confdir)
        second = Vocabularies(app.config.skos_vocabularies, app.confdir)

        assert first.fingerprint == second.fingerprint != ""

    @pytest.mark.sphinx("dirhtml", testroot="vocabularies")
    def test_a_changed_file_changes_the_fingerprint(
        self, app: SphinxTestApp, tmp_path: Path
    ) -> None:
        vocabulary = tmp_path / "one.ttl"
        vocabulary.write_text(f"<{BASE}a> a <{SKOS}Concept> .\n", encoding="utf-8")
        before = Vocabularies([str(vocabulary)], app.confdir).fingerprint

        vocabulary.write_text(f"<{BASE}b> a <{SKOS}Concept> .\n", encoding="utf-8")
        after = Vocabularies([str(vocabulary)], app.confdir).fingerprint

        assert before != after


class TestVocabulariesTitle:
    @pytest.mark.sphinx("dirhtml", testroot="vocabularies")
    def test_the_title_is_the_preferred_label_in_the_sites_language(
        self, app: SphinxTestApp
    ) -> None:
        vocabularies = Vocabularies(app.config.skos_vocabularies, app.confdir)

        assert vocabularies.title(BASE + "date-types", "de") == "Datumstypen"
        assert vocabularies.title(BASE + "date-types", "en") == "Date types"

    @pytest.mark.sphinx("dirhtml", testroot="vocabularies")
    def test_without_a_label_in_that_language_the_first_by_tag_then_text_is_used(
        self, app: SphinxTestApp, tmp_path: Path
    ) -> None:
        concept = tmp_path / "concept.ttl"
        concept.write_text(
            f'<{BASE}c> <{SKOS}prefLabel> "Zebra"@fr, "Alpha"@nl, "Beta"@fr .\n',
            encoding="utf-8",
        )
        vocabularies = Vocabularies([str(concept)], app.confdir)

        assert vocabularies.title(BASE + "c", "en") == "Beta"

    @pytest.mark.sphinx("dirhtml", testroot="vocabularies")
    def test_without_a_preferred_label_the_title_is_the_uri(
        self, app: SphinxTestApp, tmp_path: Path
    ) -> None:
        concept = tmp_path / "concept.ttl"
        concept.write_text(f"<{BASE}c> a <{SKOS}Concept> .\n", encoding="utf-8")
        vocabularies = Vocabularies([str(concept)], app.confdir)

        assert vocabularies.title(BASE + "c", "en") == BASE + "c"


class TestVocabulariesFacts:
    @pytest.mark.sphinx("dirhtml", testroot="facts")
    def test_labels_come_with_their_language_ordered_by_language_then_text(
        self, app: SphinxTestApp
    ) -> None:
        vocabularies = Vocabularies(app.config.skos_vocabularies, app.confdir)

        assert vocabularies.labels(BASE + "facts/rich", "prefLabel") == [
            Label("Reich", "de"),
            Label("Rich", "en"),
        ]
        assert vocabularies.labels(BASE + "facts/rich", "altLabel") == [
            Label("Plain", ""),
            Label("Vermögend", "de"),
            Label("Wealthy", "en"),
        ]

    @pytest.mark.sphinx("dirhtml", testroot="facts")
    def test_a_hidden_label_is_not_read_as_either_kind_of_label(
        self, app: SphinxTestApp
    ) -> None:
        vocabularies = Vocabularies(app.config.skos_vocabularies, app.confdir)

        shown = vocabularies.labels(BASE + "facts/rich", "prefLabel")
        shown += vocabularies.labels(BASE + "facts/rich", "altLabel")

        assert "secretword" not in [label.text for label in shown]

    @pytest.mark.sphinx("dirhtml", testroot="facts")
    def test_definitions_come_with_their_language_and_notations_are_sorted(
        self, app: SphinxTestApp
    ) -> None:
        vocabularies = Vocabularies(app.config.skos_vocabularies, app.confdir)

        assert vocabularies.definitions(BASE + "facts/rich") == [
            Label("Mit viel Geld.", "de"),
            Label("Having much money.", "en"),
        ]
        assert vocabularies.notations(BASE + "facts/rich") == ["R1"]

    @pytest.mark.sphinx("dirhtml", testroot="facts")
    def test_a_resource_without_facts_has_empty_lists(self, app: SphinxTestApp) -> None:
        vocabularies = Vocabularies(app.config.skos_vocabularies, app.confdir)

        assert vocabularies.labels(BASE + "facts/bare", "prefLabel") == []
        assert vocabularies.definitions(BASE + "facts/bare") == []
        assert vocabularies.notations(BASE + "facts/bare") == []
