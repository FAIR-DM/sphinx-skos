# Goals

These are the standing directions `sphinx-skos` works toward. Each one is a capability or quality
to steer by, not a task that gets ticked off. Whether a goal is served well enough is decided in
the roadmap, the feature specifications and review, never by the goal itself.

This file carries no version numbers or release plan. For what the package is, what it stays out
of, and the principles that settle a close call, read the *Scope & philosophy* section of the
[README](README.md). The words are defined in [CONTEXT.md](CONTEXT.md).

Importance is a tag on each goal, not a ranking:

- **Essential**: not worth adopting without it.
- **Expected**: a complete, dependable version is expected to have it.
- **Aspirational**: a genuine want whose absence never makes the package incomplete.

| ID | Goal | Importance | Status | Notes |
|----|------|------------|--------|-------|
| G1 | A site turns a list of vocabulary files into one page for every vocabulary, concept and collection, each a real Sphinx document | Essential | | |
| G2 | Every page has RDF copies beside it in Turtle, JSON-LD, RDF/XML and N-Triples, holding that resource's own RDF and nothing else | Essential | | |
| G3 | A page's address is its URI with the base URI removed, so a redirect from a resource's URI reaches its page with no lookup table | Essential | | |
| G4 | A concept page shows what a reader needs to use the concept: its labels in every language, definition, notation, the collections it is in and its mapping links | Essential | | |
| G5 | Any organisation can publish its vocabularies with it, with everything site-specific set in the site's `conf.py` | Essential | | |
| G6 | A site's look and feel comes entirely from its Sphinx theme, and the extension works under any theme | Essential | | Requests for logos, colours or layout options are answered by Sphinx's theme settings, not by this package |
| G7 | Software can find a page's RDF copies from the page itself | Expected | | |
| G8 | The directives that build the generated pages can be used by hand in a site's prose pages | Expected | | |

## Direction

The intended design, recorded so the first features start from it. None of it is built yet.

- **Configuration in `conf.py`.** `extensions = ["sphinx_skos"]`, `skos_vocabularies` as a list
  of file patterns, `skos_base_uri` as the base URI.
- **Built with `dirhtml`,** so a page address is a directory and the URI maps onto it directly.
- **Pages are generated as source documents when the build starts,** the way `autosummary`
  generates its stubs. Each holds one directive: `skos:vocabulary`, `skos:concept` or
  `skos:collection`.
- **A resource's own RDF** is every triple with it as subject, plus the blank nodes those reach.
  This matches how django-controlled-vocabularies 0.3.0 defines a concept's RDF.
- **Each page names its RDF copies** in `<link rel="alternate">` elements, with their media types.
- **Tests build real sites** with `sphinx.testing`.

_Written 2026-10-28. Revise as the goals change._
