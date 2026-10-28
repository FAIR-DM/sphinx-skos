# FS-001 decisions

Choices made where issue #4 and `GOALS.md` were silent. Each is settled for this feature and can
be overruled at review of the specification.

## Scope

1. **One feature covers G1 to G4, G7 and G8.** Issue #4 describes them as one thing a site
   maintainer does, and none of them is useful alone. G5 and G6 are constraints every requirement
   holds to, not stories.
2. **Four stories, by who does what.** A site maintainer publishing their files (US1), a reader
   using a page (US2), software resolving a URI (US3), and a site maintainer writing a directive
   by hand (US4). Configuration settings, warnings and rebuilds are scenarios under US1, because
   nobody sets out to do any of them on their own.

## Addresses and warnings

3. **A resource outside the base URI gets no page and a build warning naming its URI.** It cannot
   be given an address that a redirect from its URI would reach. Warning rather than error, the
   Sphinx convention: a site that wants it to fail builds with warnings treated as errors.
4. **A URI that would give an empty address, or holds `#` or `?`, is treated the same way.** A
   fragment never reaches the server and a query is not a directory, so neither can be a page
   address under `dirhtml`.
5. **Things in a vocabulary file that are not resources** (organisations, bibliographic
   references, both present in the fixture vocabularies) get no page and no warning. They are
   outside what the extension publishes, not a problem in the file.
6. **Links to URIs with no page on the site link to the URI, with no warning.** That covers
   mapping links to other vocabularies and links to resources outside the base URI. Checking that
   such a URI exists is a validator's job (README, "What it is not").
7. **A page address the site already uses keeps the site's document**, with a warning. The site's
   own pages are the maintainer's work, and overwriting them silently would lose it.
8. **A missing base URI generates nothing and warns.** No address can be derived without it.
9. **Relative patterns are read from the directory holding `conf.py`**, as Sphinx reads
   `html_static_path` and similar settings.
10. **The same resource in two files is merged.** The files together are the truth (README,
    "When choices collide", 1), so its page and copies hold every statement about it.

## Page content

11. **Hidden labels are not shown.** The SKOS Reference intends them for text search, not display.
    They remain in the RDF copies, which hold everything.
12. **Concept pages link to broader, narrower and related concepts, stated in either direction.**
    G4's list does not name them, but a reader cannot place a concept without them, and the
    fixture vocabularies use `skos:related`. The page may show what other resources state about
    a concept (its collections, its narrower concepts). Its RDF copy may not, following
    django-controlled-vocabularies' definition of a row's RDF (its ADR 0028).
13. **Other notes and Dublin Core metadata are not shown in this feature.** They are in the RDF
    copies. Showing them is a later change to this feature's pages, not a new feature.
14. **The page title is the preferred label in the site's `language`, falling back to a preferred
    label chosen the same way every build, then the URI.** Every order the vocabulary does not fix
    (unordered collection members, a vocabulary's concepts) is the same on every build, so
    rebuilding unchanged files changes nothing.
15. **The html builder is supported but the address guarantee is stated for `dirhtml`.** Under
    `html` a page is a file, not a directory, so a redirect from the URI needs a suffix.

## RDF copies

16. **Copies sit in the page's own output directory and their file names depend only on the page
    address and the format.** The exact names are a planning decision. They must not change once
    released (constitution Article XIII), as a redirect or content-negotiation rule may name them.
17. **A directive written by hand produces no copies and no alternate links.** A resource resolves
    to one page, its generated one.

## Tables of contents

18. **Generated pages emit no table-of-contents warning, and a site can list vocabulary pages in
    its own table of contents.** Without this a build of the fixture vocabularies could not be
    warning-free (SC-001, SC-002). How the generated pages are reached is a planning decision.

## Testing

19. **Themes tested are the default (alabaster) and furo**, installed in the development
    dependencies. The success criteria name "one other theme" so the choice can change.

## Planning

## D20 — Generated pages are source files written into the site's source directory

Sphinx reads every document from a file in the source directory and has no public way to add one
without a file (research R1). The extension writes one small reStructuredText file per resource
when the build starts, as `GOALS.md` and `sphinx.ext.autosummary` do, marks it as generated, and
removes it with its output once its resource is gone. A site that keeps its sources under version
control lists the generated files in `.gitignore`.

**Why:** the only route without files goes through Sphinx's private document table.
**Revisit if:** Sphinx gains a public way to provide a document without a file.

## D21 — Every generated page is an orphan

A concept in two vocabularies would be in two tables of contents, which Sphinx warns about, so
generated pages are reached by links and by the site's own tables of contents, never by one the
extension writes (research R3).

## D22 — RDF copy names follow the page's HTML file

Under `dirhtml` the copies are `index.ttl`, `index.jsonld`, `index.rdf` and `index.nt` in the
page's directory, so a web server negotiating content on the directory finds them with no lookup
table. Under `html` they are the page's file name with its suffix replaced (research R4).

## D23 — A collection is in a vocabulary when it says so or when a member is

Neither real vocabulary set states `skos:inScheme` on a collection. A vocabulary's page lists a
collection that states `skos:inScheme` for it or has a member in it (research R9).

## D24 — A vocabulary's description is shown beside its definition

FR-012 asks for "its definition or description". Both real sets describe their vocabularies with
`dcterms:description` only, so the vocabulary page shows `dcterms:description` as a field of its
own, next to `skos:definition`.

## D25 — A change to the vocabulary files rereads every document

Rereading only the documents that use a directive would need a per-document record kept, merged
and purged, to save rereading the site's few prose pages (research R2).

## D26 — "Adds no static file" is held by review, not by a test

A test listing the package's files records today's layout and fails for any new module. FR-024's
build-under-any-theme half is tested (T006).

## D27 — Links to script URIs are shown as text

A vocabulary file can come from another organisation. A link whose scheme is `javascript`, `data`
or `vbscript` is shown as text, never as a link, because the HTML writer puts `refuri` into `href`
unchanged. This narrows FR-014 only for schemes a browser runs.

## D28 — Design review

Applied to the plan and tasks: reStructuredText suffix taken from `source_suffix` (SPEC-001),
section ids from `note_implicit_target` (SPEC-002), clean-up of `_sources/` and only on HTML
builders (SPEC-003), order tests against an order the test computes (SPEC-004), addresses compared
with `/index` removed and between generated pages (ARCH-001), script URIs not linked (SEC-001, D27),
`\` refused in an address (SEC-002). Carried as a watch item for the code review: nothing adds a
stylesheet, script or static file (SPEC-005, D26).
