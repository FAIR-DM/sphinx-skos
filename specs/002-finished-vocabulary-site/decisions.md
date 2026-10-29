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
