# Feature Specification: Build a documentation site from SKOS vocabulary files

**Feature Branch**: `001-vocabulary-site`

**Created**: 2026-10-28

**Status**: Draft

**Goals**: G1, G2, G3, G4, G7, G8 (see [`GOALS.md`](../../GOALS.md)). It must also hold to G5 and
G6, which every feature serves.

**Input**: Issue #4, "Build a documentation site from SKOS vocabulary files".

## Summary

A site maintainer lists their vocabulary files and their base URI in `conf.py`, runs
`sphinx-build -b dirhtml`, and gets a site with one page for every vocabulary, concept and
collection in those files. Each page sits at its resource's URI with the base URI removed, and
has the resource's own RDF beside it in Turtle, JSON-LD, RDF/XML and N-Triples, named from the
page itself. The directives that build the generated pages can also be written by hand in the
site's own prose pages. Nothing about how the site looks comes from this package: the pages are
ordinary Sphinx documents and take their look from the site's theme.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A site maintainer publishes their vocabulary files as a site (Priority: P1)

A site maintainer adds `sphinx_skos` to `extensions`, lists their vocabulary files in
`skos_vocabularies` and sets `skos_base_uri`. When they build the site with the `dirhtml`
builder, every vocabulary, concept and collection in those files has a page at its page address,
with no document written by hand. Anything the extension cannot publish is named in a build
warning, so a build run with warnings treated as errors fails rather than leaving a page out
silently.

**Why this priority**: It is the feature. Without it nothing else in this specification has a
page to appear on.

**Independent Test**: Build a test site that lists one vocabulary file and check that the output
holds a page at the expected address for each vocabulary, concept and collection in it, and that
the build emits no warnings.

**Acceptance Scenarios**:

1. **Given** a site whose `skos_vocabularies` lists a pattern matching two vocabulary files,
   **When** the site is built with `dirhtml`, **Then** there is one page for every vocabulary,
   concept and collection in both files, and none for anything else in them.
2. **Given** `skos_base_uri` is `https://example.org/vocab/` and a concept's URI is
   `https://example.org/vocab/date-types/available`, **When** the site is built, **Then** the
   concept's page is at `date-types/available/` in the output.
3. **Given** a pattern in `skos_vocabularies` that is a relative path, **When** the site is built,
   **Then** it is read relative to the directory holding `conf.py`.
4. **Given** a vocabulary file that holds several vocabularies, **When** the site is built,
   **Then** each of them has its own page.
5. **Given** the same resource is described in two vocabulary files, **When** the site is built,
   **Then** it has one page, built from everything both files state about it.
6. **Given** a vocabulary file that also describes things that are not resources, such as an
   organisation or a bibliographic reference, **When** the site is built, **Then** none of them
   gets a page and the build emits no warning about them.
7. **Given** a resource whose URI does not start with the base URI, **When** the site is built,
   **Then** it gets no page and the build emits a warning naming its URI.
8. **Given** a resource whose URI would give it no page address, because it equals the base URI or
   holds a fragment (`#`) or a query (`?`), **When** the site is built, **Then** it gets no page and
   the build emits a warning naming its URI.
9. **Given** a page address that the site already uses for a document of its own, **When** the
   site is built, **Then** the site's own document is kept, no page is generated there, and the
   build emits a warning naming the address and the resource.
10. **Given** a pattern that matches no file, or a file that cannot be read as Turtle, **When** the
    site is built, **Then** the build emits a warning naming the pattern or the file, and every
    other file is still published.
11. **Given** `skos_vocabularies` is set but `skos_base_uri` is not, **When** the site is built,
    **Then** no page is generated and the build emits a warning saying the base URI is missing.
12. **Given** a site that has been built once, **When** a vocabulary file is edited, a resource
    removed from it, or a file added, and the site is built again without a clean, **Then** the
    output matches what a clean build of the edited files gives.
13. **Given** the generated pages, **When** the site is built, **Then** no warning is emitted about
    a generated page missing from a table of contents, and the site can put its vocabulary pages
    in a table of contents of its own.
14. **Given** the same site built under the default theme and under one other theme, **When** both
    builds finish, **Then** both emit no warnings and hold the same pages with the same content.
15. **Given** the site builds with the `html` builder instead of `dirhtml`, **When** it is built,
    **Then** it still has a page with its RDF copies for every resource, at the address that
    builder gives a document of that name.
16. **Given** the site's `language` is set, **When** the site is built, **Then** the fixed text the
    extension writes into its pages, such as section headings, is taken from Sphinx's message
    catalogue for that language, and no text from a vocabulary file is translated.

---

### User Story 2 - A reader looks up a resource and finds what they need to use it (Priority: P1)

Someone follows a concept's URI, or browses the site, and lands on the concept's page. It shows
them what they need to use the concept: its labels in every language, its definition, its
notation, its place in the vocabulary, the collections it is in and its mapping links to other
vocabularies. From a vocabulary's page they can reach every concept and collection in it, and
from a collection's page every member, in order when the collection is ordered. Every page also
shows everything else its resource's files say about it: who created and published it, its
licence, version and dates, its notes and sources, and any other property, so nothing the files
state is hidden from a reader except hidden labels.

**Why this priority**: A page with nothing a reader can use is no better than the Turtle file.
This is what the site is published for.

**Independent Test**: Build a test site from a vocabulary with labels in two languages, an ordered
collection, a notation and a mapping link to an outside URI, and check each page's content and
links in the built HTML.

**Acceptance Scenarios**:

1. **Given** a concept with preferred and alternative labels in two languages, **When** a reader
   opens its page, **Then** the page shows every one of those labels with its language.
2. **Given** a concept with hidden labels, **When** a reader opens its page, **Then** the hidden
   labels are not shown on it (they are still in its RDF copies).
3. **Given** a concept with a definition in two languages and a notation, **When** a reader opens
   its page, **Then** the page shows both definitions with their languages and the notation.
4. **Given** a concept with no preferred label in the site's `language`, **When** a reader opens
   its page, **Then** the page is titled with one of the concept's other preferred labels, chosen
   the same way on every build, and with its URI when it has no preferred label at all.
5. **Given** a concept that is a member of two collections, **When** a reader opens its page,
   **Then** the page links to both collections' pages.
6. **Given** a concept with broader, narrower or related concepts, stated on the concept itself or
   by the other concept, **When** a reader opens its page, **Then** the page links to each of them.
7. **Given** a concept with a mapping link whose target has a page on this site, **When** a reader
   opens its page, **Then** the mapping link goes to that page, and the page says which mapping
   property it is.
8. **Given** a concept with a mapping link to a URI that has no page on this site, **When** a
   reader opens its page, **Then** the mapping link goes to that URI, says which mapping property
   it is, and the build emits no warning about it.
9. **Given** any page that shows a resource URI, **When** a reader opens it, **Then** the page
   shows the URI of the resource it describes.
10. **Given** a vocabulary with concepts and collections, **When** a reader opens its page,
    **Then** it shows the vocabulary's labels and definition or description, and links to every
    concept and every collection in it.
11. **Given** an ordered collection, **When** a reader opens its page, **Then** it links to every
    member in the order the collection gives them.
12. **Given** an unordered collection, **When** a reader opens its page, **Then** it links to every
    member, in the same order on every build.
13. **Given** a concept's page, **When** a reader opens it, **Then** it links to the page of the
    vocabulary the concept is in.
14. **Given** a label or definition that holds characters with a meaning in HTML, **When** a reader
    opens the page, **Then** the characters are shown as text and nothing in them is interpreted
    as markup.
15. **Given** a vocabulary with a creator, publisher, licence, version and modified date, **When**
    a reader opens its page, **Then** each of them is shown in a field of its own.
16. **Given** a concept with a scope note, a note, an example, a history note, an editorial note
    or a change note, **When** a reader opens its page, **Then** each is shown in a field of its
    own.
17. **Given** a creator whose URI the files name, for example with `foaf:name`, **When** a reader
    opens the page, **Then** the creator is shown by that name and linked to its URI. A creator
    the files do not name is shown by its URI.
18. **Given** a resource stating a property the page has no field of its own for, **When** a
    reader opens its page, **Then** the property is shown in a field named by its prefixed name
    and linked to the property's URI, with each URI value linked and each literal shown with its
    language or datatype.
19. **Given** a property whose value is a blank node, such as a creator written as a blank node
    with a `foaf:name`, **When** a reader opens the page, **Then** the blank node's own statements
    are shown nested under the property.
20. **Given** any resource, **When** a reader opens its page, **Then** every statement the files
    make about the resource is shown, except its hidden labels, in the same order on every build.

---

### User Story 3 - Someone resolving a resource URI from software gets its RDF (Priority: P1)

Software that resolves a vocabulary URI reaches the resource's page, or a copy of it in the RDF
format it asks for. Every page has the resource's own RDF beside it in Turtle, JSON-LD, RDF/XML and
N-Triples, and names those copies with their media types in its `<link rel="alternate">`
elements, so software holding only the page can find them.

**Why this priority**: Machines resolving a URI are half of why a vocabulary is published (README,
"Why"). It is part of the agreed feature and blocks no other story.

**Independent Test**: Build a test site, parse every RDF copy of every page, and compare each graph
with the resource's own RDF read from the vocabulary file.

**Acceptance Scenarios**:

1. **Given** a resource's page, **When** the site is built, **Then** the page's directory holds
   the resource's RDF copies in Turtle, JSON-LD, RDF/XML and N-Triples.
2. **Given** any RDF copy, **When** it is parsed, **Then** its graph is the resource's own RDF as the
   vocabulary files state it: every triple with the resource as subject, plus the triples of the
   blank nodes those reach, with no triple added, dropped or changed.
3. **Given** an ordered collection, **When** its RDF copy is parsed, **Then** the member list,
   which is made of blank nodes, is complete and in order.
4. **Given** a concept whose broader concept states the narrower link, or a collection that lists
   the concept as a member, **When** the concept's RDF copy is parsed, **Then** neither statement
   is in it, because neither has the concept as subject.
5. **Given** a resource's page, **When** its HTML is read, **Then** it has one
   `<link rel="alternate">` element per RDF copy, each pointing at the copy and naming its media
   type (`text/turtle`, `application/ld+json`, `application/rdf+xml`, `application/n-triples`).
6. **Given** two builds of unchanged vocabulary files, **When** both finish, **Then** every page
   address and every RDF copy's file name is the same in both.

---

### User Story 4 - A site maintainer shows a resource in one of their own pages (Priority: P2)

A site maintainer writing a prose page, an introduction to a vocabulary or a guide to choosing a
concept, writes one of the `skos:vocabulary`, `skos:concept` or `skos:collection` directives with
a resource's URI. The resource's content appears in that page as it does on the generated page.

**Why this priority**: It lets a site be more than its generated pages (GOALS.md G8), but the site
is usable without it.

**Independent Test**: Build a test site with a prose page holding a `skos:concept` directive and
check that the concept's content appears in that page.

**Acceptance Scenarios**:

1. **Given** a prose page holding a `skos:concept`, `skos:vocabulary` or `skos:collection`
   directive with the URI of a resource in the vocabulary files, **When** the site is built,
   **Then** the page shows that resource's content as its generated page does.
2. **Given** a directive written by hand, **When** the site is built, **Then** the resource's
   generated page is still built, and it alone has the RDF copies and the
   `<link rel="alternate">` elements.
3. **Given** a directive whose URI names no resource in the vocabulary files, **When** the site is
   built, **Then** the build emits a warning naming the URI and the page.
4. **Given** a directive with no URI, or with a URI of a resource of a different kind than the
   directive (a vocabulary's URI in `skos:concept`), **When** the site is built, **Then** the build
   emits a warning naming the URI and the page.

---

### User Story 5 - A site maintainer publishes the site to GitHub Pages from their repository (Priority: P2)

A site maintainer whose vocabulary files are on GitHub adds a job of a few lines to a workflow
in their repository that calls the workflow sphinx-skos ships. A push to their default branch
builds the site and deploys it to GitHub Pages, and a pull request can build it without
deploying it.

**Why this priority**: Every repository that publishes a site would otherwise write the same
workflow (GOALS.md G5), but a site can be built and hosted without it.

**Independent Test**: Call the workflow from a vocabulary repository's branch, once installing
from the repository's own dependency group and once from a list of packages, and check that both
builds pass and upload the site.

**Acceptance Scenarios**:

1. **Given** a repository with a `docs` directory holding the site's `conf.py`, **When** a job
   calls the workflow with no inputs, **Then** the site is built with `dirhtml`, with warnings
   treated as errors, using the latest sphinx-skos, and deployed to the repository's GitHub
   Pages site.
2. **Given** a job that names the packages to install, such as a pinned sphinx-skos and a theme,
   **When** the workflow runs, **Then** those packages are installed and nothing else.
3. **Given** a job that names a dependency group of the repository's `pyproject.toml`, **When**
   the workflow runs, **Then** the repository's dependencies and that group are installed from
   its `uv.lock`, and the run fails when `uv.lock` is out of date.
4. **Given** a job that sets the workflow to build only, **When** the workflow runs, **Then** the
   site is built and uploaded as the `github-pages` artifact, and nothing is deployed.
5. **Given** a site whose build emits a warning, **When** the workflow runs, **Then** the run
   fails before anything is uploaded or deployed.
6. **Given** a job of the maintainer's own that needs the workflow's job, **When** the build
   finishes, **Then** that job can download the built site as the `github-pages` artifact.

---

### Edge Cases

- A resource outside the base URI is still shown on the pages that refer to it, linked to its URI
  (User Story 1, scenario 7, and User Story 2, scenario 8).
- A concept that is in no vocabulary in the files gets a page. Its page has no vocabulary to link
  to and no warning is emitted.
- A link to a URI under the base URI that names no resource in the files goes to that URI. The
  extension is not a validator and emits no warning.
- A vocabulary with no concepts or collections gets a page that shows its own content.
- A label with no language tag is shown as a label with no language.
- A blank node that the files make reach itself again is shown once, and the build ends.
- A property's prefixed name comes from the first vocabulary file to bind its prefix. Where two
  files bind one prefix to different namespaces, the second namespace gets the prefix with a
  number added, such as `ex1`.

## Requirements *(mandatory)*

### Functional Requirements

**Configuration and generation**

- **FR-001**: The extension MUST read the settings `skos_vocabularies` (a list of file patterns)
  and `skos_base_uri` (a URI) from the site's `conf.py`. Relative patterns are read from the
  directory holding `conf.py`. *(US1)*
- **FR-002**: The extension MUST generate one page for every `skos:ConceptScheme`, `skos:Concept`,
  `skos:Collection` and `skos:OrderedCollection` whose URI starts with the base URI, and for
  nothing else. Each generated page holds exactly one directive: `skos:vocabulary`,
  `skos:concept` or `skos:collection`. *(US1)*
- **FR-003**: The site maintainer MUST NOT need to write, keep or commit the generated pages. They
  are produced when the build starts. *(US1)*
- **FR-004**: A resource's page address MUST be its URI with the base URI removed, and depend on
  nothing else. Under `dirhtml` that address is a directory in the output. *(US1)*
- **FR-005**: When several vocabulary files describe the same resource, its page and RDF copies
  MUST be built from all of their statements together. *(US1)*
- **FR-006**: The build MUST emit a warning, naming what it concerns, and continue, for each of:
  a resource outside the base URI; a resource with no possible page address; a page address the
  site already uses; a pattern that matches no file; a file that cannot be read as Turtle; a
  missing `skos_base_uri`. In each case nothing is generated for what the warning names, and
  everything else is. *(US1)*
- **FR-007**: A rebuild after a vocabulary file changes, a file is added or removed, or a
  resource is added or removed MUST give the same output as a clean build. *(US1)*
- **FR-008**: Generated pages MUST NOT cause warnings about documents missing from a table of
  contents, and the site MUST be able to include vocabulary pages in its own tables of contents.
  *(US1)*
- **FR-009**: Every fixed piece of text the extension writes into a page MUST be marked for
  translation through Sphinx's message catalogue. Text from a vocabulary file MUST NOT be
  translated. *(US1)*

**Page content**

- **FR-010**: A concept's page MUST show its URI, its preferred and alternative labels with their
  languages, its definitions with their languages, its notations, a link to its vocabulary, links
  to the collections it is a member of, links to its broader, narrower and related concepts
  (stated in either direction), and its mapping links, each with the mapping property it uses.
  *(US2)*
- **FR-011**: Hidden labels MUST NOT be shown on a page. *(US2)*
- **FR-012**: A vocabulary's page MUST show its URI, its labels, its definition or description,
  and links to every concept and every collection in it. *(US2)*
- **FR-013**: A collection's page MUST show its URI, labels and definition, and link to every
  member. An ordered collection's members MUST be in the collection's order. *(US2)*
- **FR-025**: Every page MUST show every statement the vocabulary files make about its resource,
  other than its hidden labels. *(US2)*
- **FR-026**: Every page MUST show each of these in a field of its own when the resource states
  it: `dcterms:title`, `dcterms:description`, `skos:notation`, `skos:scopeNote`, `skos:note`,
  `skos:example`, `skos:historyNote`, `skos:editorialNote`, `skos:changeNote`,
  `dcterms:creator`, `dcterms:contributor`, `dcterms:publisher`, `dcterms:created`,
  `dcterms:issued`, `dcterms:modified`, `owl:versionInfo`, `dcterms:license`, `dcterms:rights`,
  `dcterms:identifier`, `dcterms:language`, `dcterms:source`, `dcterms:bibliographicCitation` and
  `rdfs:seeAlso`. *(US2)*
- **FR-027**: Every other property a resource states MUST be shown in a field named by its
  prefixed name, from the prefixes of the vocabulary files, or by its URI where no prefix covers
  it, and linked to the property's URI. *(US2)*
- **FR-028**: A URI value MUST be shown as a link, by its page's title when it has a page,
  else by the name the files give it with `skos:prefLabel`, `foaf:name`, `schema:name`,
  `rdfs:label` or `dcterms:title`, else by the URI. A literal MUST be shown with its language
  tag, or its datatype when it has no language. A blank node MUST be shown as its own
  statements, nested under the property, as deep as the files go. *(US2)*
- **FR-014**: A link to a resource that has a page on the site MUST go to that page. A link to
  any other URI MUST go to the URI itself, without a warning. *(US2)*
- **FR-015**: A page's title MUST be the resource's preferred label in the site's `language`, or,
  failing that, a preferred label chosen the same way on every build, or, failing that, its URI.
  Every order on a page that the vocabulary does not fix MUST be the same on every build. *(US2)*
- **FR-016**: Text from a vocabulary file MUST reach a page only as document content that the
  HTML writer escapes. *(US2)*

**RDF copies**

- **FR-017**: Every generated page MUST have the resource's RDF copies in its own output
  directory, in Turtle, JSON-LD, RDF/XML and N-Triples. *(US3)*
- **FR-018**: Each RDF copy MUST hold exactly the resource's own RDF as the vocabulary files state
  it: every triple with the resource as subject, plus the triples of the blank nodes those reach.
  Nothing is added, dropped, rewritten or inferred. *(US3)*
- **FR-019**: Every generated page MUST name each of its RDF copies in a `<link rel="alternate">`
  element with the copy's media type. *(US3)*
- **FR-020**: An RDF copy's file name MUST depend only on the page address and the format. *(US3)*

**Directives by hand**

- **FR-021**: The `skos:vocabulary`, `skos:concept` and `skos:collection` directives MUST take a
  resource URI and, in a prose page, show the same content as on the resource's generated page.
  *(US4)*
- **FR-022**: A directive used by hand MUST NOT produce RDF copies or `<link rel="alternate">`
  elements. *(US4)*
- **FR-023**: A directive with no URI, a URI naming no resource, or a URI naming a resource of a
  different kind MUST emit a warning naming the URI and the page. *(US4)*

**Look and feel**

- **FR-024**: The extension MUST add no stylesheet, script, HTML template, image, static file or
  theme option, and its pages MUST build without warnings under any Sphinx HTML theme.
  *(US1, US2)*

**Publishing to GitHub Pages**

- **FR-029**: The repository MUST ship a reusable GitHub Actions workflow,
  `.github/workflows/build-site.yml`, that builds a site with `sphinx-build -b dirhtml -W` and
  deploys it to GitHub Pages. Its inputs MUST be the docs directory (default `docs`), the Python
  version, the packages to install (default `sphinx-skos`), a dependency group to install from the
  repository's `uv.lock` instead, and whether to deploy (default yes). *(US5)*
- **FR-030**: The workflow MUST upload the built site as the `github-pages` artifact whether or
  not it deploys. *(US5)*

### Key Entities

- **Resource**: a vocabulary, a concept or a collection under the base URI, with its page address.
- **Own RDF**: a resource's triples as subject, plus those of the blank nodes they reach.
- **RDF copy**: one format of a resource's own RDF, in the page's directory.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A site listing the nine vocabulary files of
  [fairdm-vocabularies](https://github.com/FAIR-DM/fairdm-vocabularies) builds with `dirhtml` and
  warnings treated as errors, under the default theme and under one other theme.
- **SC-002**: A site listing the fifteen vocabulary files of
  [ihfc-vocabularies](https://github.com/ihfc-iugg/ihfc-vocabularies) does the same.
- **SC-003**: In both sites, every vocabulary, concept and collection in the files has a page at
  its URI with the base URI removed: 100% of them, and no page for anything else.
- **SC-004**: In both sites, every RDF copy of every page, in all four formats, parses to a graph
  isomorphic to the resource's own RDF read from the files.
- **SC-005**: In both sites, every page names all four of its RDF copies in
  `<link rel="alternate">` elements with their media types.
- **SC-006**: A site maintainer publishes a vocabulary file with three settings in `conf.py` and
  no page written by hand.

## Clarifications

### Session 2026-10-28

- Q: What happens to a resource whose URI is not under `skos_base_uri`? → A: It gets no page and
  the build warns, naming its URI. Pages that refer to it link to its URI.
- Q: What happens to a mapping link or any other link to a URI outside the site? → A: It links to
  the URI itself, with no warning. Only resources the files define get pages.
- Q: Which labels does a page show? → A: Preferred and alternative labels in every language.
  Hidden labels stay out of the page, as the SKOS Reference intends them for search, and remain in
  the RDF copies.
- Q: Does a concept page show its place in the hierarchy? → A: Yes. It links to its broader,
  narrower and related concepts, whichever concept states the link, as a reader cannot use a
  concept's page without them. The RDF copy still holds only the concept's own triples.
- Q: Which properties does a page show? → A: Every statement the files make about the resource
  except hidden labels. Common metadata (Dublin Core, `owl:versionInfo`, the SKOS notes,
  `rdfs:seeAlso`) gets a field of its own, and every other property a field named by its
  prefixed name, so no statement is hidden from a reader.
- Q: Does a directive written by hand produce RDF copies? → A: No. A resource has one page with
  its copies, its generated page, so its URI resolves to one place.

## Assumptions

- The vocabulary files are Turtle, as `CONTEXT.md` defines a vocabulary file.
- Linking to a resource from a prose page with a cross-reference role, an index of all
  vocabularies, and search are out of scope.
- Releasing the package is out of scope.
- Look and feel is out of scope permanently (G6, constitution Article X).
