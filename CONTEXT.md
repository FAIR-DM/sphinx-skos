# sphinx-skos — Context

The words this repository uses, what each one means here, and the words it avoids. Issues, pull
requests, code and tests use these terms.

SKOS terms are from the [SKOS Reference](https://www.w3.org/TR/skos-reference/).

## Glossary

**Site**
The Sphinx project that publishes vocabularies. It either lists `sphinx_skos` in the `extensions`
of its own `conf.py`, or is built by `sphinx-skos build` from a `[tool.sphinx-skos]` table with no
`conf.py` at all. It may have its own theme and its own prose pages. _Avoid_: project, portal
(both mean other things in neighbouring packages).

**Vocabulary**
One SKOS concept scheme (`skos:ConceptScheme`) and the concepts in it. A site may publish several.
_Avoid_: scheme on its own, thesaurus, taxonomy, ontology.

**Vocabulary file**
A Turtle file a site lists in `skos_vocabularies` or in the `vocabularies` key of its settings
table. The source of truth for everything the
extension publishes. One file may hold one vocabulary or several. _Avoid_: input, data file.

**Concept**
A `skos:Concept`. _Avoid_: term, entry, keyword.

**Collection**
A `skos:Collection` or `skos:OrderedCollection`: a named group of concepts, which may be ordered.
A collection is not a vocabulary and does not own its members. _Avoid_: group, list, subset.

**Resource**
A vocabulary, a concept or a collection: anything that gets a page.

**Base URI**
The `skos_base_uri` setting. The part of every resource URI that the site's address replaces.

**Page address**
Where a resource's page lives on the built site: its URI with the base URI removed, as a
directory under the `dirhtml` builder. _Avoid_: slug, permalink.

**Page**
The Sphinx document generated for one resource, and the HTML built from it. _Avoid_: view.

**RDF copy**
A file beside a page holding that resource's own RDF, in one of four formats: Turtle (`.ttl`),
JSON-LD (`.jsonld`), RDF/XML (`.rdf`) and N-Triples (`.nt`). _Avoid_: export, download,
serialisation on its own.

**Own RDF**
What a resource's RDF copies contain: every triple with the resource as subject, plus the
triples of any blank nodes those reach.

**Directive**
One of `skos:vocabulary`, `skos:concept` and `skos:collection`. A generated page holds exactly
one. A prose page may use them by hand.

**Label**
A `skos:prefLabel`, `skos:altLabel` or `skos:hiddenLabel`, each in its own language. _Avoid_:
name, title.

**Definition**
`skos:definition`. _Avoid_: description.

**Notation**
`skos:notation`: a code that identifies a concept within its vocabulary. _Avoid_: code, key.

**Mapping link**
A link from a concept to a concept in another vocabulary: `skos:exactMatch`, `skos:closeMatch`,
`skos:broadMatch`, `skos:narrowMatch` or `skos:relatedMatch`. _Avoid_: crosswalk, alignment.

**Generated-pages directory**
The directory in a site's source that holds every generated page and the index: `vocabularies/`
unless `skos_directory` says otherwise. _Avoid_: output directory (that is where the built site
goes).

**Index**
The page at the root of the generated-pages directory that lists every vocabulary. The one
document a site adds to its own table of contents. _Avoid_: contents page, landing page.

**Front page**
The site's root page: the site's own when it has one, otherwise the one `sphinx-skos build`
writes. _Avoid_: home page, landing page.

**Whole-vocabulary file**
A file holding a whole vocabulary in one of the four RDF formats, offered from the vocabulary's
page. Not an RDF copy, which holds one resource. _Avoid_: dump, bulk export.

**Download**
A link on a page to that page's RDF in one format. _Avoid_: export.

**Default theme**
Furo, installed with the package and used when the site sets no theme.

**Namespace prefix**
A prefix and namespace URI pair declared in a vocabulary file. _Avoid_: abbreviation, CURIE
prefix.

**Look and feel**
Logos, colours, fonts and layout. Set by the site's Sphinx theme, never by this extension, which
only chooses the default theme.
