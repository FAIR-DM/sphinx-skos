# sphinx-skos

[![Tests](https://github.com/FAIR-DM/sphinx-skos/actions/workflows/tests.yml/badge.svg)](https://github.com/FAIR-DM/sphinx-skos/actions/workflows/tests.yml)
[![Build](https://github.com/FAIR-DM/sphinx-skos/actions/workflows/build.yml/badge.svg)](https://github.com/FAIR-DM/sphinx-skos/actions/workflows/build.yml)
[![Publish](https://github.com/FAIR-DM/sphinx-skos/actions/workflows/publish.yml/badge.svg)](https://github.com/FAIR-DM/sphinx-skos/actions/workflows/publish.yml)
[![Coverage](https://codecov.io/gh/FAIR-DM/sphinx-skos/branch/main/graph/badge.svg)](https://codecov.io/gh/FAIR-DM/sphinx-skos)
[![PyPI](https://img.shields.io/pypi/v/sphinx-skos)](https://pypi.org/project/sphinx-skos/)
[![Development status](https://img.shields.io/pypi/status/sphinx-skos)](https://pypi.org/project/sphinx-skos/)
[![Python](https://img.shields.io/pypi/pyversions/sphinx-skos)](https://pypi.org/project/sphinx-skos/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Licence](https://img.shields.io/github/license/FAIR-DM/sphinx-skos)](https://github.com/FAIR-DM/sphinx-skos/blob/main/LICENSE)

A [Sphinx](https://www.sphinx-doc.org/) extension that builds SKOS vocabularies into a
documentation site. Point it at your vocabulary files and Sphinx publishes one page for every
vocabulary, every concept and every collection, with the RDF for each page beside it.

## Why

A controlled vocabulary is published so that people can read it and machines can resolve it.
Each concept has a URI, and that URI should lead somewhere useful: a page a person can read, and
the same concept in RDF for software that asks for it.

Most tools that render a SKOS vocabulary produce one long page for the whole vocabulary, or are a
site generator of their own with their own templates and theming. `sphinx-skos` does neither. It
turns each concept into an ordinary Sphinx document, so a vocabulary site is a Sphinx site: it can
hold prose pages next to the generated ones, link between them, and look however its Sphinx theme
makes it look.

## Status

Early. The version is `0.0.1`. The package installs and registers with Sphinx, but it does not
yet read vocabularies or generate pages. The configuration below shows where it is going, not
what it does today.

## Planned usage

```python
# conf.py
extensions = ["sphinx_skos"]
skos_vocabularies = ["../vocabularies/*.ttl"]
skos_base_uri = "https://w3id.org/example/vocabularies/"
```

Built with the `dirhtml` builder, a concept's page lives at its URI with `skos_base_uri` removed,
so a redirect from the URI's domain to the site maps one address directly onto the other. Each
page has Turtle, JSON-LD, RDF/XML and N-Triples copies beside it.

## Scope & philosophy

**What it is.** A Sphinx extension that reads SKOS vocabulary files and turns them into Sphinx
documents: one page per vocabulary, concept and collection, each with its RDF copies. It works for
any vocabulary from any organisation.

**What it is not.**

- **Not a theme.** Logos, colours, fonts and layout come from Sphinx's own theme settings in your
  `conf.py`: `html_theme`, `html_logo`, `html_theme_options` and the rest. The extension renders
  content only. Requests to add a logo, a colour scheme or a layout option to this package will
  be closed with a pointer to [Sphinx's HTML theming
  documentation](https://www.sphinx-doc.org/en/master/usage/theming.html).
- **Not a vocabulary editor.** The Turtle files are the source. The extension reads them and
  never writes them back.
- **Not a SKOS validator.** It renders what the files say. Checking a vocabulary's quality is the
  job of tools built for it.
- **Not a server.** It writes static files. Resolving a URI to a page is done by a redirect
  service such as [w3id.org](https://w3id.org/) or by your web server.

**When choices collide:**

1. The vocabulary files are the truth. A page shows what they say, and the RDF copies contain
   what they contain, without anything added or dropped.
2. A concept's address never changes because the extension changed.
3. Anything a site can set in Sphinx itself stays in Sphinx.

### Prior art

[pyLODE](https://github.com/RDFLib/pyLODE) renders a SKOS vocabulary or an OWL ontology as HTML
and is well maintained. It produces a single page per vocabulary, which does not give each concept
a page of its own to resolve to. `sphinx-skos` exists for the one-page-per-concept case.

## Contributing

See [CONTRIBUTING.md](https://github.com/FAIR-DM/sphinx-skos/blob/main/CONTRIBUTING.md). The rules
every change follows are in
[CONSTITUTION.md](https://github.com/FAIR-DM/sphinx-skos/blob/main/CONSTITUTION.md).

## License

MIT. See [LICENSE](https://github.com/FAIR-DM/sphinx-skos/blob/main/LICENSE).
