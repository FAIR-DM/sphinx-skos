# Publish vocabulary files as a site

Turn a set of Turtle vocabulary files into a Sphinx site that has one page for every
vocabulary, concept and collection in them. Do this when the vocabulary files are finished
enough to publish, or to see how they will look.

## Before you start

You need a Sphinx site with sphinx-skos installed in the same environment as Sphinx, and
vocabulary files in Turtle (`.ttl`).

## Steps

1. Add the extension and the two settings to the site's `conf.py`. The patterns in
   [`skos_vocabularies`](../reference/settings.md#skos_vocabularies) are read from the
   directory that holds `conf.py`. [`skos_base_uri`](../reference/settings.md#skos_base_uri) is
   the start of every resource URI that the site's address replaces.

   ```python
   extensions = ["sphinx_skos"]
   skos_vocabularies = ["vocabularies/*.ttl"]
   skos_base_uri = "https://w3id.org/example/vocabularies/"
   ```

2. Build the site with the `dirhtml` builder, which gives each page a directory of its own.

   ```console
   sphinx-build -b dirhtml docs docs/_build/dirhtml
   ```

3. Check the build output. A concept with the URI
   `https://w3id.org/example/vocabularies/date-types/available` has its page at
   `date-types/available/index.html`. Every vocabulary, concept and collection in the files has a
   page, and nothing else does.

4. Link to a vocabulary from one of the site's own pages by listing its page address in a
   `toctree`. The generated pages are not in any table of contents on their own, and Sphinx does
   not warn about that.

   ````rst
   .. toctree::

      date-types
   ````

5. If the site's source directory is under version control, list the generated sources in
   `.gitignore`. Every build writes them again, so they need not be kept. They sit at the page
   addresses, so a vocabulary at `date-types` and its concepts need two entries.

   ```text
   date-types.rst
   date-types/
   ```

   A document of your own at a page address is kept and the build warns about it. A file whose
   first line is not the extension's own comment is never overwritten or deleted.

## The result

The built site has a page for every resource at its page address. The build prints a warning for
each resource that cannot get a page, naming it, so a build run with warnings as errors (`-W`)
fails instead of leaving a page out. Fix a warning by correcting the URI in the vocabulary file,
the base URI, or the name of your own page that is in the way.
