# Settings

The settings sphinx-skos adds to a site's `conf.py`. A change to any of them rebuilds the whole
site. To use them, follow [Publish vocabulary files as a
site](../how-to/publish-vocabulary-files.md).

## The pyproject.toml table

A site can set `project`, `html_logo`, `skos_base_uri`, `skos_vocabularies` and `skos_directory`
in a `[tool.sphinx-skos]` table instead of in `conf.py`. A site built with
[`sphinx-skos build`](command.md) can have no `conf.py` at all, and then the table, with a title,
a base URI and a list of vocabulary patterns, is the whole configuration:

```toml
[tool.sphinx-skos]
title = "Example vocabularies"
base-uri = "https://example.org/vocab/"
vocabularies = ["data/*.ttl"]
directory = "catalogue"
logo = "docs/_static/logo.svg"
```

| Key            | Sets                        |
| -------------- | --------------------------- |
| `title`        | `project` and `html_title`  |
| `base-uri`     | `skos_base_uri`             |
| `vocabularies` | `skos_vocabularies`         |
| `directory`    | `skos_directory`            |
| `logo`         | `html_logo`                 |

`title` names the site in the theme too, so the sidebar shows the title alone, without the
word "documentation" Sphinx adds. It sets `html_title` only when it sets `project` and the site sets no
`html_title` of its own. `logo` is the path of an image file, read from the directory of the
`pyproject.toml`. Sphinx copies the file into the built site and the theme shows it.

The table is read from the nearest `pyproject.toml` at or above the directory that holds
`conf.py`, or above the current directory when the site has none. The search stops at the first `pyproject.toml` it finds: if that file has no table,
no setting comes from a file further up. A relative pattern in `vocabularies` is read from the
directory of that `pyproject.toml`, and so is `logo`. A value that `conf.py` or `-D` sets wins over the table, even
when it equals the default. A key the table does not know gives a build warning that names it.

## The order settings are read in

For each setting the table can hold, the first source that sets it wins:

1. `-D` on the Sphinx command line.
2. The site's `conf.py`, even when it sets the value to the default.
3. The `[tool.sphinx-skos]` table.
4. The default.

## Theme

When the site sets no `html_theme`, in `conf.py` or with `-D`, the site is built with
[Furo](https://pradyunsg.me/furo/), which sphinx-skos depends on. A site that sets any theme keeps
it. The extension adds no stylesheet, script or static path, and one theme option, the
repository link below. This holds whether the site is built with `sphinx-skos build` or with
`sphinx-build`.

## Repository link

When the site is built with Furo and its `pyproject.toml` names the project's repository, the
footer of every page links it with a GitHub icon. The URL is the first of these keys in
`[project.urls]`, matched in any case, whose value is an `http` or `https` URL:

1. `Repository`
2. `Source`
3. `Source Code`
4. `Homepage`

```toml
[project.urls]
Repository = "https://github.com/example/vocabularies"
```

The file is the same nearest `pyproject.toml` the settings table is read from, and it needs no
`[tool.sphinx-skos]` table for this. The link goes to Furo's `footer_icons` theme option. A site
that sets `footer_icons` in its `html_theme_options` keeps its own, and its other theme options
are kept beside the link. Under any other theme, or when no key holds a URL, nothing is added and
there is no warning.

## Navigation

The theme's navigation keeps the children of every top-level entry, and below that it opens only
the branch of the page being read. On a concept's page it lists the concept's vocabulary with
that vocabulary's concepts and collections, and the other vocabularies without theirs. A site of
many vocabularies would otherwise list every concept of every vocabulary on every page.

The extension does this by replacing the `toctree` function that a theme calls to draw its
navigation, in the `html-page-context` event, before the theme reads it. The entries and their
links are Sphinx's own. Any theme that draws its navigation with `toctree` gets the same
entries.

## Front page

When the site has no document at its `root_doc`, in any source suffix, and vocabulary pages are
generated, the extension writes one. Its title is `project` and it lists the front page itself,
as "Home", then the vocabularies index and then every other document of the site, sorted by
name, so the navigation leads back to it from every page. A site that adds a front page of its
own gets the generated one deleted on the next build.

The front page is the one generated file outside the [generated-pages
directory](#skos_directory). When the site has a `docs/` directory without a front page, it is
written there at the site's root document, so a site that wants to keep it out of version
control ignores it as well as the directory, or writes a front page of its own. Without `docs/`,
the command's own source directory holds it and nothing needs ignoring.

## skos_vocabularies

- **Type**: list of strings
- **Default**: `[]`

The vocabulary files the site publishes, as glob patterns. A pattern with `**` matches in
subdirectories too. A relative pattern is read from the directory that holds `conf.py`, and an
absolute pattern is read where it points. A file that two patterns match is read once.

Each matched file must be Turtle. The files are read into one graph, so a resource described in
several files has every statement from all of them. A pattern that matches no file, and a file
that cannot be read as Turtle, each give a build warning that names the pattern or the file. The
other files are still published.

A vocabulary, concept or collection is a subject whose type is `skos:ConceptScheme`,
`skos:Concept`, `skos:Collection` or `skos:OrderedCollection`. Each gets a page. Anything else in
the files, such as an organisation or a bibliographic reference, gets none and no warning.

## skos_base_uri

- **Type**: string
- **Default**: `""`

The start of every resource URI that the site's address replaces. A resource's page address is its
URI with this string removed. Under the `dirhtml` builder the page is at that address as a
directory, so `https://example.org/vocab/` and the URI `https://example.org/vocab/a/b` give the page
`a/b/`.

A relative IRI in a vocabulary file, such as `<other-thing>`, resolves against this string, not
against the file's location.

When `skos_vocabularies` is set and `skos_base_uri` is not, the build gives one warning and
generates no page.

A resource gets a build warning naming it, and no page, when:

- its URI does not start with the base URI,
- its page address is empty, holds `#`, `?`, `\`, whitespace or a control character, starts with
  `/`, or has an empty, `.` or `..` segment,
- its page address is already used by a document of the site's own, or by a resource whose URI
  sorts first. `a` and `a/index` are the same address, and an address ending in `/` is the
  directory of that name.

The site's own document is kept in every case, including a file that `exclude_patterns` hides
from Sphinx: the page is not written over it and the warning names the address and the resource.

## skos_directory

- **Type**: string
- **Default**: `"catalogue"`

The directory, inside the site's source directory, that holds every page the extension generates.
A resource's page is at this directory followed by its page address, so with the default the
concept `https://example.org/vocab/a/b` and the base URI `https://example.org/vocab/` give the
page `catalogue/a/b/`. The directory also holds an index page, `index`, titled "Catalogue", that links every
vocabulary and every concept and collection that has a page. List it in a `toctree`, as
[Add vocabulary pages to a site](../how-to/add-vocabulary-pages-to-a-site.md) shows.

The value is a relative path with `/` between its parts, such as `catalogue` or
`reference/terms`. When it is empty, starts with `/`, or has an empty, `.` or `..` part, the build
gives one warning that names `skos_directory` and generates no page.

Keep the vocabulary files outside this directory, which a site normally ignores in version
control. The extension deletes a generated file in it when its resource goes, and a file of the
site's own at a page's address stops that page from being written.
