# RDF copies

The files sphinx-skos writes beside each generated page, holding that resource's own RDF.

## What a copy holds

A copy holds every triple with the resource as subject, and the triples of any blank nodes those
reach, such as the cells of a `skos:memberList`. It does not hold what other resources say about
it. A concept's copy has no `skos:narrower` stated by its broader concept and no `skos:member`
naming it from a collection, unless the vocabulary files state those about the concept itself.
Namespace prefixes are the ones the vocabulary files declare.

## Names and media types

A copy is named after the page's HTML file with the suffix replaced.

| Format | Suffix | Media type | `dirhtml` builder | `html` builder |
|---|---|---|---|---|
| Turtle | `.ttl` | `text/turtle` | `index.ttl` | `<name>.ttl` |
| JSON-LD | `.jsonld` | `application/ld+json` | `index.jsonld` | `<name>.jsonld` |
| RDF/XML | `.rdf` | `application/rdf+xml` | `index.rdf` | `<name>.rdf` |
| N-Triples | `.nt` | `application/n-triples` | `index.nt` | `<name>.nt` |

Under `dirhtml` the copies sit in the page's directory, so the concept at
`https://example.org/vocab/date-types/available` has `date-types/available/index.ttl` and the rest.
Under `html` they sit beside `date-types/available.html`, as `date-types/available.ttl`.

These names are permanent. They depend only on the page address and the format, so two builds of
unchanged files give the same files at the same addresses, and a release that renames one is a
breaking change.

## Whole-vocabulary files

Under the `dirhtml` builder a vocabulary also has four whole files, which hold the graph of the
vocabulary files it comes from instead of the vocabulary's own triples alone. They are named after
the vocabulary's page address, with the suffix of each format, and sit beside the page's
directory: the vocabulary at `https://example.org/vocab/date-types` has
`vocabularies/date-types.ttl`, `.jsonld`, `.rdf` and `.nt`, next to its page at
`vocabularies/date-types/`.

A whole file holds every statement of every vocabulary file that states something about the
vocabulary, a concept in it or a collection in it, nothing added and nothing dropped. A vocabulary
that has a file to itself gets the file as it is. When a file holds several vocabularies, each of
them offers the whole file, and when a vocabulary is stated across several files, its whole file
is their union. Its namespace prefixes are those the files declare.

Only the `dirhtml` builder writes them, because no other file is ever written at that address
there. Under the `html` builder the vocabulary's own Turtle copy is, so a vocabulary's page offers
its own copies instead. A vocabulary's own copies and the alternate links in its page head are the
same as a concept's: they hold the vocabulary's own RDF. A vocabulary removed from the files loses
its whole files on the next build.

## Links in the page

Every generated page's `<head>` has one `<link rel="alternate">` for each copy. Its `type` is the
copy's media type and its `href` is the copy's file name, which resolves from the page's own
address. Pages the site wrote by hand have none. The page also lists its files in a download field, which
the [directives reference](directives.md#download) describes. The extension adds no template, so the links
appear under any Sphinx theme that renders Sphinx's `metatags`, which Sphinx's own themes and
Furo do.

Copies are written only by builders that write HTML. A resource that is removed from the
vocabulary files loses its page and its copies on the next build.
