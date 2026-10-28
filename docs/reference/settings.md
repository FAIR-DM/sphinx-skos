# Settings

The settings sphinx-skos adds to a site's `conf.py`. A change to either one rebuilds the whole
site. To use them, follow [Publish vocabulary files as a
site](../how-to/publish-vocabulary-files.md).

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
