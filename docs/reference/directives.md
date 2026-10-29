# Directives

The three directives that show a resource in a page of your own. The generated pages are written
with the same directives, so a page you write by hand shows the same fields and links.

## Directives

| Directive | Shows |
|---|---|
| `skos:vocabulary` | A vocabulary |
| `skos:concept` | A concept |
| `skos:collection` | A collection |

Each takes the resource's URI as its one argument and has no options. Content written under the
directive goes inside the resource's section, after its fields, so a `toctree` there nests under
the resource's title in a theme's navigation. A vocabulary's generated page uses this for its
hidden list of concepts and collections.

```rst
.. skos:concept:: https://w3id.org/example/vocabularies/date-types/available
```

## What is shown

The directive becomes a section titled with the resource, holding a field list. It shows every
statement the vocabulary files make about the resource except its hidden labels, which are meant
for search and stay in the [RDF copies](rdf-copies.md) only. A field appears only when the
resource has a value for it, except the URI, which always appears.

The fields come in this order:

1. The URI.
2. The labels and what the resource is: preferred labels, alternative labels, definitions,
   titles (`dcterms:title`), descriptions (`dcterms:description`), notations, and the scope
   notes, notes, examples, history notes, editorial notes and change notes.
3. The fields of the resource's kind, in the table below.
4. Who made it, when and on what terms: creators, contributors and publishers, the created,
   issued and modified dates, the version (`owl:versionInfo`), the licence (`dcterms:license`),
   rights, identifiers, languages, sources, citations (`dcterms:bibliographicCitation`) and
   `rdfs:seeAlso` links.
5. Every other property, one field each, sorted by name. Each is named by its prefixed name, such
   as `dcterms:isPartOf`, linked to the property's URI. A property no prefix in the files covers
   is named by its URI.

| Directive | Fields of its kind, in order |
|---|---|
| `skos:concept` | vocabulary, collections, broader, narrower, related, one field for each mapping link the concept has |
| `skos:vocabulary` | concepts, collections, namespace prefixes |
| `skos:collection` | members |

A generated page ends with one more field, [Download](#download).

How a value is shown depends on what it is:

- **A URI** is a link. A link to a resource that has a page goes to that page and shows the
  resource's title. Any other link goes to the URI itself, and shows the name the files give it,
  for example a creator's `foaf:name`, or the URI when they give none. A URI that runs code or
  carries data when followed, one that starts with `javascript:`, `data:` or `vbscript:`, is
  shown as text and never linked.
- **A literal** is shown as its text, followed by its language tag, or by its datatype when it has
  no language, such as `(xsd:date)`.
- **A blank node** is shown as a field list of its own statements, nested in the field, as deep
  as the files go.

Within a field, URIs come first, sorted by the text they show, then literals, sorted by language
and then text, then blank nodes. An ordered collection's members keep the collection's order.
Every page shows its fields and values in the same order on every build.

## Namespace prefixes

A vocabulary, on its generated page and written by hand alike, lists the namespace prefixes
declared by the vocabulary files that state it. The field holds a bulleted list: each item is the
prefix and a colon, followed by the namespace as a link. The empty prefix is shown as `:`. Pairs
are listed once, sorted by prefix and then namespace, so a prefix that two files bind to different
namespaces appears twice. A prefix that no file declares is not listed, including those that
rdflib knows by default. The field is absent when the files declare none.

## Download

Every generated page ends with a field that links the page's RDF files, one link each for Turtle,
JSON-LD, RDF/XML and N-Triples. A concept's and a collection's page link their own
[RDF copies](rdf-copies.md). A vocabulary's page links its whole files under the `dirhtml` builder,
and its own copies under the `html` builder. Any other builder, such as `singlehtml` or `text`,
writes no copies, so it leaves the field out. A page written by hand has no download field.

## What is not written

A directive written by hand writes no [RDF copies](rdf-copies.md), adds no alternate links
to the page and has no download field. Only the resource's generated page has them. The page you write keeps all its own
content, and the resource keeps its generated page.

## Warnings

A directive that cannot show its resource produces no output and prints a build warning naming
the page it is on.

| Cause | The warning names |
|---|---|
| The URI names no resource in the vocabulary files | The URI and the page |
| The URI names a resource of another kind, such as a vocabulary given to `skos:concept` | The URI and the page |
| No URI is given | The page |

## Several in one page

A directive may sit under a titled section of a page, and the same directive may be used more
than once in a page. Each section it produces gets its own identifier.
