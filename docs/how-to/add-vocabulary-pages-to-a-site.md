# Add vocabulary pages to a site

Put the pages sphinx-skos generates into a Sphinx site's table of contents, and keep them out of
version control. Do this once the site builds the pages, as in [Publish vocabulary files as a
site](publish-vocabulary-files.md), or when you move a site from version 0.3.

## Before you start

You need a Sphinx site that lists `sphinx_skos` in its `extensions` and sets
[`skos_vocabularies`](../reference/settings.md#skos_vocabularies) and
[`skos_base_uri`](../reference/settings.md#skos_base_uri).

## Steps

1. Keep the vocabulary files outside the directory that holds the generated pages. The pages go
   in [`skos_directory`](../reference/settings.md#skos_directory), `vocabularies` unless you set
   another. The next steps ignore that directory in version control, and a vocabulary file in it would be
   ignored too.

   ```python
   skos_vocabularies = ["data/*.ttl"]
   ```

2. List the index page in a `toctree` of one of the site's own pages, such as `index.rst`. The
   index links every vocabulary. Without this entry Sphinx warns that the index is in no table of contents.

   ````rst
   .. toctree::

      vocabularies/index
   ````

3. Add the directory to `.gitignore`. Every build writes the pages again, so they need not be
   kept.

   ```text
   vocabularies/
   ```

4. Build the site.

   ```console
   sphinx-build -b dirhtml docs docs/_build/dirhtml
   ```

## Move a site from version 0.3

Version 0.3 wrote the pages at the root of the source directory, at their page addresses. From
the next version they are in `skos_directory`.

1. If the vocabulary files are in `vocabularies/`, move them to another directory, such as
   `data/`, and change the patterns in `skos_vocabularies`. The directory is about to hold only
   generated files.
2. Replace the old `.gitignore` entries, one for each vocabulary, with `vocabularies/`.
3. If `conf.py` sets no `html_theme`, the site is now built with Furo instead of Sphinx's default,
   alabaster. To keep the old look, set `html_theme = "alabaster"`. Remove any
   `html_theme_options` that only alabaster accepts, or a build that treats warnings as errors
   fails.
4. Follow the steps above.
5. Build the site. The build deletes the pages version 0.3 wrote at the old addresses, with their
   output, and leaves every file that has no generated-page comment on its first line.
6. Redirect each old address to the new one, for example `/date-types/available/` to
   `/vocabularies/date-types/available/`, with the host's redirect rules or a Sphinx extension
   for redirects. Every page address now starts with the directory, so links from other sites
   to the old addresses break without a redirect.

## The result

Every generated page is under `skos_directory`, the index lists the vocabularies, and the
theme's navigation shows each vocabulary's concepts and collections beneath it. A build that treats
warnings as errors (`-W`) passes. Pages from an earlier version are gone.
