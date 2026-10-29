# Give a site a ready-made layout

Build a vocabulary site with a finished layout without choosing a theme or writing any theme
settings. Do this when the site needs to look finished and has no theme of its own to keep.

## Before you start

You need a site that publishes its vocabulary files with sphinx-skos, as in [Publish vocabulary
files as a site](publish-vocabulary-files.md).

## Steps

1. Install sphinx-skos with the `book` extra, which installs
   [sphinx-book-theme](https://sphinx-book-theme.readthedocs.io/) with it.

   ```console
   pip install "sphinx-skos[book]"
   ```

   In a project managed with uv, add it to the dependency group the site is built from, for
   example `uv add --group docs "sphinx-skos[book]"`.

2. Remove `html_theme` from the site's `conf.py` if it is there. The layout applies only to a
   site that sets no theme, in `conf.py` or with `-D html_theme=…` on the command line.

3. Build the site.

   ```console
   sphinx-build -b dirhtml docs docs/_build/dirhtml
   ```

## The result

The site is built with sphinx-book-theme, laid out for a vocabulary site:

- The left sidebar lists every vocabulary, under a *Vocabularies* caption, and the pages the
  site's root document lists in its own `toctree`, on every page. A vocabulary the root document
  already lists keeps its place and is not listed twice.
- The top bar has no search button. The search field is in the sidebar.
- No page has a right-hand sidebar, and the article takes the width it leaves.
- The download menu of a generated page offers the resource's [RDF copies](../reference/rdf-copies.md)
  in Turtle, JSON-LD, RDF/XML and N-Triples, in place of the page's source. The site's own
  pages keep the theme's menu.

## Change part of the layout

Every setting in `conf.py` wins over the layout's defaults. To put the right-hand sidebar back,
for example, set its items as sphinx-book-theme documents them:

```python
html_theme_options = {"secondary_sidebar_items": ["page-toc"]}
```

The article then keeps the theme's own width. Any other option of sphinx-book-theme, `html_logo`,
`html_title` and the rest work as the theme describes.

To leave the layout entirely, set `html_theme`, even to `"sphinx_book_theme"`. The extension then
sets nothing for the theme, and the site looks as that theme and its own settings make it look.
