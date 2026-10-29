# FS-002 planning notes

Suggestions from the maintainer for how this feature is built. Each one is answered when the
feature is planned: adopted or not, and why.

Generated pages should work the way sphinx-autodoc2 writes its API pages: into one directory of
their own, with an index the site includes in its own table of contents once, and each vocabulary
page listing its concepts and collections in a hidden table of contents so they appear in the
sidebar.

The ready-made layout is the one already previewed with sphinx-book-theme 1.4.0:
`html_theme_options = {"navbar_persistent": [], "secondary_sidebar_items": []}`, plus one
stylesheet rule giving the article the full width once the right-hand sidebar is gone:
`@media (min-width: 1200px) { .bd-main .bd-content .bd-article-container { max-width: 100%; } }`.

In the preview, the download menu was filled from an `html-page-context` handler that replaces the
buttons of sphinx-book-theme's `download-buttons` entry in `header_buttons` with one link per
format, using the page's `<link rel="alternate">` copies for a concept or collection and the
whole-vocabulary files for a vocabulary. That replaced a `conf.py` hook and a build-finished
export step in the site; both belong in the package now.

The one-command build should be as easy as fairdm-docs
([FAIR-DM/fairdm-docs](https://github.com/FAIR-DM/fairdm-docs)): settings in a `[tool.*]` table of
`pyproject.toml`, no `conf.py` needed, and a `docs/` directory with its own `conf.py` that is
optional and overrides everything.

Namespace prefixes on a vocabulary's page should read like pyLODE's.
