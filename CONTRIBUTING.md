# Contributing to sphinx-skos

Thank you for helping. This guide covers what the package will and will not take, how to set up,
and what a pull request needs.

## Before you open an issue

`sphinx-skos` renders the content of SKOS vocabularies. It does not control how a site looks.
Logos, colours, fonts and layout come from the Sphinx theme a site chooses, set in its `conf.py`
with `html_theme`, `html_logo` and `html_theme_options`. See Sphinx's
[HTML theming documentation](https://www.sphinx-doc.org/en/master/usage/theming.html).
The one exception is the optional ready-made layout of the `book` extra, a set of defaults for
sphinx-book-theme that every site setting overrides.

Issues and pull requests asking this package for a logo, a colour scheme, a stylesheet, a
template or a layout option are closed with a pointer here. That is a standing decision, recorded
in the README's *Scope & philosophy* section and in `CONSTITUTION.md` (Article X).

Equally out of scope: editing or validating vocabularies, and serving pages. The README explains
why.

## Setting up

```bash
git clone https://github.com/FAIR-DM/sphinx-skos.git
cd sphinx-skos
uv sync
uv run pre-commit install
```

## Making a change

1. Branch from `main`.
2. Write a test first, and watch it fail for the right reason. Tests build a small site with
   `sphinx.testing`. Test sites live under `tests/roots/`. See
   [docs/contributing/standards/testing.md](docs/contributing/standards/testing.md).
3. Make the change.
4. Run the checks:

   ```bash
   uv run pytest
   uv run pre-commit run --all-files
   ```

5. Add a line to `CHANGELOG.md` under `[Unreleased]` if the change is visible to a site author.
6. Open a pull request that says what changed and why.

## Standards

- [CONSTITUTION.md](CONSTITUTION.md): the rules every change follows.
- [CONTEXT.md](CONTEXT.md): the words this repository uses.
- [docs/contributing/standards/](docs/contributing/standards/): testing, documentation and
  docstrings.

## Licence

By contributing you agree that your contribution is licensed under the MIT License.
