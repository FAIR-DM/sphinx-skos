# Changelog

All notable changes to this project are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[semantic versioning](https://semver.org/).

## [Unreleased]

### Added

- The `skos_vocabularies` and `skos_base_uri` settings. The vocabulary files they name are read
  into one graph when a build starts.
- A generated page for every vocabulary, concept and collection, at its URI with the base URI
  removed. A page is titled with its resource. A resource that cannot get a page is named in a
  build warning.
- The `skos` domain, with the `skos:vocabulary`, `skos:concept` and `skos:collection`
  directives.

## [v0.1.0] - 2026-10-28

### Added

- The `sphinx_skos` extension, which a site can list in its `extensions`. It does not yet read
  vocabularies.
