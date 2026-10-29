# ADR 0003 — Generated pages have a directory of their own

**Status:** accepted. Supersedes [ADR 0001](0001-generated-pages-are-source-files.md).

## Decision

The extension still writes one reStructuredText file per vocabulary, concept and collection into
the site's source directory when a build starts. The files now all go in one directory, set by
`skos_directory` and `vocabularies` by default, at the resource's page address inside it. The
extension also writes an index page, `<directory>/index`, that lists every vocabulary and, hidden,
every concept and collection.

- A generated file starts with the marker line and holds one directive. It no longer holds
  `:orphan:`, so Sphinx's check for documents in no table of contents applies to it. A site lists
  `<directory>/index` in a `toctree`.
- A file is rewritten only when its text changes. A marked file whose resource is gone, wherever
  it sits in the source directory, is deleted at the next build with its output, which removes
  the pages an earlier version wrote at the old addresses.
- A file without the marker is the site's own and is never written over or deleted. A resource
  whose address the site already uses gets no page and a build warning.
- A `skos_directory` that is empty, absolute or has an empty, `.` or `..` part generates no page
  and gives a warning.
- The vocabulary files are kept outside the directory.

## Why

Sphinx still needs a file for every document, which is the reason ADR 0001 gives. What changed
is how a site lives with those files. Pages spread over the root of the source directory needed
one `.gitignore` entry for every vocabulary, could collide with the site's own pages anywhere,
and were marked `:orphan:`, which hid them from Sphinx's table-of-contents check and left a
reader without a way to reach them from the site. One directory needs one ignore entry, one
`toctree` entry, and a clear boundary between the extension's files and the site's.

## Revisit if

Sphinx gains a public way for an extension to provide a document that has no file.
