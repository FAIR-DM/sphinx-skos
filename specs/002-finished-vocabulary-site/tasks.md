# Tasks: A finished vocabulary site out of the box

**Feature**: `002-finished-vocabulary-site` · **Spec**: [`spec.md`](./spec.md) · **Plan**:
[`plan.md`](./plan.md)

Every task is test-first per Article I: the test is written and seen to fail before the code that
makes it pass. Test scope per task is one class or one file. The full suite runs once per group.

**A test never asserts wording or appearance** (`docs/contributing/standards/testing.md` §1). A
warning is asserted by the setting, URI, address or file it names, never by its sentence. A field
is found by the data in it, never by its heading. Furo's rendering is never asserted: tests read
the toctree tree Sphinx records.

**The extension adds no stylesheet, script, template, image, static file or theme option.** A task
that creates a file under `sphinx_skos/` other than a `.py` module has gone wrong.

**Names**: no leading underscores, line length 88, no compatibility aliases.

**Existing tests that pin a page address** (`date-types/available/` and the like) are updated to
the address under `vocabularies/` in T001. That is the specified behaviour changing (FR-014
supersedes feature 001's FR-004), not a regression being hidden. No other existing assertion is
weakened.

---

## Phase: User Story 2 — A developer adds the vocabulary pages to their own Sphinx site (P1)

### Group 1

#### T001 — Generated pages live under one directory

**Files**: `sphinx_skos/__init__.py`, `sphinx_skos/pages.py`, `tests/test_pages.py`, every test that
reads a generated page's address, `tests/roots/*/index.rst`, `tests/roots/*/conf.py`,
`tests/roots/*/vocabularies/` → `tests/roots/*/data/`

Every test root's vocabulary files move from `vocabularies/` to `data/` (patterns updated), so the
tests use the layout the documentation will recommend: vocabulary files outside the
generated-pages directory (DR-003).

`skos_directory` registered (plan, Generated pages). `find_docname` returns
`<directory>/<address>`. Directory validation. Tests:

- with the default setting every generated page is under `vocabularies/` and no generated file is
  elsewhere in the source directory (US2 scenarios 1, 3, FR-013, FR-014);
- with `skos_directory = "terms"` every page is under `terms/` (scenario 2);
- `""`, `"/abs"`, `"a/../b"` each warn naming `skos_directory` and generate no page (scenario 9,
  FR-018).

Existing tests' expected addresses gain the `vocabularies/` prefix.

#### T002 — An index page, and no generated page is orphan

**Files**: `sphinx_skos/pages.py`, `sphinx_skos/__init__.py`, `tests/test_pages.py`,
`tests/roots/*/index.rst`, new `tests/roots/test-unlisted/`

`index_text()`, the reserved index name, `:orphan:` removed. Test roots' own `index.rst` list
`vocabularies/index` in a toctree. Tests:

- `vocabularies/index` exists and links to every vocabulary (scenario 4, FR-015);
- no generated source holds `:orphan:`, and a site listing the index builds with no warning
  (scenario 5, FR-016);
- a site that does not list the index gets exactly one warning, naming the index document
  (scenario 6), using `test-unlisted`;
- a concept in no vocabulary is in a toctree of the index and causes no warning;
- a resource at address `index` warns as a collision and the index is kept.

#### T003 — Files that are not generated are kept, and old pages go

**Files**: `tests/test_pages.py`, new `tests/roots/test-upgrade/`

No new code expected (`clean` already does this; research R1). Tests:

- a file of the site's own inside `vocabularies/` at a resource's address is neither written over
  nor deleted, and the warning names the address and the resource (scenario 7, FR-017);
- a marked page at an old address (written into the test root before the build, as 0.3 wrote it)
  is removed, an unmarked file beside it is kept, and the output matches a clean build (scenario 8).

#### T004 — Documentation for the directory

**Files**: `docs/reference/settings.md`, new `docs/how-to/add-vocabulary-pages-to-a-site.md`,
`docs/how-to/index.md`, new `docs/adr/0003-generated-pages-have-their-own-directory.md`,
`docs/adr/0001-generated-pages-are-source-files.md`, `CHANGELOG.md`

`skos_directory` in the settings reference; the how-to (the index in a toctree, one `.gitignore`
entry, vocabulary files kept outside the generated-pages directory, moving a 0.3 site including
its redirect and moving any vocabulary files out of `vocabularies/` before ignoring it); ADR 0003 superseding 0001, and 0001 marked
`superseded by 0003`; a CHANGELOG entry naming the address change as breaking.

---

## Phase: User Story 3 — A reader finds a concept from the site's navigation (P1)

### Group 2

#### T005 — Each vocabulary lists its concepts and collections in a hidden toctree

**Files**: `sphinx_skos/pages.py`, `tests/test_pages.py`, `docs/how-to/add-vocabulary-pages-to-a-site.md`

`source_text` for a vocabulary appends the hidden toctree (plan). Tests, reading
`app.env.toctree_includes` and `app.env.tocs`/`get_and_resolve_doctree` where needed:

- the index's toctree holds every vocabulary (US3 scenario 1);
- a vocabulary's toctree holds its concepts then its collections in the order its page links them
  (scenario 2, FR-019);
- every concept and collection of `test-vocabularies` is below its vocabulary in the tree
  (scenario 3, SC-004);
- the vocabulary page's body has no visible toctree output (scenario 4);
- a concept in two vocabularies is in both toctrees, has one page and the build emits no warning
  (scenario 5, FR-020), with a new two-vocabulary test root.

The how-to says the theme's navigation shows the concepts beneath their vocabulary.

---

## Phase: User Story 4 — A reader takes a vocabulary's or a concept's RDF to use elsewhere (P2)

### Group 3

#### T006 — Each file's graph and its declared prefixes are kept

**Files**: `sphinx_skos/vocabularies.py`, `tests/test_vocabularies.py`, `tests/test_copies.py`

`load` with `bind_namespaces="none"` and `self.files`; `vocabulary_files`, `vocabulary_graph`,
`declared_prefixes` (plan). Tests:

- a vocabulary stated across two files has both files and both files' prefixes;
- a prefix declared in no file is absent (US4 scenario 8, FR-026);
- two files declaring one prefix for different namespaces give both pairs once each, sorted by
  prefix then namespace (scenario 7, FR-027);
- the existing Turtle-copy prefix test and every page's prefixed property names are unchanged.

#### T007 — Whole-vocabulary files

**Files**: `sphinx_skos/copies.py`, `sphinx_skos/__init__.py`, `sphinx_skos/pages.py`,
`tests/test_copies.py`

`whole_paths`, `write_whole`, the `dirhtml`-only call, removal of a gone vocabulary's files.
Tests:

- for every vocabulary of `test-vocabularies`, four files at `vocabularies/<address>.<ext>` that
  each parse to a graph isomorphic to the vocabulary file (US4 scenarios 2, 3, FR-023, SC-003);
- a vocabulary's own copies and every page's `<link rel="alternate">` elements are unchanged
  (FR-024);
- a vocabulary removed from the files has its whole files removed on the next build.

#### T008 — Downloads on every generated page

**Files**: `sphinx_skos/directives.py`, `tests/test_directives.py`

The `Download` field and the `DownloadLinks` post-transform (plan). Tests, under Furo and
alabaster:

- a concept's and a collection's page link to their four copies, and each link resolves to a file
  in the output (US4 scenario 1, FR-021, FR-022, SC-006);
- a vocabulary's page links to its four whole files, each resolving (scenario 2);
- a page written by hand with a directive has no download links (scenario 5);
- a site built with `html` and then with `dirhtml` over the same doctree directory: every download
  link of the second build resolves to a file (DR-002);
- a `text` build of a generated page holds no download field;
- the field's heading goes through `translate` (FR-025): with a catalogue that translates it, the
  translated text appears.

#### T009 — Namespace prefixes on a vocabulary's page

**Files**: `sphinx_skos/directives.py`, `tests/test_directives.py`

The `Namespace prefixes` field (plan). Tests:

- a vocabulary page lists every declared prefix with its namespace URI as a link (scenario 6);
- the list is in the same order across two builds and none undeclared appears (scenarios 7, 8).

#### T010 — Documentation for downloads and prefixes

**Files**: `docs/reference/rdf-copies.md`, `docs/reference/directives.md`, `CHANGELOG.md`

Whole-vocabulary files (names, contents, `dirhtml` only), the two new fields.

---

## Phase: User Story 1 — A developer publishes vocabulary files as a site with one command (P1)

### Group 4

#### T011 — Settings from `pyproject.toml`, and Furo by default

**Files**: new `sphinx_skos/settings.py`, `sphinx_skos/__init__.py`, `pyproject.toml`, `uv.lock`,
new `tests/test_settings.py`, new test roots as needed

`uv remove --group dev furo; uv add furo`. deptry DEP002 waiver for `furo` with a comment.
`SiteSettings` (plan). Tests:

- a `[tool.sphinx-skos]` table beside a `conf.py` that sets none of the settings: each mapped
  setting takes the table's value, and relative patterns are read from the table's directory
  (US1 scenario 3, FR-002);
- the same with `conf.py` setting `skos_base_uri` and `project`: the `conf.py` values win
  (scenario 6, FR-005);
- an unknown key warns naming it;
- a site that sets no theme is built with `furo`; one that sets `html_theme = "alabaster"` is
  built with alabaster; one that passes `-D html_theme=alabaster` likewise; a theme option the site
  sets is kept (scenarios 10, 11, FR-010, FR-011);
- the package adds no `html_static_path`, `html_css_files` or theme option (FR-012);
- `importlib.metadata.requires("sphinx-skos")` names `furo` without an extra marker (FR-009);
- a table-less `pyproject.toml` between the configuration directory and a tabled ancestor: no
  setting comes from the ancestor (DR-011).

#### T012 — The front page

**Files**: `sphinx_skos/pages.py`, `tests/test_pages.py`, new `tests/roots/test-no-front-page/`

`front_page_text`, written when the site has no root document. Tests:

- a site with vocabularies and no `index` gets a front page whose title is `project` and whose
  toctree holds `vocabularies/index` and every page of the site's own, one in a subdirectory
  included, and the build emits no warning (scenarios 2, 4, FR-003);
- a site whose only pages are generated gets a front page and no warning;
- a site with its own `index` (any suffix) keeps it, and no generated front page exists
  (scenario 5, FR-004);
- a generated front page is removed once the site adds its own, also when the site's own has a
  different suffix (`index.md` beside the marked `index.rst`), with no warning (DR-010). If
  discovery warns, `find_site_documents` skips marked files before discovering;
- a `project` holding reStructuredText markup appears in the title as text.

### Group 5

#### T013 — `sphinx-skos build`

**Files**: new `sphinx_skos/cli.py`, `pyproject.toml` (`[project.scripts]`), new `tests/test_cli.py`

`SiteBuild` and `main` (plan). Tests, each in a temporary project directory with
`monkeypatch.chdir`:

- `pyproject.toml` whose table holds exactly `title`, `base-uri` and `vocabularies`, and one
  vocabulary file, built with `-W`: exit 0, `_build/site/index.html` and a page per resource
  (scenario 1, FR-001, FR-006, SC-001);
- `-o out`: the site is in `out/` (scenario 9);
- a `docs/` with a prose page and no `index`: the prose page is built and the front page links it
  (scenario 4);
- a `docs/conf.py` that lists `sphinx_skos` and sets `skos_base_uri`: the conf value wins over
  the table's and the pages are built (scenario 6, FR-004);
- an unreadable vocabulary file: exit 0 without `-W`, non-zero with it (scenario 7, FR-007);
- neither table nor `docs/conf.py`: exit 2, and the message names `[tool.sphinx-skos]` and
  `docs/conf.py` (scenario 8, FR-008).

#### T014 — Documentation and the scope amendments

**Files**: `README.md`, `docs/how-to/publish-vocabulary-files.md`, new `docs/reference/command.md`,
`docs/reference/index.md`, `docs/reference/settings.md`, `CHANGELOG.md`, `CONTEXT.md`, `GOALS.md`,
`CONSTITUTION.md`, `AGENTS.md`, `specs/001-vocabulary-site/spec.md`

README quickstart becomes the one-command build; README *Scope & philosophy*, GOALS G3/G5/G6,
CONSTITUTION Articles X/XI/XIII (version 1.1.0, amended date), `CONTEXT.md` (*Site*, new terms) and
`AGENTS.md`'s "renders content only" line amended as the spec's *Amendments* sets out. The how-to
rewritten around `sphinx-skos build`; the command reference; the settings reference gains the
`[tool.sphinx-skos]` table, the order settings are read in and the Furo default. The feature 001
spec edited to read as current where this feature changed it (FR-004, FR-008, FR-024 and its
summary). No test: documentation. Before the pull request is marked ready, the fairdm-vocabularies
files are built by hand with `sphinx-skos build -W` from a three-key table, and the result for
SC-001 to SC-004 goes in the pull request body.

## Fixes

#### T015 — The navigation nests each vocabulary's members under its title

**Files**: `sphinx_skos/directives.py`, `sphinx_skos/pages.py`, `tests/test_pages.py`,
`docs/reference/directives.md`

The hidden toctree sat beside the directive's section, so a theme drew the concepts beside their
vocabulary rather than beneath it. The directives now parse their content into their section and
the vocabulary's toctree is written as that content. Test: the resolved navigation nests every
member's entry inside its vocabulary's entry (US3 scenario 2, SC-004).
