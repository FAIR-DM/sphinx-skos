# Implementation Plan: Build a documentation site from SKOS vocabulary files

**Branch**: `001-vocabulary-site` | **Date**: 2026-10-28 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-vocabulary-site/spec.md`, research in
[research.md](research.md).

## Summary

When the build starts, the extension reads the vocabulary files listed in `skos_vocabularies` into
one RDF graph, works out a page address for every vocabulary, concept and collection under
`skos_base_uri`, and writes one small reStructuredText file per resource into the source
directory, each holding `:orphan:` and one directive. The `skos` domain's three directives turn a
URI into a titled section of docutils nodes: labels, definitions, notations and links. When each
generated page is written as HTML, the extension writes the resource's own RDF beside it in four
formats and names the copies in `<link rel="alternate">` elements. The same directives can be
written by hand in any page and then produce the content only.

## Technical Context

**Language/Version**: Python 3.12 to 3.14

**Primary Dependencies**: Sphinx 9.0 or later, docutils (through Sphinx), rdflib 7.6 or later
(new runtime dependency, research R4)

**Storage**: files only. The site's vocabulary files are read. Generated page sources are written
into the site's source directory, RDF copies into the output directory.

**Testing**: pytest with `sphinx.testing` (`app` fixture, `@pytest.mark.sphinx`), test sites under
`tests/roots/test-<name>/`, RDF compared with `rdflib.compare.isomorphic`. furo joins the dev
dependencies as the second theme (decision 19).

**Target Platform**: any platform Sphinx runs on

**Project Type**: library (Sphinx extension)

**Performance Goals**: none stated. The larger real set (ihfc, 221 resources) must build in
seconds.

**Constraints**: no stylesheet, script, template, image, static file or theme option (FR-024,
Article X). No vocabulary text joined into HTML strings (Article V).

**Scale/Scope**: the two real sets: 155 and 221 resources.

## Constitution Check

| Article | How the plan holds to it |
|---|---|
| I Testing | Every behaviour is built test-first against a real site build. No test asserts wording or appearance. |
| II Simplicity | One graph, one pass at `builder-inited`, no caching beyond Sphinx's own. |
| III Anti-abstraction | One base class, `ResourceDirective`, with three present subclasses. No other base class. |
| IV Integration-first | Tests build sites through `sphinx.testing` and read the output directory and doctrees. |
| V Security | Vocabulary text reaches pages only as docutils `Text` nodes and `refuri` attributes. The alternate links are built from fixed media types and file names derived from the page address, escaped with `html.escape`. Addresses that would leave the page's place in the source directory (`.`, `..`, empty segments, a leading `/`) get no page. Vocabulary files are only read. |
| VI Documentation | Each story updates README, CHANGELOG and the `docs/` pages for the names it introduces. |
| VII Dependencies | rdflib, with its reason in research R4. furo is a dev dependency only. |
| VIII i18n | Fixed text through `get_translation("sphinx_skos")`. Vocabulary text never translated. |
| IX Cohesion | `Vocabularies`, `GeneratedPages` and `RdfCopies` classes group their subjects. Directives are `SphinxDirective` subclasses inside a `Domain`. Event handlers are module functions connected in `setup()`. |
| X Content only | No static or template files. Alternate links go into the theme's existing `metatags`. |
| XI Nothing site-specific | All URIs come from `conf.py`. Test sites use `https://example.org/…`. |
| XII Files are the truth | RDF copies are `Graph.cbd(uri, include_reifications=False)`, serialised as is. |
| XIII Stable addresses | Address is the URI with the base removed. Copy names depend only on the address and the format. |
| XIV Stack | Python 3.12+, Sphinx 9.0+, uv, hatchling. |

No violation to justify.

## Design

### Modules

```text
sphinx_skos/
├── __init__.py       # setup(): settings, domain, event handlers
├── vocabularies.py   # Vocabularies: load and merge files, read SKOS facts from the graph
├── pages.py          # GeneratedPages: addresses, collisions, writing and removing sources
├── domain.py         # SKOSDomain: the three directives, the build's state, the fingerprint
├── directives.py     # ResourceDirective and VocabularyDirective, ConceptDirective, CollectionDirective
└── copies.py         # RdfCopies: the four files and the alternate links for one page
```

Tests mirror it: `tests/test_vocabularies.py`, `tests/test_pages.py`, `tests/test_domain.py`,
`tests/test_directives.py`, `tests/test_copies.py`, with `tests/test_smoke.py` kept. The
`setup()` wiring in `__init__.py` is exercised through those builds and `tests/test_smoke.py`.

### Settings

- `skos_vocabularies`: list of glob patterns, default `[]`, `rebuild="env"`. Relative patterns
  are joined to `app.confdir`. `glob.glob(pattern, recursive=True)`, sorted, duplicates dropped.
- `skos_base_uri`: string, default `""`, `rebuild="env"`.

### `Vocabularies` (`vocabularies.py`)

Built once per build from the settings and the configuration directory.

- **Loading**: each matched file is parsed into a graph of its own with `format="turtle"`, then
  added to the merged graph, so a file that fails to parse adds nothing. A pattern matching no
  file warns naming the pattern. A file that fails to parse warns naming the file. Every other
  file still loads (FR-006).
- **`fingerprint`**: SHA-256 over each loaded file's path and bytes, in order (research R2).
- **`resources`**: URI to kind (`vocabulary`, `concept`, `collection`) for every subject typed
  `skos:ConceptScheme`, `skos:Concept`, `skos:Collection` or `skos:OrderedCollection`. Nothing
  else is a resource, and other subjects never warn (US1 scenario 6).
- **`own_rdf(uri)`**: `graph.cbd(uri, include_reifications=False)`.
- **Reading facts** for one URI, each returning a list in a fixed order: labels by property
  (`prefLabel`, `altLabel`), definitions, notations, title (research R9), vocabularies of a
  concept, collections of a concept, broader, narrower and related in both directions (decision
  12), mapping links as (property, target) for the five mapping properties, a vocabulary's
  concepts and collections, and a collection's members (`memberList` order, else sorted).
  Every list the vocabulary does not order is sorted by title, then URI.

### `GeneratedPages` (`pages.py`)

Built at `builder-inited` from `Vocabularies`, the base URI, the source directory and the source
suffixes.

- **Page address** (research R10): the URI with the base removed, refused when empty, holding `#`
  or `?`, starting with `/`, or having an empty, `.` or `..` segment. Document name: the address,
  or `<address>index` when the address ends in `/`.
- **Warnings**, each naming its subject and each leaving that resource without a page: outside the
  base URI, no page address, address already used by the site (naming the address and the
  resource). With `skos_vocabularies` set and `skos_base_uri` empty, one warning and no pages at
  all.
- **Sources**: `<srcdir>/<docname>.rst` holding a marker comment line, `:orphan:` and one
  directive with the URI. Written only when the text differs from what is on disk.
- **Clean-up**: every `.rst` file under the source directory whose first line is the marker and
  whose document name is no longer generated is deleted, with the builder's output file for it
  (`builder.get_outfilename(docname)`) and its RDF copies, when they exist. Files without the
  marker are never touched. Directories the build writes into (`outdir`, `doctreedir`) are skipped
  when they sit inside the source directory.
- **`docname_for(uri)`**: the generated document for a URI, or `None`. This is what links and RDF
  copies ask.

### `SKOSDomain` (`domain.py`)

- `name = "skos"`, directives `vocabulary`, `concept`, `collection`, no roles.
- `initial_data = {"fingerprint": ""}`. `clear_doc` and `merge_domaindata` have nothing per
  document to clear or merge.
- Instance attributes `vocabularies` and `pages`, set by the `builder-inited` handler. Never
  pickled (research R7).

### Event handlers (`__init__.py`)

- `builder-inited`: build `Vocabularies` and `GeneratedPages`, write and clean the sources, store
  both on the domain.
- `env-get-outdated`: when the domain's stored fingerprint differs from the current one, store the
  new one and return every found document (research R2).
- `html-page-context`: for a page whose name `GeneratedPages` generated, call `RdfCopies` to write
  the four files and append the alternate links to `context["metatags"]`. Only for builders whose
  `format` is `html`.

### Directives (`directives.py`)

`ResourceDirective(SphinxDirective)` takes one required argument, the URI, and no content. Its
`run()`:

1. Looks the URI up in the domain's `Vocabularies`. Not a resource, or a resource of another kind
   than the directive's: warning naming the URI, at `self.get_location()`, and no nodes (FR-023).
   A missing argument is refused by docutils' own argument check, which reports at the page.
2. Returns one `nodes.section` whose `nodes.title` is the resource's title, with a
   `nodes.field_list` below it. Fields appear only when they have values, except the URI, which
   always appears.
3. A link to a URI with a generated page is a `pending_xref` (`refdomain="std"`, `reftype="doc"`,
   `reftarget="/" + docname`, `refexplicit=True`) around the target's title. Any other link is a
   `nodes.reference` with `refuri` set to the URI and the URI as its text (research R6).
4. Field names are fixed text through `_ = get_translation("sphinx_skos")`. A label shown with its
   language puts the tag in its own text node beside the label. A label with no tag shows no tag.
   Vocabulary text only ever goes into `nodes.Text`.

| Directive | Fields, in order |
|---|---|
| `skos:concept` | URI · preferred labels · alternative labels · definitions · notations · vocabulary · collections · broader · narrower · related · one field per mapping property used |
| `skos:vocabulary` | URI · preferred labels · alternative labels · definitions · descriptions (`dcterms:description`) · concepts · collections |
| `skos:collection` | URI · preferred labels · alternative labels · definitions · members |

Hidden labels never appear (FR-011). A vocabulary's "definition or description" (FR-012) is
`skos:definition`, and `dcterms:description` as a field of its own, since both real sets use
`dcterms:description`.

### `RdfCopies` (`copies.py`)

For one generated page: the four formats as (suffix, rdflib format, media type):
`.ttl`/`turtle`/`text/turtle`, `.jsonld`/`json-ld`/`application/ld+json`,
`.rdf`/`xml`/`application/rdf+xml`, `.nt`/`nt`/`application/n-triples`. Each copy is written to
the page's output file with its suffix replaced (research R4). The alternate links use the copy's
bare file name as `href`.

### Test sites

Under `tests/roots/`, URIs under `https://example.org/vocab/`:

- `test-vocabularies`: two files matched by one pattern, holding two vocabularies, concepts with
  labels in two languages, hidden labels, a notation, an ordered and an unordered collection,
  broader, narrower and related links stated from either side, a mapping link to a concept with a
  page and one to an outside URI, a resource outside the base URI, an organisation, a concept in
  no vocabulary, a vocabulary with no concepts, a label with no language, and a label holding
  `<b>&amp;</b>`. One resource is described in both files. Tests for a clean build use a root
  without the resource outside the base URI.
- Further small roots only where a scenario needs a different `conf.py` or a page of the site's
  own: missing base URI, a pattern matching nothing and an unreadable file, an address collision,
  a translation catalogue, a prose page with hand-written directives.

Tests that need a rebuild copy a root into `tmp_path` and build it twice with `make_app`.

### Real vocabulary sets

SC-001 and SC-002 are checked at the end of the build on the real files, outside the test suite,
because the files belong to other repositories (Article XI). Both sets are built with `dirhtml`,
`-W`, under alabaster and furo, into `/home/sam/projects/worktrees/`.

## Project Structure

### Documentation (this feature)

```text
specs/001-vocabulary-site/
├── spec.md
├── decisions.md
├── research.md
├── plan.md
└── tasks.md
```

### Source Code (repository root)

```text
sphinx_skos/          # the modules above
tests/
├── conftest.py
├── roots/test-*/     # test sites
└── test_*.py         # mirrors sphinx_skos/
docs/
├── index.md
├── how-to/
└── reference/
```

**Structure Decision**: the single package layout the scaffold already has.

## Complexity Tracking

Nothing to justify.
