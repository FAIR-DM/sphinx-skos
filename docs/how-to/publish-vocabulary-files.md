# Publish vocabulary files as a site

Turn a set of Turtle vocabulary files into a site that has a front page and one page for every
vocabulary, concept and collection in them. Do this when the vocabulary files are finished
enough to publish, or to see how they will look. You need no Sphinx knowledge and no `conf.py`.

## Before you start

You need sphinx-skos installed, and vocabulary files in Turtle (`.ttl`). Keep the files outside
the `catalogue/` directory: the build treats that directory as its own and the extension
deletes generated files in it.

## Steps

1. Add a `[tool.sphinx-skos]` table to `pyproject.toml`, at the top of the project. The
   `vocabularies` patterns are read from the directory that holds `pyproject.toml`.
   [`base-uri`](../reference/settings.md#skos_base_uri) is the start of every resource URI that the
   site's address replaces.

   ```toml
   [tool.sphinx-skos]
   title = "Example vocabularies"
   base-uri = "https://w3id.org/example/vocabularies/"
   vocabularies = ["data/*.ttl"]
   ```

   To show a logo in the sidebar, add `logo` with the path of an image file, read from the same
   directory, such as `logo = "docs/_static/logo.svg"`. To link the site's repository from the
   footer, name it in `[project.urls]`, such as `Repository =
   "https://github.com/example/vocabularies"`.

2. Build the site from the same directory.

   ```console
   sphinx-skos build -W
   ```

   The site is written to `_build/site/`. Pass `-o` to write it elsewhere. `-W` makes a warning
   fail the build, which is what you want in a publishing job; leave it out to see the warnings
   and still get a site.

3. Check the build output. Open `_build/site/index.html`: it links the catalogue, which lists every vocabulary. A concept
   with the URI `https://w3id.org/example/vocabularies/date-types/available` has its page at
   `catalogue/date-types/available/index.html`. Every vocabulary, concept and collection in
   the files has a page, and nothing else does.

4. Add `_build/` and `catalogue/` to `.gitignore`, because both are produced by the build.

## Add pages of your own

Create a `docs/` directory and put prose pages in it. They join the site, and the front page
links to them. If `docs/` has no front page, the build writes `docs/index.rst`, and you add that
file to `.gitignore` as well, or write a front page of your own. To change any setting, or the theme, add a `docs/conf.py` that lists `sphinx_skos` in
`extensions`; its values win over the table. See [Command](../reference/command.md) and
[Settings](../reference/settings.md).

## The result

The built site has a front page and a page for every resource at its page address, in the Furo
theme unless you chose another. The build prints a warning for each resource that cannot get a
page, naming it, so a build run with `-W` fails instead of leaving a page out. Fix a warning by
correcting the URI in the vocabulary file, the base URI, or the name of your own page that is in
the way.
