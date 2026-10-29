# Settings

The settings sphinx-skos adds to a site's `conf.py`. A change to any of them rebuilds the whole
site. To use them, follow [Publish vocabulary files as a
site](../how-to/publish-vocabulary-files.md).

## The pyproject.toml table

A site can set `project`, `skos_base_uri`, `skos_vocabularies` and `skos_directory` in a
`[tool.sphinx-skos]` table instead of in `conf.py`:

```toml
[tool.sphinx-skos]
title = "Example vocabularies"
base-uri = "https://example.org/vocab/"
vocabularies = ["data/*.ttl"]
directory = "vocabularies"
```

| Key            | Sets                |
| -------------- | ------------------- |
| `title`        | `project`           |
| `base-uri`     | `skos_base_uri`     |
| `vocabularies` | `skos_vocabularies` |
| `directory`    | `skos_directory`    |

The table is read from the nearest `pyproject.toml` at or above the directory that holds
`conf.py`. The search stops at the first `pyproject.toml` it finds: if that file has no table,
no setting comes from a file further up. A relative pattern in `vocabularies` is read from the
directory of that `pyproject.toml`. A value that `conf.py` or `-D` sets wins over the table, even
when it equals the default. A key the table does not know gives a build warning that names it.

## Theme

When the site sets no `html_theme`, in `conf.py` or with `-D`, the site is built with
[Furo](https://pradyunsg.me/furo/), which sphinx-skos depends on. A site that sets any theme keeps
it. The extension adds no stylesheet, script, static path or theme option.

## Front page

When the site has no document at its `root_doc`, in any source suffix, and vocabulary pages are
generated, the extension writes one. Its title is `project` and it lists the vocabularies index
and then every other document of the site, sorted by name. A site that adds a front page of its
own gets the generated one deleted on the next build.

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
- **Default**: `"vocabularies"`

The directory, inside the site's source directory, that holds every page the extension generates.
A resource's page is at this directory followed by its page address, so with the default the
concept `https://example.org/vocab/a/b` and the base URI `https://example.org/vocab/` give the
page `vocabularies/a/b/`. The directory also holds an index page, `index`, that links every
vocabulary and every concept and collection that has a page. List it in a `toctree`, as
[Add vocabulary pages to a site](../how-to/add-vocabulary-pages-to-a-site.md) shows.

The value is a relative path with `/` between its parts, such as `vocabularies` or
`reference/terms`. When it is empty, starts with `/`, or has an empty, `.` or `..` part, the build
gives one warning that names `skos_directory` and generates no page.

Keep the vocabulary files outside this directory, which a site normally ignores in version
control. The extension deletes a generated file in it when its resource goes, and a file of the
site's own at a page's address stops that page from being written.
