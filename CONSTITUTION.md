# sphinx-skos Constitution

The rules every change to this repository follows. The words in it are defined in
[`CONTEXT.md`](CONTEXT.md).

## Core articles

### Article I — Testing
Every change follows [`docs/contributing/standards/testing.md`](docs/contributing/standards/testing.md): what gets a test
and what does not, the test-first cycle, test structure and fixtures, and the coverage floors.

### Article II — Simplicity
Start with the simplest design that satisfies the specification. New dependencies, new
abstractions and new infrastructure each need a stated reason in the plan or the pull request.
No speculative generality.

### Article III — Anti-Abstraction
No wrapper layers, base classes or "future-proofing" indirection without a present, concrete
second use. Prefer duplication over the wrong abstraction.

### Article IV — Integration-First
The extension's contract is what a site author writes in `conf.py` and in a page, and what the
build writes out. Tests build a real site through `sphinx.testing` and check the pages and RDF
copies it produces, the way a site author or a client resolving a URI meets them.

### Article V — Security & data-safety
Text taken from a vocabulary file reaches a page only through docutils nodes, which the HTML
writer escapes. No change builds HTML by joining strings with vocabulary content. Secrets live in
runtime configuration, never in code, test sites or version control. A vocabulary file is read,
never written.

### Article VI — Documentation
Public API changes ship their docs in the same pull request: README and CHANGELOG updated.
Docstrings and code comments follow
[`docs/contributing/standards/code-documentation.md`](docs/contributing/standards/code-documentation.md). The pages
under `docs/` and the README's quickstart follow
[`docs/contributing/standards/documentation.md`](docs/contributing/standards/documentation.md). The README follows
the package README standard, including its badge row and a *Scope & philosophy* section.

### Article VII — Dependency discipline
A new runtime dependency needs a stated reason. `deptry` must pass: no unused, missing or
transitively relied-upon dependencies.

### Article VIII — Internationalization
Fixed text the extension writes into a page, such as a section heading, is marked for translation
with Sphinx's own message catalogue (`sphinx.locale.get_translation`), so a site's `language`
setting applies to it. Text from a vocabulary is never translated: it is shown in the languages
the vocabulary provides.

### Article IX — Cohesion (Python)
Related behaviour is grouped in a class, not scattered across module-level functions.

**The test:** two or more module-level functions that share a *subject* belong on a class. They
share a subject when they operate on the same data, take the same first argument, are only
meaningful in sequence, or are named around the same noun (`build_x`, `validate_x`, `render_x`).

**Why.** In a published package a class is the extension point. A site that needs different
behaviour subclasses it and overrides one method. A module of functions can only be
monkey-patched, which is not a supported interface.

**Sphinx first.** Where Sphinx already owns the grouping, use it rather than inventing a class: a
`SphinxDirective` subclass for a directive, a `Domain` for a set of directives and roles, an
event handler connected in `setup()` for work done at a stage of the build.

**Exceptions**, stated rather than assumed: a standalone pure function with no siblings, the
module-level `setup()` Sphinx requires, `conftest.py` fixtures, and a module of independent
utilities that genuinely share no subject.

**This does not license abstraction.** Article III still holds.

## Project articles

### Article X — Content, never look and feel
The extension emits document content (docutils nodes) and RDF copies. It adds no stylesheet,
script, HTML template, image, static file or theme option. It sets one default, `html_theme =
"furo"`, for a site that sets no theme itself, and installs Furo for it. Two things pass through
it without being its own:

- A site's title and logo, written in the `[tool.sphinx-skos]` table, go to Sphinx's
  `html_title` and `html_logo`, so a site with no `conf.py` can name them. The words and the
  image are the site's.
- The navigation opens only the branch of the page being read below its top level, because the
  generated pages would otherwise list every concept of every vocabulary on every page. The
  entries are Sphinx's own, and no markup is added to them.

Colours, fonts, layout and every other look-and-feel choice are set by the site through Sphinx's
theme settings, and a change that adds any of them to this package is out of scope however it is
asked for.

### Article XI — Nothing site-specific in the package
No organisation's URI, name, vocabulary or default appears in the package code. Everything a site
needs to differ in comes from its `pyproject.toml` or its `conf.py`. Test sites use example URIs, never a real
organisation's.

### Article XII — The vocabulary files are the truth
A resource's RDF copies contain its own RDF exactly as the vocabulary files state it: no triple
added, dropped or rewritten. A page shows what the files say and nothing the files do not.

### Article XIII — Page addresses are stable
A resource's page address is its URI with the base URI removed, under the generated-pages
directory. It depends on the URI, the base URI and that directory's name, and on nothing else. A
change that moves any existing resource to a different address is a breaking change.

### Article XIV — Compatibility and stack
- Python 3.12 or later, Sphinx 9.0 or later. Every supported Python and Sphinx pair is tested in
  CI. Dropping a Python or Sphinx version is a minor release, recorded in `CHANGELOG.md`.
- uv-managed, built with hatchling. Tests use pytest with `sphinx.testing`.
- Semantic versioning. Settings, directive names and import paths do not change without a major
  version, and a deprecated setting warns for at least one minor version before it is removed.
  Below 1.0.0 that deprecation window is advisory, because there is no stable surface yet.

## Articles not adopted

- Data-model conventions (Django) — this package has no Django models and does not use Django.

## Quality bar

Read at plan and review. Applies to every change.

- Test coverage meets the floors in `docs/contributing/standards/testing.md` (`codecov.yml` is
  the reference).
- Every public API change updates README and CHANGELOG in the same pull request.
- Lint, type-check (`mypy`) and `deptry` pass.
- The package builds, its metadata is valid, the README renders on PyPI with absolute links, and
  the public API honours the deprecation policy in Article XIV.

## Non-negotiables

- Tests, build and lint pass before a change merges. Nobody overrides a red check.
- The default branch requires one approval, and the author of a change never approves it.

---

**Version**: 1.2.0 | **Ratified**: 2026-10-28 | **Last Amended**: 2026-10-29
