# ADR 0002 — RDF copy names follow the page's HTML file

**Status:** accepted

## Decision

A resource's RDF copies are written beside its page's HTML file, named after that file with its
suffix replaced by `.ttl`, `.jsonld`, `.rdf` or `.nt`. Under `dirhtml` that is `index.ttl`,
`index.jsonld`, `index.rdf` and `index.nt` in the page's directory. Under `html` it is
`<name>.ttl` and the rest beside `<name>.html`. Each page names its copies in
`<link rel="alternate">` elements with their media types. The names are permanent: changing them
is a breaking change.

## Why

A copy's name has to depend only on the page address and the format, so that a redirect or a
content-negotiation rule written once keeps working. Sharing the page's base name lets a web
server that negotiates content on a directory, such as Apache with `MultiViews` and
`DirectoryIndex index`, serve the right copy for an `Accept` header with no lookup table.

## Revisit if

A widely used way of serving static sites needs a different naming to negotiate content.
