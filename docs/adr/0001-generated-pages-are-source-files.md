# ADR 0001 — Generated pages are source files in the site's source directory

**Status:** accepted

## Decision

When a build starts, the extension writes one reStructuredText file per vocabulary, concept and
collection into the site's source directory, at the resource's page address, using the first
suffix in `source_suffix` that Sphinx reads as reStructuredText. Each file starts with a marker
line, then `:orphan:` and one `skos:vocabulary`, `skos:concept` or `skos:collection` directive.

- A file is rewritten only when its text changes.
- A marked file whose resource is gone is deleted at the next build, with its HTML page, its
  copied source and its RDF copies.
- A file without the marker is the site's own and is never written over or deleted. A resource
  whose address the site already uses gets no page and a build warning.

Sites that keep their source directory under version control list the generated files in
`.gitignore`.

## Why

Sphinx reads every document from a file in the source directory: `Project.discover` walks the
directory to find documents and `Builder.read_doc` reads each one from its path. There is no
public way to give Sphinx a document without a file. Registering documents in `Project`'s private
tables would work, but it could break in any Sphinx release, and a reader of the code could not
tell why it works. Rendering pages through `html-collect-pages` would make them something other
than Sphinx documents, and would need an HTML template, which the package does not ship.
`sphinx.ext.autosummary` writes stub pages into the source directory the same way, so the approach
is one Sphinx users already know.

## Revisit if

Sphinx gains a public way for an extension to provide a document that has no file.
