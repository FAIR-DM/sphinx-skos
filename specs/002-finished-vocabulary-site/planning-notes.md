# FS-002 planning notes

Suggestions from the maintainer for how this feature is built. Each one is answered when the
feature is planned: adopted or not, and why.

Generated pages should work the way sphinx-autodoc2 writes its API pages: into one directory of
their own, with an index the site includes in its own table of contents once, and each vocabulary
page listing its concepts and collections in a hidden table of contents so they appear in the
sidebar.

Default to Furo, which is included: Furo is installed with the package and used when a site sets
no theme. No layout of our own on top of it.

The one-command build should be as easy as fairdm-docs
([FAIR-DM/fairdm-docs](https://github.com/FAIR-DM/fairdm-docs)): settings in a `[tool.*]` table of
`pyproject.toml`, no `conf.py` needed, and a `docs/` directory with its own `conf.py` that is
optional and overrides everything.

Namespace prefixes on a vocabulary's page should read like pyLODE's.
