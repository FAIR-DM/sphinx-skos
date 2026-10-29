# Domain Docs

How an agent should read this repo's domain documentation before working on the codebase.

## Before exploring, read these

- **`CONTEXT.md`** at the repo root: the vocabulary this repository uses, and the words it
  deliberately avoids.
- **`GOALS.md`**: what the package works toward, and the intended design for features not yet
  built.
- **`docs/adr/`**, when it exists: the decisions that touch the area you are about to work in.

If any of these files don't exist, proceed silently. Don't flag their absence, and don't suggest
creating them upfront.

## File structure

Single-context repo:

```
/
├── CONTEXT.md
├── CONSTITUTION.md
├── GOALS.md
├── docs/adr/        (created when the first decision is recorded)
└── sphinx_skos/
```

## Use the glossary's vocabulary

When your output names a domain concept (in an issue title, say, or a test name), use the term as
defined in `CONTEXT.md`. Don't drift to synonyms the glossary explicitly avoids. Two are worth
repeating:

- A **vocabulary** is a SKOS concept scheme. Don't call it a scheme, thesaurus or taxonomy.
- The files beside a page are **RDF copies**. Don't call them exports or downloads.

## Look and feel is out of scope

Anything about logos, colours, fonts, layout, stylesheets or templates belongs to the site's
Sphinx theme, not to this package (`CONSTITUTION.md`, Article X). A request for one is answered by
pointing at Sphinx's theme settings, never by adding an option here. The two things Article X
lets through, a site's own title and logo from its settings table and a navigation that opens
only the current branch, are not precedents for more.

## Flag conflicts with a recorded decision

If your output contradicts a decision in `docs/adr/`, surface it explicitly rather than silently
overriding it.
