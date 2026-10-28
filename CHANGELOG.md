# Changelog

All notable changes to this project are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[semantic versioning](https://semver.org/).

## [Unreleased]

## [v0.3.1] - 2026-10-28

### Fixed

- A rebuild after the extension is upgraded rereads every page, so it gives what a clean build
  gives. Before, an incremental build kept the pages the previous version had rendered.

## [v0.3.0] - 2026-10-28

### Changed

- A page shows every statement its resource carries, except hidden labels. Titles,
  descriptions, notations, the SKOS notes, creators, contributors, publishers, dates, the
  version, licence, rights, identifiers, languages, sources, citations and `rdfs:seeAlso` each
  get a field of their own, on every kind of page. Every other property gets a field named by
  its prefixed name, linked to the property. A literal shows its language or datatype, and a
  blank node shows its own statements nested.
- A link to a URI with no page on the site shows the name the vocabulary files give it, such as
  a creator's `foaf:name`, instead of the URI.
- The vocabulary files' namespace prefixes are bound in `Vocabularies.graph`.

### Removed

- `Vocabularies.descriptions()` and `Vocabularies.notations()`. Use `Vocabularies.statements()`.

## [v0.2.0] - 2026-10-28

### Added

- The `skos_vocabularies` and `skos_base_uri` settings. The vocabulary files they name are read
  into one graph when a build starts.
- A generated page for every vocabulary, concept and collection, at its URI with the base URI
  removed. A page is titled with its resource. A resource that cannot get a page is named in a
  build warning.
- Four RDF copies beside every generated page, in Turtle, JSON-LD, RDF/XML and N-Triples, holding
  that resource's own RDF. Each page's head names them with `<link rel="alternate">` elements. The
  copy names are permanent. A removed resource's copies are removed with its page.
- The `skos` domain, with the `skos:vocabulary`, `skos:concept` and `skos:collection`
  directives. Written by hand in a page of your own, each shows the same fields and links as the
  resource's generated page, and warns, naming the page, when its URI is missing, names no
  resource or names a resource of another kind.

## [v0.1.0] - 2026-10-28

### Added

- The `sphinx_skos` extension, which a site can list in its `extensions`. It does not yet read
  vocabularies.
