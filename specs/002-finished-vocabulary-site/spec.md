# Feature Specification: A finished vocabulary site out of the box

**Feature Branch**: `002-finished-vocabulary-site`

**Created**: 2026-10-29

**Status**: Draft

**Goals**: G1, G2, G3, G5, G6 and G7 (see [`GOALS.md`](../../GOALS.md)). G3, G5 and G6 are
amended by this feature, as set out under *Amendments* below.

**Input**: Issue #27, which brings together issues #19, #20, #21, #22 and #23 as one feature: a site that installs
sphinx-skos gets a finished vocabulary site, with navigation, downloads and a layout, without
writing Sphinx configuration.

## Summary

A developer lists their vocabulary files, base URI and title in `pyproject.toml` and runs
`sphinx-skos build`. They get a finished site: a front page listing every vocabulary, a page for
every vocabulary, concept and collection, navigation that shows each vocabulary's concepts and
collections, and on every page a way to download its RDF in four formats. A developer who keeps a
Sphinx site of their own gets the same pages in one directory, and adds them to their site with
one entry in a table of contents.

Installing the optional `sphinx-skos[book]` extra gives the site a ready-made layout built on
sphinx-book-theme, used only when the site chooses no theme of its own. Every setting a site makes
itself, in `pyproject.toml` or in its own `conf.py`, wins over every default.

A reader finds a concept from the site's navigation, reads the namespace prefixes a vocabulary
declares, and takes a concept's RDF, or a whole vocabulary's, in the format they need.

## Amendments

This feature changes what the package is for, and amends its stated scope in the same change:

- **README, *Scope & philosophy*.** The package is still not a theme and adds no look-and-feel
  options, but it ships one optional, ready-made layout, used only when the `book` extra is
  installed and the site sets no theme, and overridable in full by the site.
- **GOALS G5.** Everything site-specific is set in `pyproject.toml` or in the site's own
  `conf.py`.
- **GOALS G6.** A site's look and feel comes from its Sphinx theme, and the extension works under
  any theme. With the `book` extra installed and no theme chosen, the theme is sphinx-book-theme
  with the ready-made layout.
- **GOALS G3 and constitution Article XIII.** A page's address is its URI with the base URI
  removed, under the generated-pages directory. It depends on the URI, the base URI and that
  directory's name, and on nothing else.
- **Constitution Article X.** The extension adds no stylesheet, script, template, image, static
  file or theme option, except the ready-made layout, which applies only when the `book` extra is
  installed and the site has chosen no theme.
- **Constitution Article XI.** Everything a site needs to differ in comes from its
  `pyproject.toml` or its `conf.py`.
- **ADR 0001** is superseded by a new decision record: generated pages are written into a
  directory of their own, with an index, and are listed in tables of contents rather than marked
  `:orphan:`.
- **`CONTEXT.md`.** *Site* no longer requires a `conf.py` of its own, and the glossary gains the
  terms under *Key Entities*.
- **The feature 001 specification** is edited to read as current wherever this feature changes
  what it describes: page addresses, tables of contents, and look and feel.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A developer publishes vocabulary files as a site with one command (Priority: P1)

A developer with a few Turtle files and no Sphinx knowledge adds a `[tool.sphinx-skos]` table to
`pyproject.toml`, naming the site's title, its base URI and its vocabulary files, and runs
`sphinx-skos build`. The site is built with no `conf.py` and no page written by hand. When they
want more, they add a `docs/` directory of their own: its pages join the site, and its `conf.py`
can change any setting. With the `book` extra installed and no theme chosen, the site has the
ready-made layout.

**Why this priority**: It is what makes the site finished out of the box. Every other story is
seen through a site built this way.

**Independent Test**: In a directory holding only a `pyproject.toml` and one vocabulary file, run
`sphinx-skos build` and check that it exits zero and the output holds a front page and a page for
every resource in the file.

**Acceptance Scenarios**:

1. **Given** a project whose `pyproject.toml` has a `[tool.sphinx-skos]` table with a title, a
   base URI and a vocabulary pattern, and no `docs/` directory, **When** the developer runs
   `sphinx-skos build`, **Then** the command exits zero and the site is built with the `dirhtml`
   builder into the documented default output directory.
2. **Given** that build, **When** the developer opens the front page, **Then** it carries the
   site's title and links to every vocabulary.
3. **Given** a vocabulary pattern that is a relative path, **When** the site is built, **Then** it
   is read relative to the directory holding `pyproject.toml`.
4. **Given** a project with a `docs/` directory of its own holding prose pages and no front page,
   **When** the site is built, **Then** the prose pages are part of the site and the generated
   front page links to them as well as to every vocabulary.
5. **Given** a `docs/` directory with a front page of its own, **When** the site is built,
   **Then** that front page is the site's front page and is not written over.
6. **Given** a setting made by the package's defaults, again in `[tool.sphinx-skos]`, and again in
   the site's own `docs/conf.py`, **When** the site is built, **Then** the `conf.py` value is
   used. **Given** a setting made by the defaults and in `[tool.sphinx-skos]` only, **Then** the
   `[tool.sphinx-skos]` value is used.
7. **Given** the developer asks for warnings to fail the build, **When** a vocabulary file cannot
   be read, **Then** the command exits non-zero. Without that request, the same build exits zero
   and reports the warning.
8. **Given** no `[tool.sphinx-skos]` table and no `docs/conf.py`, **When** the developer runs
   `sphinx-skos build`, **Then** the command exits non-zero with a message saying what to add.
9. **Given** the developer passes an output directory to the command, **When** the site is built,
   **Then** it is written there.
10. **Given** the `book` extra is installed and the site sets no theme, **When** the site is
    built, **Then** it uses sphinx-book-theme with the ready-made layout: the vocabularies and the
    site's own top-level pages in the left sidebar on every page, the top bar's search component
    and the right-hand sidebar both turned off, the layout's stylesheet included, and each
    generated page's downloads in the theme's download menu in place of the page source.
11. **Given** the `book` extra is installed and the site sets its own theme, **When** the site is
    built, **Then** none of the ready-made layout applies: no theme option, stylesheet or menu
    change comes from the package.
12. **Given** the `book` extra is installed, the site sets no theme, and its `conf.py` sets one of
    the theme options the layout sets, **When** the site is built, **Then** the site's value is
    used and every other part of the layout still applies.
13. **Given** the `book` extra is not installed and the site sets no theme, **When** the site is
    built, **Then** it uses Sphinx's default theme and builds without warnings.

---

### User Story 2 - A developer adds the vocabulary pages to their own Sphinx site (Priority: P1)

A developer who already runs a Sphinx site lists their vocabulary files in `conf.py`, as today.
Every generated page is written into one directory of the site's source, `vocabularies/` unless
they name it otherwise, with an index page listing every vocabulary. They add that index to one of
their own tables of contents, and ignore the directory with one `.gitignore` entry.

**Why this priority**: It is how an existing site gets navigation, and the one-command build in
US1 is built on the same directory.

**Independent Test**: Build a test site whose root table of contents lists `vocabularies/index`,
and check that every generated page sits under `vocabularies/`, that the build emits no warning,
and that the source directory outside `vocabularies/` gained no generated file.

**Acceptance Scenarios**:

1. **Given** a site with the default settings, **When** it is built, **Then** every generated page
   is under `vocabularies/` in the source directory, and no generated file is anywhere else in it.
2. **Given** a site that sets the generated-pages directory to another name, **When** it is built,
   **Then** every generated page is under that directory instead.
3. **Given** the base URI `https://w3id.org/example/vocabularies/` and a concept
   `https://w3id.org/example/vocabularies/date-types/available`, **When** the site is built with
   the default directory, **Then** the concept's page is `vocabularies/date-types/available/` in
   the output.
4. **Given** the generated-pages directory, **When** the site is built, **Then** it holds an
   index page that links to every vocabulary.
5. **Given** a site that lists the index in one of its own tables of contents and nothing else
   from the directory, **When** it is built, **Then** the build emits no warning about a document
   missing from a table of contents, and no generated page is `:orphan:`.
6. **Given** a site that does not list the index in any table of contents, **When** it is built,
   **Then** the build emits one warning, about the index, and none for any other generated page.
7. **Given** a file in the generated-pages directory that the extension did not generate,
   **When** the site is built, **Then** the file is neither written over nor deleted, and a
   resource whose page would replace it gets no page and a warning naming both.
8. **Given** a site built by an earlier version, with generated pages at the old addresses in its
   source directory, **When** it is built by this version, **Then** those generated pages are
   removed, the site's own files are kept, and the output matches a clean build.
9. **Given** a site that sets the generated-pages directory to an empty name, or to a path
   outside the source directory, **When** it is built, **Then** no page is generated and the build
   emits a warning naming the setting.

---

### User Story 3 - A reader finds a concept from the site's navigation (Priority: P1)

A reader on a vocabulary site sees the vocabularies in the site's navigation. Under each
vocabulary they find its concepts and collections, and on a concept's page that concept is the
current page in the navigation.

**Why this priority**: Without it a reader reaches a concept only by following links from its
vocabulary's page or by searching, and the theme's navigation is empty.

**Independent Test**: Build a test site and check that the vocabulary's page carries a hidden
table of contents listing each concept and collection, and that a concept's page is placed
beneath its vocabulary in the site's table-of-contents tree.

**Acceptance Scenarios**:

1. **Given** a built site, **When** a reader opens any page, **Then** the theme's navigation lists
   every vocabulary.
2. **Given** a vocabulary's page, **When** a reader looks at the navigation, **Then** the
   vocabulary's concepts and collections are listed beneath it, in the order the vocabulary's
   page shows them.
3. **Given** a concept's page, **When** a reader looks at the navigation, **Then** that concept is
   the current page, beneath its vocabulary.
4. **Given** the table of contents on a vocabulary's page, **When** a reader reads the page,
   **Then** it adds nothing to the page body: it is hidden.
5. **Given** a concept in two vocabularies, **When** the site is built, **Then** the concept has
   one page, it is listed under both vocabularies, and the build emits no warning about it.

---

### User Story 4 - A reader takes a vocabulary's or a concept's RDF to use elsewhere (Priority: P2)

A reader who wants to work with the data, in a triple store, a query or their own Turtle, finds
on every page a way to download that resource's RDF in Turtle, JSON-LD, RDF/XML or N-Triples. On a
vocabulary's page the download is the whole vocabulary, and the page lists the namespace prefixes
the vocabulary's files declare, so the reader can write prefixed names that match.

**Why this priority**: The RDF copies exist today and software can find them, so the data is
reachable. This story makes it reachable to a person.

**Independent Test**: Build a test site and check that a concept's page links to its four RDF
copies, that a vocabulary's page links to four whole-vocabulary files, that each
whole-vocabulary file parses to the graph of the vocabulary file, and that the vocabulary's page
lists that file's prefixes.

**Acceptance Scenarios**:

1. **Given** any theme and a site that adds nothing to its configuration for downloads, **When** a
   reader opens a concept's or a collection's page, **Then** the page offers its RDF copies for
   download in Turtle, JSON-LD, RDF/XML and N-Triples.
2. **Given** a vocabulary's page, **When** a reader downloads its RDF in any of the four formats,
   **Then** the file holds the whole vocabulary: the concept scheme, every concept in it and every
   collection in it.
3. **Given** a vocabulary file, **When** the site is built, **Then** each of the four
   whole-vocabulary files of a vocabulary read from it parses to a graph isomorphic to the file's
   own, with nothing added or dropped.
4. **Given** the ready-made layout of US1, **When** a reader opens the download menu on any
   generated page, **Then** it offers that page's downloads in all four formats and nothing else.
5. **Given** a page written by hand with one of the directives, **When** it is built, **Then** it
   offers no downloads, as it has no RDF copies.
6. **Given** a vocabulary file that declares namespace prefixes, **When** a reader opens the page
   of a vocabulary from that file, **Then** the page lists each prefix the file declares with its
   namespace URI.
7. **Given** the same files built twice, **When** the two builds of a vocabulary's page are
   compared, **Then** the prefixes are listed in the same order.
8. **Given** prefixes the RDF library knows but the vocabulary file does not declare, **When** the
   vocabulary's page is built, **Then** none of them is listed.

---

### Edge Cases

- **A vocabulary stated across several files.** Its page lists the prefixes declared in any of
  those files, and its whole-vocabulary files hold the graph of all of them together.
- **One file holding several vocabularies.** Each of them offers that file's whole graph, which
  holds the others too. Nothing in a file is dropped from its downloads.
- **Two files declaring one prefix for different namespaces.** Each distinct prefix and namespace
  pair is listed once.
- **A vocabulary with no concepts and no collections.** Its page has no table of contents, and
  the build emits no warning.
- **A collection whose members come from another vocabulary.** It is listed under its own
  vocabulary in the navigation, and its members link to their pages as today.
- **A vocabulary of thousands of concepts.** The navigation lists them all; how much of the list
  is shown at once is the theme's.

## Requirements *(mandatory)*

### Functional Requirements

**One-command build**

- **FR-001**: The package MUST provide a `sphinx-skos build` command that builds a site with the
  `dirhtml` builder from the `[tool.sphinx-skos]` table of the `pyproject.toml` in the directory
  it is run from, with no `conf.py` and no page written by hand. *(US1)*
- **FR-002**: `[tool.sphinx-skos]` MUST accept the site's title, its base URI, its vocabulary
  patterns, and every other setting the extension adds to a site. Relative vocabulary patterns are
  read from the directory holding `pyproject.toml`. *(US1)*
- **FR-003**: When the site has no front page of its own, the build MUST write one that carries
  the site's title and links to every vocabulary and to every prose page of the site's own.
  *(US1)*
- **FR-004**: When a `docs/` directory exists, its pages MUST be part of the site, and its
  `conf.py`, if it has one, MUST be read. A front page of its own MUST NOT be written over.
  *(US1)*
- **FR-005**: Settings MUST be read in this order, each overriding the one before: the package's
  defaults, `[tool.sphinx-skos]`, the site's own `conf.py`. *(US1)*
- **FR-006**: The command MUST write to a documented default output directory, and accept another
  one. *(US1)*
- **FR-007**: The command MUST accept an option that makes a build warning fail it with a non-zero
  exit, and MUST exit non-zero when the build fails. *(US1)*
- **FR-008**: The command MUST exit non-zero, with a message naming what to add, when it finds
  neither a `[tool.sphinx-skos]` table nor a `docs/conf.py`. *(US1)*

**Ready-made layout**

- **FR-009**: The package MUST offer an optional extra, `book`, that installs sphinx-book-theme.
  Without the extra, the package MUST NOT require sphinx-book-theme. *(US1)*
- **FR-010**: When sphinx-book-theme is installed and the site sets no `html_theme`, the site MUST
  be built with sphinx-book-theme and the ready-made layout: every vocabulary and every top-level
  page of the site's own in the left sidebar on every page; the top bar's search component turned
  off; the right-hand sidebar turned off, with the layout's stylesheet giving the article the width
  it leaves; each generated page's downloads in the theme's download menu in place of the page
  source. *(US1, US4)*
- **FR-011**: Any theme option or other setting the site sets MUST win over the layout's value for
  it. *(US1)*
- **FR-012**: When the site sets its own `html_theme`, the package MUST add no theme option,
  stylesheet or other part of the layout. *(US1)*

**Generated-pages directory**

- **FR-013**: Every generated page MUST be written under one directory of the site's source
  directory, `vocabularies` by default, named by a setting. Nothing generated MUST be written
  anywhere else in the source directory. *(US2)*
- **FR-014**: A resource's page address MUST be its URI with the base URI removed, under the
  generated-pages directory, and depend on nothing else. *(US2)*
- **FR-015**: The generated-pages directory MUST hold an index page listing every vocabulary in a
  table of contents. *(US2, US3)*
- **FR-016**: No generated page MUST be `:orphan:`, and a site that lists the index in a table of
  contents MUST build without warnings about documents missing from one. *(US2)*
- **FR-017**: The extension MUST never write over or delete a file it did not generate, inside the
  generated-pages directory or elsewhere. It MUST delete pages it generated that are no longer
  produced, including those an earlier version wrote at the old addresses. *(US2)*
- **FR-018**: A generated-pages directory setting that is empty, or that leads outside the source
  directory, MUST give a warning naming the setting, and no page. *(US2)*

**Navigation**

- **FR-019**: Each vocabulary's page MUST list its concepts and collections in a hidden table of
  contents, in the order the page shows them. *(US3)*
- **FR-020**: A concept that belongs to several vocabularies MUST be listed under each without a
  build warning. *(US3)*

**Downloads**

- **FR-021**: Every generated page MUST offer its downloads in Turtle, JSON-LD, RDF/XML and
  N-Triples on the page itself, under any theme, with nothing added to the site's configuration.
  Under the ready-made layout they are offered in the theme's download menu instead. *(US4)*
- **FR-022**: A concept's or collection's downloads MUST be its RDF copies. *(US4)*
- **FR-023**: The build MUST write one whole-vocabulary file per vocabulary and format, holding the
  graph of every vocabulary file the vocabulary is stated in, with nothing added or dropped. A
  vocabulary's downloads MUST be those files. *(US4)*
- **FR-024**: A vocabulary's RDF copies, and the `<link rel="alternate">` elements on every page,
  MUST stay as they are. *(US4)*
- **FR-025**: Fixed text the downloads add to a page MUST be marked for translation. *(US4)*

**Namespace prefixes**

- **FR-026**: A vocabulary's page MUST list every namespace prefix declared in the vocabulary
  files it is stated in, each with its namespace URI, and no prefix those files do not declare.
  *(US4)*
- **FR-027**: The list MUST be in an order fixed by the prefixes and namespaces themselves, the
  same on every build. *(US4)*

**Scope documents**

- **FR-028**: The README's *Scope & philosophy*, GOALS G3, G5 and G6, constitution Articles X, XI
  and XIII, `CONTEXT.md`, ADR 0001 and the feature 001 specification MUST be amended as
  *Amendments* sets out, in the same change. *(US1, US2)*

### Key Entities

- **Generated-pages directory**: the directory in the site's source that holds every generated
  page and the index, `vocabularies/` by default.
- **Index**: the page at the root of the generated-pages directory that lists every vocabulary;
  the one document a site adds to its own table of contents.
- **Front page**: the site's root page. The site's own, when it has one; otherwise the one the
  one-command build writes.
- **Whole-vocabulary file**: a file holding a whole vocabulary in one of the four formats, offered
  from the vocabulary's page.
- **Download**: a link on a page, or in the theme's download menu, to that page's RDF in one
  format.
- **Ready-made layout**: sphinx-book-theme with the settings and stylesheet this feature
  describes, used only when the `book` extra is installed and the site sets no theme.
- **Namespace prefix**: a prefix and namespace URI pair declared in a vocabulary file.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The vocabulary files of
  [fairdm-vocabularies](https://github.com/FAIR-DM/fairdm-vocabularies) build into a complete site
  with `sphinx-skos build`, warnings treated as errors, from a `[tool.sphinx-skos]` table of three
  settings and no `conf.py`.
- **SC-002**: With the `book` extra installed and no theme chosen, that site has every part of the
  ready-made layout with nothing added to its configuration.
- **SC-003**: In that site, every whole-vocabulary file, in all four formats, parses to a graph
  isomorphic to the vocabulary file it was built from: 100% of them.
- **SC-004**: In that site, 100% of concepts and collections appear in the navigation beneath
  their vocabulary.
- **SC-005**: A site built on sphinx-skos 0.3 moves to this version by adding one entry to a table
  of contents and replacing its generated-page `.gitignore` entries with one, and then builds with
  warnings treated as errors.
- **SC-006**: Under Sphinx's default theme and under one other theme, every generated page offers
  four downloads, and the build emits no warning.

## Clarifications

### Session 2026-10-29

- Q: Are the five issues one feature or five? → A: One. Together they make the site finished out
  of the box, and none of the reader-facing parts is much use until the navigation and the build
  exist. They make four stories: two for the developer, who builds the site with one command or
  inside a site of their own, and two for the reader, who navigates it and takes its data.
- Q: Does the one-command build need a `docs/` directory? → A: No. Without one, the site is the
  generated pages and a generated front page. With one, its pages join the site and its `conf.py`
  is read.
- Q: Which page is the front page when `docs/` has one of its own? → A: The site's own. The
  generated front page is written only when the site has none, so a site's own page is never
  written over, and that page lists the generated-pages index in its own table of contents, as a
  site with a `conf.py` does.
- Q: Where are the downloads under a theme other than the ready-made layout? → A: On the page,
  as part of its content, so they work under any theme with no template. Under the ready-made
  layout they are in the theme's download menu, where the page source would be, and are not
  repeated on the page.
- Q: What does a vocabulary's own RDF copy hold now? → A: What it holds today: the scheme's own
  RDF. Its `<link rel="alternate">` elements are unchanged, so software resolving a vocabulary's
  URI gets the same answer. Only the downloads offered to a person are the whole vocabulary.
- Q: What is in a whole-vocabulary file? → A: The graph of every vocabulary file the vocabulary is
  stated in, as issue #19 asks: the same graph as the files, nothing added or dropped. With one
  vocabulary per file, the usual case, that is exactly the file. A file holding several
  vocabularies offers its whole graph from each of them, rather than dropping statements that
  belong to no single one, such as a publishing organisation.
- Q: In what order are the prefixes listed? → A: By prefix, then by namespace URI. Only prefixes
  declared in the files the vocabulary is stated in are listed, never the RDF library's own
  defaults.
- Q: Does moving the pages under a directory break existing sites? → A: Yes, for a site that
  redirects its URIs to the old addresses. Below 1.0.0 that is a minor release, recorded in the
  changelog with what to change: the redirect target gains the directory, the site's table of
  contents gains the index, and `.gitignore` needs one entry. Pages an earlier version generated
  are removed by the first build.
- Q: Can the generated-pages directory be the source directory itself, to keep the old
  addresses? → A: No. The directory holds its own index, which would clash with the site's front
  page, and a directory of its own is what makes one `.gitignore` entry enough.
- Q: Does the layout apply to a site that sets sphinx-book-theme as its theme itself? → A: No.
  Setting any theme is the site taking control, and issue #20 gives a site that sets its own theme
  none of the defaults.
- Q: Does the reusable GitHub Pages workflow change? → A: Not in this feature. It keeps building
  sites that have a `docs/conf.py`. A version that runs `sphinx-skos build` follows as its own
  change.

## Assumptions

- The vocabulary files are Turtle, as `CONTEXT.md` defines a vocabulary file.
- The ready-made layout is built against sphinx-book-theme 1.4.
- The one-command build reads the `pyproject.toml` in the directory it is run from.
- A live-reloading development server, and any command other than `build`, are out of scope.
- Releasing the package is out of scope.
