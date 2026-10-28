# Directives

The three directives that show a resource in a page of your own. The generated pages are written
with the same directives, so a page you write by hand shows the same fields and links.

## Directives

| Directive | Shows |
|---|---|
| `skos:vocabulary` | A vocabulary |
| `skos:concept` | A concept |
| `skos:collection` | A collection |

Each takes the resource's URI as its one argument and has no content and no options.

```rst
.. skos:concept:: https://w3id.org/example/vocabularies/date-types/available
```

## What is shown

The directive becomes a section titled with the resource, holding a field list. A field appears
only when the resource has a value for it, except the URI, which always appears. Hidden labels
never appear.

| Directive | Fields, in order |
|---|---|
| `skos:concept` | URI, preferred labels, alternative labels, definitions, notations, vocabulary, collections, broader, narrower, related, one field for each mapping link the concept has |
| `skos:vocabulary` | URI, preferred labels, alternative labels, definitions, descriptions, concepts, collections |
| `skos:collection` | URI, preferred labels, alternative labels, definitions, members |

A link to a resource that has a page goes to that page. Any other link goes to the URI itself.
A URI that runs code or carries data when followed, one that starts with `javascript:`,
`data:` or `vbscript:`, is shown as text and never linked.

## What is not written

A directive written by hand writes no [RDF copies](rdf-copies.md) and adds no alternate links
to the page. Only the resource's generated page has them. The page you write keeps all its own
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
