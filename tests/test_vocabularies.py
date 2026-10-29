from pathlib import Path
from typing import Literal

import pytest
from rdflib import DCTERMS, SKOS, Namespace, URIRef
from rdflib.term import Literal as RDFLiteral
from sphinx.testing.util import SphinxTestApp

from sphinx_skos.vocabularies import Label, Target, Vocabularies

BASE = "https://example.org/vocab/"
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")


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

        assert "data/absent-*.ttl" in app.warning.getvalue()

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

    @pytest.mark.sphinx("dirhtml", testroot="unreadable")
    def test_a_member_list_that_loops_keeps_its_members_and_names_the_collection(
        self, app: SphinxTestApp, tmp_path: Path
    ) -> None:
        looped = tmp_path / "looped.ttl"
        looped.write_text(
            f"<{BASE}ordered> a <{SKOS}OrderedCollection> ;\n"
            f"    <{SKOS}memberList> _:first .\n"
            f"_:first <{RDF}first> <{BASE}one> ; <{RDF}rest> _:second .\n"
            f"_:second <{RDF}first> <{BASE}two> ; <{RDF}rest> _:first .\n",
            encoding="utf-8",
        )
        vocabularies = Vocabularies([str(looped)], app.confdir)

        members = vocabularies.listed_members(BASE + "ordered")

        assert members == [BASE + "one", BASE + "two"]
        assert BASE + "ordered" in app.warning.getvalue()


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
    def test_a_language_setting_matches_a_label_tag_whatever_its_case_or_separator(
        self, app: SphinxTestApp, tmp_path: Path
    ) -> None:
        concept = tmp_path / "concept.ttl"
        concept.write_text(
            f'<{BASE}c> <{SKOS}prefLabel> "Hi"@en, "Hallo"@pt-BR .\n',
            encoding="utf-8",
        )
        vocabularies = Vocabularies([str(concept)], app.confdir)

        assert vocabularies.title(BASE + "c", "pt_BR") == "Hallo"

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
    def test_definitions_come_with_their_language(
        self, app: SphinxTestApp
    ) -> None:
        vocabularies = Vocabularies(app.config.skos_vocabularies, app.confdir)

        assert vocabularies.definitions(BASE + "facts/rich") == [
            Label("Mit viel Geld.", "de"),
            Label("Having much money.", "en"),
        ]

    @pytest.mark.sphinx("dirhtml", testroot="facts")
    def test_statements_leave_out_hidden_labels(self, app: SphinxTestApp) -> None:
        vocabularies = Vocabularies(app.config.skos_vocabularies, app.confdir)

        statements = vocabularies.statements(URIRef(BASE + "facts/rich"))
        assert SKOS.hiddenLabel not in statements
        assert SKOS.prefLabel in statements

    @pytest.mark.sphinx("dirhtml", testroot="facts")
    def test_a_resource_without_facts_has_empty_lists(self, app: SphinxTestApp) -> None:
        vocabularies = Vocabularies(app.config.skos_vocabularies, app.confdir)

        assert vocabularies.labels(BASE + "facts/bare", "prefLabel") == []
        assert vocabularies.definitions(BASE + "facts/bare") == []


class TestVocabulariesRelations:
    @pytest.fixture
    def vocabularies(self, rootdir: Path) -> Vocabularies:
        return Vocabularies(["data/*.ttl"], rootdir / "test-relations")

    def test_a_concepts_vocabularies_come_from_either_way_of_stating_them(
        self, vocabularies: Vocabularies
    ) -> None:
        assert vocabularies.vocabularies_of(BASE + "rel/hub", "en") == [BASE + "rel"]
        assert vocabularies.vocabularies_of(BASE + "rel/top", "en") == [BASE + "rel"]
        assert vocabularies.vocabularies_of(BASE + "rel/top2", "en") == [BASE + "rel"]
        assert vocabularies.vocabularies_of(BASE + "rel/loose", "en") == []

    def test_a_concepts_collections_include_those_that_list_it(
        self, vocabularies: Vocabularies
    ) -> None:
        assert vocabularies.collections_of(BASE + "rel/hub", "en") == [
            BASE + "rel/col-b",
            BASE + "rel/col-a",
        ]
        assert vocabularies.collections_of(BASE + "rel/loose", "en") == []

    @pytest.mark.parametrize(
        ("property_", "expected"),
        [
            ("broader", ["rel/pb2", "rel/pb1"]),
            ("narrower", ["rel/n2", "rel/n1"]),
            ("related", ["rel/r2", "rel/r1"]),
        ],
    )
    def test_a_relation_is_read_whichever_concept_states_it(
        self,
        vocabularies: Vocabularies,
        property_: Literal["broader", "narrower", "related"],
        expected: list[str],
    ) -> None:
        found = vocabularies.relations(BASE + "rel/hub", property_, "en")

        assert found == [BASE + name for name in expected]

    def test_mappings_come_per_property_with_a_literal_marked_as_no_uri(
        self, vocabularies: Vocabularies
    ) -> None:
        found = dict(vocabularies.mappings(BASE + "rel/hub", "en"))

        assert list(found) == ["exactMatch", "closeMatch"]
        assert found["exactMatch"] == [
            Target(BASE + "rel-other/mapped", True),
            Target("https://elsewhere.example/outside", True),
            Target("plain text", False),
        ]

    def test_a_vocabulary_holds_the_concepts_that_say_so_and_its_top_concepts(
        self, vocabularies: Vocabularies
    ) -> None:
        found = vocabularies.concepts_in(BASE + "rel", "en")

        assert sorted(found) == sorted(
            BASE + name
            for name in (
                "rel/hub",
                "rel/r1",
                "rel/r2",
                "rel/n1",
                "rel/n2",
                "rel/pb1",
                "rel/pb2",
                "rel/top",
                "rel/top2",
            )
        )
        assert vocabularies.concepts_in(BASE + "rel-empty", "en") == []

    def test_a_collection_is_in_a_vocabulary_by_statement_or_by_member(
        self, vocabularies: Vocabularies
    ) -> None:
        found = vocabularies.collections_in(BASE + "rel", "en")

        assert sorted(found) == sorted(
            BASE + name for name in ("rel/col-a", "rel/col-b", "rel/col-c")
        )
        assert vocabularies.collections_in(BASE + "rel-other", "en") == []

    def test_members_come_in_list_order_when_the_collection_is_ordered(
        self, vocabularies: Vocabularies
    ) -> None:
        found = vocabularies.members_of(BASE + "rel/col-a", "en")

        assert found == [BASE + name for name in ("rel/r1", "rel/pb2", "rel/hub")]

    def test_members_come_sorted_by_title_when_the_collection_is_unordered(
        self, vocabularies: Vocabularies
    ) -> None:
        found = vocabularies.members_of(BASE + "rel/col-b", "en")

        assert found == [BASE + name for name in ("rel/pb2", "rel/n2", "rel/hub")]

    def test_statements_are_every_property_of_a_resource(
        self, vocabularies: Vocabularies
    ) -> None:
        statements = vocabularies.statements(URIRef(BASE + "rel"))

        assert statements[DCTERMS.description] == [
            RDFLiteral("Describes the relations.", lang="en")
        ]
        assert set(statements) == set(
            vocabularies.graph.predicates(URIRef(BASE + "rel"))
        )


class TestVocabulariesOwnRdf:
    @pytest.fixture
    def vocabularies(self, rootdir: Path) -> Vocabularies:
        return Vocabularies(["data/*.ttl"], rootdir / "test-relations")

    def test_own_rdf_is_only_triples_with_the_resource_as_subject_or_in_its_lists(
        self, vocabularies: Vocabularies
    ) -> None:
        own = vocabularies.own_rdf(BASE + "rel/col-a")

        assert (URIRef(BASE + "rel/col-a"), RDF.type, SKOS.OrderedCollection) in own
        assert (None, SKOS.member, URIRef(BASE + "rel/r1")) not in own
        assert set(own.subjects()) - {URIRef(BASE + "rel/col-a")} <= set(own.objects())

    def test_own_rdf_keeps_the_files_namespace_prefixes(
        self, vocabularies: Vocabularies
    ) -> None:
        own = vocabularies.own_rdf(BASE + "rel/hub")

        assert (
            dict(own.namespaces())["skos"]
            == dict(vocabularies.graph.namespaces())["skos"]
        )


class TestVocabulariesNames:
    @pytest.fixture
    def vocabularies(self, rootdir: Path) -> Vocabularies:
        return Vocabularies(["data/*.ttl"], rootdir / "test-properties")

    def test_an_agent_is_named_by_its_foaf_name(
        self, vocabularies: Vocabularies
    ) -> None:
        maker = "https://example.org/agents/maker"
        assert vocabularies.name(maker, "en") == "Maker Org"

    def test_a_uri_the_files_do_not_name_is_named_by_itself(
        self, vocabularies: Vocabularies
    ) -> None:
        unnamed = "https://example.org/agents/unnamed"
        assert vocabularies.name(unnamed, "en") == unnamed

    def test_a_resource_is_named_by_its_title(self, vocabularies: Vocabularies) -> None:
        assert vocabularies.name(BASE + "prop", "en") == "Properties"

    def test_a_uri_is_shortened_by_a_prefix_of_the_files(
        self, vocabularies: Vocabularies
    ) -> None:
        assert vocabularies.curie("https://example.org/terms/custom") == "ex:custom"
        unprefixed = "https://unprefixed.example/predicate"
        assert vocabularies.curie(unprefixed) == unprefixed
