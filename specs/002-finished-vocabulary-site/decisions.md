# FS-002 decisions

Choices made where issues #19 to #23 were silent. Each is settled for this feature and can be
overruled at review of the specification.

## D1. Four stories, by who does what

The five issues describe two people. A developer either builds a site with one command (#21) or
adds the pages to a Sphinx site of their own (#23), and either way gets Furo when they choose no
theme (#20). A reader either finds a concept through the navigation (#23) or takes its data away
(#19, #22). Downloads and prefixes are one story because a reader looks for both for the same
reason: to use the vocabulary's RDF somewhere else.

## D2. Downloads are page content under any theme

Issue #19 asks for downloads under any theme with nothing added to `conf.py`, and constitution
Article X rules out a template. The downloads are therefore part of each page's content, under
Furo as under every other theme.

## D3. The vocabulary's RDF copies keep their meaning

A vocabulary page's `<link rel="alternate">` elements still name the scheme's own RDF, so the
answer software gets when it resolves a vocabulary's URI does not change. The whole-vocabulary
files are a separate set, offered to people from the page.

## D4. A whole-vocabulary file is the graph of the files it comes from

Issue #19 asks for "the same graph as the files it was read from, with nothing added or dropped".
Taking that literally keeps statements that belong to no single resource, such as a publishing
organisation, which a selection of resources would drop. The cost falls on a file holding several
vocabularies: each of them offers the whole file.

## D5. The GitHub Pages workflow is out of scope

The reusable workflow that publishes a site keeps running `sphinx-build` against a `docs/conf.py`.
Changing it to run `sphinx-skos build` is a separate change to the workflow file.

## D6. Furo is the default theme, with nothing added to it

When a site chooses no theme it gets Furo, installed with the package. Furo's sidebar shows the
site's tables of contents, hidden ones included, so the navigation needs nothing from the package
beyond the tables of contents themselves. The package therefore still ships no stylesheet,
template or theme option, and Article X changes only to allow the one default setting.

## D7. Whole-vocabulary files are written by `dirhtml` only

They are named after the vocabulary's page address, `vocabularies/date-types.ttl` for the page
`vocabularies/date-types/`. Under `dirhtml` no other file is ever written at that path. Under the
`html` builder the vocabulary's own Turtle copy is, so under any builder but `dirhtml` a
vocabulary page offers its own copies instead. `dirhtml` is the builder the package documents and
the one page addresses rely on. This narrows FR-023 to that builder (design review DR-006).

**ADR:** none — a naming rule recorded in the RDF copies reference, nothing else depends on it.

## D8. Whether the site set a value is read from Sphinx's raw configuration

A site that sets `html_theme = "alabaster"` must get alabaster, so comparing a value with its
default cannot tell a site's choice from no choice. Sphinx has no public accessor for what
`conf.py` set; `Config._raw_config` holds it. It is read in one method whose docstring says why,
and the CI matrix covers every supported Sphinx version. The settings table is read only from the
nearest `pyproject.toml`, never from an ancestor past it (design review DR-011).

**ADR:** pending — decided at convergence.

## D9. The generated front page is the one generated file outside the directory

FR-013 keeps generated pages in their own directory, and FR-003 asks for a front page when the
site has none. When `docs/` exists without a front page, the front page is written at the site's
root document, outside the directory, and a site that wants to ignore it adds a second
`.gitignore` entry or writes a front page of its own. Without `docs/`, the source directory is
the command's own and nothing is ignored. Raised by the design review (DR-007).

**ADR:** none — recorded in the how-to; nothing else depends on it.

## D10. A site's own `conf.py` lists the extension itself

`sphinx-skos build` adds the extension only when there is no `docs/conf.py`. A `conf.py` lists
`sphinx_skos` in its `extensions`, like any Sphinx site, so it is read once and never rewritten
on the command line (design review DR-008).

**ADR:** none — documented in the command reference.

## D11. Vocabulary files are kept outside the generated-pages directory

The default directory `vocabularies/` is also where the earlier how-to kept vocabulary files. The
documentation now keeps them outside it (`data/` in the examples, `../vocabularies/` in the
README), and the move-from-0.3 steps move them before the directory is ignored (DR-003).

**ADR:** none — documentation and test layout.
