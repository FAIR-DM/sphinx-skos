# FS-001 research

Read against `main` at `2d22de9`, Sphinx 9.2.0, docutils 0.23 and rdflib 7.6.0 as resolved in the
project's virtual environment. `spec.md` has no `planning-notes.md` beside it and no sketch.

## R1. How a generated page becomes a Sphinx document

**Finding.** Sphinx reads every document from a file in the source directory. `Project.discover`
(`sphinx/project.py:49`) builds the document list by walking the source directory, and
`Builder.read_doc` (`sphinx/builders/__init__.py:632`) opens `env.doc2path(docname)` with
`read_text`. There is no public way to give Sphinx a document that has no file. The only route
without a file goes through the private `Project._docname_to_path` mapping.

**Decision.** Write each generated page as a small reStructuredText file in the source directory
when the build starts, from a `builder-inited` handler, the way `sphinx.ext.autosummary` writes its
stub pages. `GOALS.md` names this design ("the way `autosummary` generates its stubs"). The file
holds a marker comment, `:orphan:` and one directive. A document's name is its page address, so
the file sits where the address says: `https://example.org/vocab/date-types/available` with base
`https://example.org/vocab/` is `date-types/available.rst`.

- A file is rewritten only when its text changes, so an unchanged page keeps its modification
  time and Sphinx does not read it again for that reason.
- A file carrying the marker whose resource is gone is deleted at the next build, together with
  the HTML page and RDF copies Sphinx wrote for it, since Sphinx itself never removes the output
  of a removed document. That is what makes a rebuild match a clean build (FR-007).
- A file without the marker is the site's own and is never written over or deleted (FR-006,
  US1 scenario 9).

**Rejected.** Registering documents through `Project._docname_to_path`: it is private, it can
change in any Sphinx release, and a reader of the code could not tell why it works. Rendering
pages through `html-collect-pages` (as ablog does): those pages are not Sphinx documents, which G1
requires, and they need an HTML template, which Article X forbids.

**Consequence for the site maintainer.** The generated files appear in the source directory after
a build. They need not be written, kept or committed (FR-003): every build rewrites them, and a
site that keeps its source directory under version control lists them in `.gitignore`. The README
says so.

## R2. Rebuilding after a vocabulary file changes

**Finding.** A generated page's text names only a URI, so it does not change when the vocabulary
file does, and Sphinx's own outdated-file check (`env.get_outdated_files`,
`sphinx/environment/__init__.py:521`) would leave the page stale. A concept page also shows the
labels of the concepts and collections it links to, which may come from other files.

**Decision.** Keep a fingerprint of the vocabulary files, the SHA-256 of each matched file's bytes
in pattern order, in the domain's data, which Sphinx pickles with the environment. In an
`env-get-outdated` handler, when the fingerprint differs from the last build's, return every
document in the site, so all of them are read again. Returning only the documents that use a
directive would mean recording, merging and purging that set per document, for a saving only on
the site's few prose pages. Settings changes are already
covered: `skos_vocabularies` and `skos_base_uri` are registered with `rebuild="env"`.

## R3. Tables of contents

**Finding.** A document in no table of contents raises "document isn't included in any toctree"
(`sphinx/environment/__init__.py:811`) unless its metadata says `orphan`. A document listed in
two tables of contents raises "document is referenced in multiple toctrees" (line 952), so giving
each concept a place under its vocabulary's table of contents fails as soon as a concept is in two
vocabularies.

**Decision.** Every generated page carries `:orphan:`. A site lists vocabulary pages in its own
`toctree` by page address (`date-types`), and that works on an orphan page.

## R4. The RDF copies

**Finding.** rdflib 7.6.0 serialises all four formats without a plug-in: `turtle`, `json-ld`,
`xml` and `nt`. `Graph.cbd(resource, include_reifications=False)` is exactly a resource's own RDF:
every triple with it as subject, plus the triples of the blank nodes those reach, recursively
(`rdflib/graph.py:2025`, rules 1 and 2 of the Concise Bounded Description). Rule 3, reifications,
would add triples, which is why `include_reifications=False`.

**Decision.** rdflib becomes the runtime dependency (Article VII: reading Turtle and writing four
RDF formats is the whole job of the package and there is no smaller way to do it). The copies are
written from the `html-page-context` handler for each generated page, beside the page's HTML file,
named after it with the format's suffix:

| Builder | Page | Copies |
|---|---|---|
| `dirhtml` | `date-types/available/index.html` | `date-types/available/index.ttl`, `index.jsonld`, `index.rdf`, `index.nt` |
| `html` | `date-types/available.html` | `date-types/available.ttl`, `available.jsonld`, `available.rdf`, `available.nt` |

The name depends only on the page address and the format (FR-020). Under `dirhtml` the copies
share the base name `index` with the page, so a web server negotiating content on the directory
(Apache `MultiViews` with `DirectoryIndex index`) picks the right file from the `Accept` header
with no lookup table. These names are permanent once released (decision 16).

**Media types**: `text/turtle`, `application/ld+json`, `application/rdf+xml`,
`application/n-triples`.

## R5. The `<link rel="alternate">` elements

**Finding.** Both themes the tests use render the `metatags` context value in the page head:
`sphinx/themes/basic/layout.html:99` (alabaster extends `basic`) and
`furo/theme/furo/base.html:9`. The `html-page-context` event (`sphinx/builders/html/__init__.py:1188`)
passes the context before rendering.

**Decision.** Append one `<link rel="alternate" type="…" href="…">` per copy to
`context["metatags"]`. The `href` is the copy's file name relative to the page, so it works under
any base URL. Both attribute values pass through `html.escape(…, quote=True)`. No vocabulary text
goes into the element: the media type is fixed and the file name is derived from the address.
Adding to `metatags` adds no template, so Article X holds.

## R6. Links between pages

**Finding.** A link to another document has to be resolved per builder, because `dirhtml` and
`html` give the same document different relative URIs. Sphinx's standard domain resolves
`pending_xref` nodes with `refdomain="std"`, `reftype="doc"` and an absolute target (`/date-types`)
for exactly this.

**Decision.** Where a linked URI has a generated page, the directive emits that `pending_xref`
with `refexplicit=True` and the linked resource's title as its text. Every other URI becomes a
`nodes.reference` with `refuri` set to the URI itself and no warning (FR-014). Which URIs have
pages is known before any document is read, because the pages are worked out at `builder-inited`.
No custom role and no `resolve_xref` is needed.

## R7. Directive names and where the extension keeps its state

**Decision.** A `Domain` named `skos` holds the three directives, so they are `skos:vocabulary`,
`skos:concept` and `skos:collection` (constitution Article IX names the domain as Sphinx's
grouping for this). The domain instance also holds the loaded vocabularies and the generated-page
table for the build. Sphinx creates domains afresh for each build and does not pickle them
(`env.__getstate__`, `sphinx/environment/__init__.py:242`), so the parsed graph is never written
into the environment pickle. Parallel reading and writing fork after `builder-inited`, so the
workers inherit it.

## R8. Translation of fixed text

**Finding.** `sphinx.locale.get_translation(catalog)` (`sphinx/locale/__init__.py:181`) returns a
function that translates through the catalogue registered with `app.add_message_catalog`, and
returns the text unchanged when none is registered.

**Decision.** Every fixed string the extension writes into a page goes through
`translate = get_translation("sphinx_skos")`. The package ships no translations yet, so it registers no
catalogue. The test of FR-009 registers a catalogue of its own from the test site's `conf.py`
`setup()` and checks that a heading comes from it while a vocabulary label equal to the same
message is left as written.

## R9. Page content that SKOS leaves open

- **A concept's vocabularies**: `skos:inScheme`, `skos:topConceptOf`, and the scheme's
  `skos:hasTopConcept`. Every concept in both real vocabulary sets states `skos:inScheme`.
- **A vocabulary's collections**: neither real set states `skos:inScheme` on a collection (0 of 39
  collections). A collection is in a vocabulary when it states `skos:inScheme` for it, or when one
  of its members is a concept in it.
- **A collection's members**: `skos:member`, or the `skos:memberList` list of an ordered
  collection, in list order (US2 scenario 11). Unordered members, and every other list the
  vocabulary does not order, are sorted by title and then URI (FR-015).
- **A concept's collections**: collections whose `skos:member` or `skos:memberList` names it.
- **The page title** (FR-015): the `skos:prefLabel` in `config.language`, else the first preferred
  label sorted by language tag then text, else the URI. The same rule names every linked resource.

## R10. Page addresses that cannot be used

A URI is under the base URI when it starts with it. The rest is the page address. It cannot be
used, and gets the "no page address" warning, when it is empty, holds `#` or `?` (decision 4), or
when any of its `/`-separated segments is empty, `.` or `..`, or it starts with `/`. The last
three cases would put a generated file outside the page's own place in the source directory. An
address ending in `/` is the document `<address>index`, which both builders put at the same place.

A page address is already used by the site when the source directory has a document at that
name, or at `<address>/index`, in any of the site's `source_suffix` suffixes, that is not a file
the extension generated (decision 7).

## Both real vocabulary sets

| | fairdm-vocabularies | ihfc-vocabularies |
|---|---|---|
| Files | 9 | 15 |
| Base URI | `https://w3id.org/fairdm/vocabularies/` | `https://portal.heatflow.world/vocabularies/` |
| Vocabularies | 9 | 15 |
| Concepts | 127 | 186 |
| Collections | 19 ordered | 20 unordered |
| Blank nodes | 87 (member lists) | 0 |
| Labels | `en` only | `en` only, with `altLabel` and `hiddenLabel` |
| Other resources | organisations | organisations |

No resource URI in either set ends in `/` or holds `#`, and none is outside its base URI.

## What already exists

```
own RDF of a resource             · 3, package · rdflib.Graph.cbd(include_reifications=False)
reading Turtle, writing 4 formats · 3, package · rdflib parsers and serializers
graph comparison in tests         · 3, package · rdflib.compare.isomorphic
generated source pages            · 7, new     · searched Sphinx for document providers without files (none public), autosummary's generator (writes files the same way, but for Python objects)
rebuild on vocabulary change      · 7, new     · Sphinx's env-get-outdated event is the hook; no extension provides a file fingerprint for non-document inputs
cross-page links                  · 3, package · sphinx std domain, pending_xref reftype "doc"
links to outside URIs             · 3, package · docutils nodes.reference(refuri=…)
directive namespace               · 3, package · sphinx.domains.Domain
title, field and list nodes       · 3, package · docutils nodes (section, title, field_list, bullet_list)
alternate links in the head       · 3, package · Sphinx html-page-context "metatags"
escaping of attribute values      · 4, stdlib  · html.escape
translation of fixed text         · 3, package · sphinx.locale.get_translation
file patterns                     · 4, stdlib  · glob.glob(recursive=True)
fingerprint of files              · 4, stdlib  · hashlib.sha256
warnings with locations           · 3, package · sphinx.util.logging.getLogger, SphinxDirective.get_location
```
