# Changelog

All notable changes to this project are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[semantic versioning](https://semver.org/).

## [Unreleased]

### Added

- The `sphinx-skos build` command builds a site from a `[tool.sphinx-skos]` table in
  `pyproject.toml`, with the `dirhtml` builder and no `conf.py`, into `_build/site/`. `-o` chooses
  the output directory and `-W` makes a warning fail the build. A `docs/` directory adds pages of
  the site's own, and a `docs/conf.py` is used as it is.
- The `skos_directory` setting, `vocabularies` by default, names the directory that holds the
  generated pages.
- An index page, `vocabularies/index`, links every vocabulary. List it in a `toctree`.
- Every generated page ends with a download field linking its RDF files. A vocabulary's page links
  four whole files, holding the graph of the vocabulary files it comes from, written beside the
  page's directory when the site is built with `dirhtml`, for example
  `vocabularies/date-types.ttl`.
- A vocabulary's page lists the namespace prefixes its files declare, each linked to its
  namespace.

### Changed

- **Breaking:** generated pages are no longer at the root of the source directory. Every page
  address now starts with `skos_directory`, so `date-types/available/` becomes
  `vocabularies/date-types/available/`. Add a redirect from each old address. Keep vocabulary
  files outside the directory, because it now holds only generated files.
- Generated pages are no longer marked `:orphan:`. A site that lists no page that leads to the
  index gets Sphinx's warning that the index is in no table of contents.
- Pages that an earlier version wrote at the old addresses are deleted at the first build.
- Furo is installed with the package, and a site that sets no `html_theme` is built with it
  instead of alabaster. Set `html_theme = "alabaster"` to keep the old look, and remove theme
  options Furo does not accept.

## [v0.3.3] - 2026-10-29

### Fixed

- A page's Turtle copy uses the prefix names its own vocabulary file declares, including the empty
  prefix, instead of generated names such as `default3`. The statements are unchanged.

## [v0.3.2] - 2026-10-28

### Added

- A reusable GitHub Actions workflow, `.github/workflows/build-site.yml`, that builds a site with
  the `dirhtml` builder, with warnings treated as errors, and deploys it to GitHub Pages. It
  installs a list of packages or the repository's own uv dependency group, and can build without
  deploying. The built site is uploaded as the `github-pages` artifact.

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
