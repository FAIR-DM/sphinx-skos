# Tasks: Build a documentation site from SKOS vocabulary files

**Feature**: `001-vocabulary-site` · **Spec**: [`spec.md`](./spec.md) · **Plan**: [`plan.md`](./plan.md)

Every task is test-first per Article I: the test is written and seen to fail before the code that
makes it pass. Test scope per task is one class or one file. The full suite runs once per group, at
its report.

**A test never asserts wording or appearance** (`docs/contributing/standards/testing.md` §1). A
warning is asserted by the URI, pattern, file or address it names, never by its sentence. A field
is found by the data in it, never by its heading.

**The extension adds no stylesheet, script, template, image, static file or theme option.** A task
that creates a file under `sphinx_skos/` other than a `.py` module has gone wrong.

**Names**: no leading underscores, line length 88, no compatibility aliases.

---

## Phase: User Story 1 — A site maintainer publishes their vocabulary files as a site (P1)

### Group 1

#### T001 — rdflib and furo join the dependencies

**Files**: `pyproject.toml`, `uv.lock`

`rdflib>=7.6` in `dependencies`, `furo` in the `dev` group, through `uv add`. `deptry .` passes
once T002 imports rdflib.

#### T002 — The vocabulary files become one graph

**Files**: `sphinx_skos/vocabularies.py` (new), `sphinx_skos/__init__.py`, `tests/test_vocabularies.py` (new), `tests/roots/test-vocabularies/` (new), `tests/roots/test-unreadable/` (new)

The two settings registered in `setup()` (plan, Settings). `Vocabularies` loading, `fingerprint`
and `resources` (plan, `Vocabularies`). Tests:

- a relative pattern is read from the configuration directory (US1 scenario 3);
- every typed resource in both files is in `resources` with its kind, and an organisation and a
  bibliographic reference are not (scenarios 1, 6);
- a resource stated in both files has every statement from both (scenario 5, FR-005);
- a pattern matching no file warns naming the pattern, and a file that is not Turtle warns naming
  the file, while every other file still loads (scenario 10).

#### T003 — Every resource gets a generated page at its address

**Files**: `sphinx_skos/pages.py` (new), `sphinx_skos/domain.py` (new), `sphinx_skos/directives.py` (new), `sphinx_skos/__init__.py`, `tests/test_pages.py` (new), `tests/roots/test-no-base-uri/` (new), `tests/roots/test-collision/` (new)

`GeneratedPages` (plan, `GeneratedPages`), `SKOSDomain` (plan) and the `builder-inited` handler.
The three directives exist with the title section only: `ResourceDirective.run()` steps 1 and 2,
title rule from research R9, no fields yet. Tests, building `test-vocabularies` with `dirhtml`:

- one output page per vocabulary, concept and collection, at its address, and none for anything
  else (scenarios 1, 2, 4, FR-002, FR-004);
- a resource outside the base URI has no page and a warning names its URI (scenario 7);
- a URI equal to the base URI, one with `#`, one with `?`, one with a `\` and one with a `..`
  segment have no page and each is named in a warning (scenario 8, research R10);
- a site's own document at an address keeps its content, and the warning names the address and
  the resource (scenario 9), including a site document `a` against a resource whose address is
  `a/`, and two resources `x` and `x/` (the second named in the warning);
- a site whose `source_suffix` is `{".txt": "restructuredtext"}` has every page, so a hard-coded
  `.rst` fails, and a site with no reStructuredText suffix gets one warning and no pages;
- with no base URI, no page is generated and one warning is emitted (scenario 11);
- a generated page raises no table-of-contents warning, and a site whose `index` lists a
  vocabulary's address in a `toctree` builds clean with that page in its table of contents
  (scenario 13, FR-008);
- the generated source files carry no hand-written content: the site's own pages are unchanged
  after the build (FR-003).

#### T004 — The user documentation for publishing a site

**Files**: `README.md`, `CHANGELOG.md`, `docs/index.md` (new), `docs/how-to/index.md` (new), `docs/how-to/publish-vocabulary-files.md` (new), `docs/reference/index.md` (new), `docs/reference/settings.md` (new)

Per `docs/contributing/standards/documentation.md`: the README's status and quickstart become
true, the how-to walks a maintainer through the three settings, building with `dirhtml`, listing
vocabulary pages in a `toctree`, and listing the generated sources in `.gitignore` (research R1).
The settings reference gives both settings with type, default and meaning. CHANGELOG under
`[Unreleased]`, `### Added`.

### Group 2

#### T005 — A rebuild gives what a clean build gives

**Files**: `sphinx_skos/domain.py`, `sphinx_skos/pages.py`, `sphinx_skos/__init__.py`, `tests/test_domain.py` (new), `tests/test_pages.py`

The fingerprint in domain data and the `env-get-outdated` handler (plan, Event handlers), and the
clean-up of stale generated sources and their output (plan, `GeneratedPages`). Each test copies
`test-vocabularies` into `tmp_path`, builds, changes the files, builds again without a clean, and
compares the set of output files and each page's doctree with a clean build of the changed files
(scenario 12, FR-007):

- a label edited: the page shows the new label;
- a resource removed: its page, its source and its `_sources/` copy are gone (its RDF copies are
  added to this test in T011);
- a file added: its resources have pages;
- an unchanged rebuild rewrites no generated source (modification times kept).

#### T006 — Any theme, and the html builder

**Files**: `tests/test_pages.py`

- built under alabaster and under furo, both clean, with the same page set (scenario 14, FR-024);
- built with `html`, every resource has a page at the file the builder gives its document name
  (scenario 15).

FR-024's "adds no stylesheet, script, template, image, static file or theme option" is held by
review of the diff, not by a test: a test that lists the package's files only records today's
layout.

---

## Phase: User Story 2 — A reader looks up a resource and finds what they need to use it (P1)

### Group 3

#### T007 — A concept page shows its own facts

**Files**: `sphinx_skos/vocabularies.py`, `sphinx_skos/directives.py`, `tests/test_vocabularies.py`, `tests/test_directives.py` (new)

`ConceptDirective` fields URI, preferred labels, alternative labels, definitions and notations
(plan, Directives). Tests read the built doctree or HTML for the concept:

- every preferred and alternative label appears with its language, and a label with no language
  shows none (US2 scenario 1, edge case);
- no hidden label appears in the HTML (scenario 2, FR-011);
- both definitions with their languages, and the notation (scenario 3);
- the title is the label in the site's `language`; a concept whose preferred labels are in two
  other languages, written in reverse tag order, is titled with the label the test computes as the
  first by tag then text; a concept with no preferred label is titled with its URI (scenario 4,
  FR-015);
- the URI appears on the page (scenario 9);
- a label holding `<b>&amp;</b>` appears in the HTML escaped, and no `<b>` element comes from it
  (scenario 14, FR-016).

#### T008 — Fixed text is translatable and vocabulary text is not

**Files**: `sphinx_skos/directives.py`, `tests/test_directives.py`, `tests/roots/test-translation/` (new)

The test site's `conf.py` sets `language = "de"` and registers a `sphinx_skos` catalogue of its own
in `setup(app)`, compiled from a `.po` file in the root with babel at test time. A field name comes
out as the catalogue's translation, and a vocabulary label equal to that same message id is left as
written (US1 scenario 16, FR-009).

### Group 4

#### T009 — A concept page links to everything related to it

**Files**: `sphinx_skos/vocabularies.py`, `sphinx_skos/directives.py`, `tests/test_vocabularies.py`, `tests/test_directives.py`

Concept fields vocabulary, collections, broader, narrower, related and mapping links, and the link
rule (plan, Directives step 3). Tests on the built HTML, finding each link by its `href`:

- both collections the concept is a member of are linked (scenario 5);
- broader, narrower and related concepts are linked whether the link is stated on this concept or
  on the other one (scenario 6);
- a mapping link to a concept with a page goes to that page, and one to an outside URI goes to the
  URI, each in the field of its own mapping property, with no warning (scenarios 7, 8, FR-014);
- the concept's vocabulary page is linked (scenario 13), and a concept in no vocabulary builds
  with no warning (edge case);
- a link to a resource outside the base URI goes to its URI (edge case);
- a mapping link to a `javascript:` URI is shown as text with no link (decision D27).

#### T010 — Vocabulary and collection pages

**Files**: `sphinx_skos/vocabularies.py`, `sphinx_skos/directives.py`, `tests/test_vocabularies.py`, `tests/test_directives.py`

`VocabularyDirective` and `CollectionDirective` fields (plan, Directives). Tests:

- a vocabulary page shows its labels and definition or description and links every concept and
  every collection in it (scenario 10, FR-012), and a vocabulary with none builds with its own
  content (edge case);
- an ordered collection links its members in list order (scenario 11);
- an unordered collection, whose members the file lists out of title order, links every member in
  the order the test computes by title then URI (scenario 12);
- a vocabulary's concepts and a concept's relations, written out of order in the file, come out
  in the order the test computes (FR-015).

---

## Phase: User Story 3 — Someone resolving a resource URI from software gets its RDF (P1)

### Group 5

#### T011 — Four RDF copies beside every page

**Files**: `sphinx_skos/copies.py` (new), `sphinx_skos/vocabularies.py`, `sphinx_skos/__init__.py`, `tests/test_copies.py` (new), `tests/test_vocabularies.py`

`own_rdf`, `RdfCopies` and the `html-page-context` handler (plan). Tests:

- every page's directory holds `index.ttl`, `index.jsonld`, `index.rdf` and `index.nt` under
  `dirhtml` (US3 scenario 1, FR-017), and `<name>.ttl` and the rest beside `<name>.html` under
  `html`;
- each copy, in each format, parses to a graph isomorphic to the resource's own RDF taken from the
  files independently, by reading the test files with rdflib in the test and collecting the
  resource's triples and blank-node closure there (scenario 2, FR-018);
- an ordered collection's copy holds its member list complete and in order (scenario 3);
- a concept's copy holds neither the broader concept's `skos:narrower` nor a collection's
  `skos:member` naming it (scenario 4);
- the rebuild test of T005 for a removed resource also finds its copies gone, and `GeneratedPages`
  removes them.

#### T012 — Software finds the copies from the page

**Files**: `sphinx_skos/copies.py`, `tests/test_copies.py`, `README.md`, `CHANGELOG.md`, `docs/reference/rdf-copies.md` (new), `docs/reference/index.md`

- every generated page's HTML has one `<link rel="alternate">` per copy, each `href` resolving to
  the copy and each `type` its media type (scenario 5, FR-019), under alabaster and under furo;
- two builds of unchanged files give the same page addresses and copy file names (scenario 6,
  FR-020).

The reference page gives the copy names per builder and the media types, and says the names are
permanent.

#### T014 — Both real vocabulary sets build clean

**Files**: none in the repository. Run by the maintainer of the build, not dispatched.

A site listing fairdm-vocabularies' nine files and one listing ihfc-vocabularies' fifteen, each with
its own base URI, built with `dirhtml -W` under alabaster and under furo, in a working directory
outside the repository (Article XI keeps real organisations out of the test sites). Each build is
checked by a script that reads the files with rdflib on its own: every resource has a page at its
address and nothing else does (SC-003), every copy in every format is isomorphic to the resource's
own RDF (SC-004), and every page names its four copies (SC-005). SC-001, SC-002, SC-006.

---

## Phase: User Story 4 — A site maintainer shows a resource in one of their own pages (P2)

### Group 6

#### T013 — Directives written by hand

**Files**: `sphinx_skos/directives.py`, `tests/test_directives.py`, `tests/roots/test-prose/` (new), `README.md`, `CHANGELOG.md`, `docs/reference/directives.md` (new), `docs/reference/index.md`, `docs/how-to/show-a-resource-in-a-page.md` (new), `docs/how-to/index.md`

The test site has a prose page with each of the three directives by hand. Tests:

- each shows the same fields and links as on the resource's generated page (US4 scenario 1, FR-021);
- the generated pages are still built, and only they have RDF copies and alternate links; the
  prose page has neither (scenario 2, FR-022);
- a URI naming no resource warns naming the URI and the page (scenario 3);
- a directive with no URI, and a vocabulary's URI in `skos:concept`, each warn naming the page
  and, where there is one, the URI (scenario 4, FR-023);
- a directive under a titled section of a prose page, and the same directive twice in one page,
  build clean (design review SPEC-002).

---

## Dependencies

Group 1 → Group 2 → Group 3 → Group 4 → Group 5 → Group 6. Within a group, tasks run in order.
Stories run one at a time in one worktree: each story extends `directives.py` and its tests.
