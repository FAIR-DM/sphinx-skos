# FS-002 research

Read against `main` at v0.3.3, Sphinx 9.2.0, rdflib 7.6 and Furo 2025.12.19.

## Planning notes, answered

**"Generated pages should work the way sphinx-autodoc2 writes its API pages."** Adopted.
sphinx-autodoc2 writes every page under one directory of the source (`apidocs/` by default) with
an `index` that the site lists once, and each package page lists its modules in a toctree. The
plan does the same: `skos_directory` (default `vocabularies`), a generated `index` there, and a
hidden toctree in each vocabulary's generated source.

**"Default to Furo, which is included."** Adopted. Furo moves from the `dev` group into
`dependencies`, and `html_theme` defaults to `furo` when the site sets no theme (R4). Furo's
sidebar is the site's global toctree, hidden entries included, with the current page's branch
expanded, so the navigation needs no template, stylesheet or theme option (R3).

**"As easy as fairdm-docs."** Adopted in shape, not in code. fairdm-docs reads a `[tool.*]` table
and builds with an optional `docs/conf.py` that overrides it. Its code is Django- and
portal-specific, so none of it is reused. The command here is one subcommand, `build` (R6).

**"Namespace prefixes should read like pyLODE's."** Adopted. pyLODE shows a table of prefix and
namespace URI. The vocabulary page gets one field holding that list (R8).

## R1. Where generated pages go

`GeneratedPages.find_docname` gives a resource the document `<address>`; it becomes
`<skos_directory>/<address>`. Every existing rule (unusable addresses, collisions with the site's
own documents, write-only-when-changed) is unchanged, applied to the longer name.

`GeneratedPages.clean` already deletes every marked file in the source directory that the current
build did not produce, wherever it is. Pages an earlier version wrote at the old addresses carry
the marker, so the first build after the upgrade deletes them with no new code (US2 scenario 8).

## R2. Tables of contents

- Sphinx warns "document isn't included in any toctree" for a document no toctree lists and
  that is not `:orphan:`. A document listed only in a `:hidden:` toctree counts as included.
- A document listed in two toctrees gets `logger.info`, not a warning
  (`sphinx/environment/__init__.py`, `_check_toc_parents`), so a concept in two vocabularies
  builds clean (US3 scenario 5, FR-020).
- The simplest place for the toctrees is the generated source itself: the vocabulary page's
  source gains a `.. toctree::` with `:hidden:` after its directive, and the index's source a
  visible one. No node building and no new directive. Entries are absolute document names
  (`/vocabularies/date-types/available`), so they do not depend on the page's own depth.
- A concept or collection in no vocabulary would be in no toctree. It is listed in a hidden
  toctree on the index, so no generated page needs `:orphan:`.

## R3. Furo's navigation

Furo renders `toctree(collapse=False, titles_only=True, maxdepth=-1, includehidden=True)` from the
root document in its left sidebar on every page, and marks the current page and its ancestors.
That is US3 in full once the toctrees of R2 exist. Testing Furo's rendering would test a
dependency (`testing.md`); the tests read the toctree tree Sphinx records
(`env.toctree_includes`), which is what Furo draws.

## R4. Knowing whether the site set a value

FR-005, FR-010 and FR-011 need to know whether the site's `conf.py` set `html_theme`,
`project` or an `skos_*` setting, not merely whether its value differs from the default: a site
that sets `html_theme = "alabaster"` must get alabaster. Sphinx's `Config` keeps what `conf.py`
set in `_raw_config` and what `-D` set in `overrides`; there is no public accessor for the former.

- Comparing with the default is wrong for a site that sets the default explicitly.
- Reading `conf.py` a second time with `Config.read` is public but runs the site's code twice.
- `config._raw_config` is read in one method, with a comment saying why, and the CI matrix
  (Sphinx 9.0 to 9.2) runs the tests that pin it. This is the plan's choice.

The handler runs on `config-inited`, before any builder reads `html_theme`.

## R5. Settings from `pyproject.toml`

`tomllib` is in the standard library from Python 3.11. The extension looks for `pyproject.toml`
in the configuration directory and its parents, nearest first, and stops at the first one it
finds, table or not, so a project never takes settings from an unrelated ancestor. Keys map to settings: `title` to `project`, `base-uri` to
`skos_base_uri`, `vocabularies` to `skos_vocabularies` and `directory` to `skos_directory`. A
relative vocabulary pattern from the table is made absolute against the table's directory, so it
is read from there (FR-002) while one from `conf.py` is still read from the configuration
directory. An unknown key gives a warning naming it.

## R6. The command

`sphinx.cmd.build.build_main(argv)` is Sphinx's public entry point and returns the exit code.

- **No `docs/conf.py`**: `-C` (no configuration file) and `-D extensions=sphinx_skos`. With `-C`,
  Sphinx's configuration directory is the source directory.
- **`docs/conf.py`**: used as it is. It lists `sphinx_skos` in its own `extensions`, like any
  Sphinx site. (`-D extensions=` would replace its list outright, so adding the extension for it
  would mean running `conf.py` twice.)
- **Source directory**: `docs/` when it exists, else `_build/source/`, created empty.
- **Output**: `_build/site/` by default, `-o/--output` to change it; doctrees in
  `_build/doctrees/`. All relative to the directory holding `pyproject.toml`.
- **`-W/--fail-on-warning`** passes `-W` through. `build_main` returns non-zero on a failed build.
- **Neither a table nor `docs/conf.py`**: exit 2 with a message naming both.

## R7. Whole-vocabulary files

`Vocabularies.load` parses each file into its own `Graph` and discards it after merging. The plan
keeps each file's graph as well, parsed with `bind_namespaces="none"` so that `namespaces()` is
exactly what the file declares (`Graph()` binds rdflib's thirty defaults; checked). The merged
graph keeps the defaults: the pages shorten property names with them.

A vocabulary is *stated in* a file when the file has a statement whose subject is the scheme or
one of the vocabulary's concepts or collections (`concepts_in`, `collections_in`). Its
whole-vocabulary graph is the union of those files' graphs, which for one vocabulary per file is
the file's graph exactly (SC-003).

**Name and place.** Written beside the page's output directory and named after the page address,
`vocabularies/date-types.ttl` for the page `vocabularies/date-types/`, as the preview did. Under
`dirhtml` nothing else is ever written there: every page is a directory holding `index.html` and
its copies are `index.*`. Under the `html` builder the vocabulary's own copy is at that same path,
so the files are written only by `dirhtml`, the builder the package documents. Under any other
builder a vocabulary page's downloads are its own copies.

## R8. What the page shows

- **Downloads**: one field, `Download` (translated), holding a link per format, labelled by the
  format's name, to the copy's file name relative to the page, as the `<link rel="alternate">`
  elements already do. Shown only on a generated page and only by an HTML builder. A reference
  node with `refuri`, so the HTML writer escapes it (Article V).
- **Prefixes**: one field, `Namespace prefixes` (translated), on a vocabulary's generated page and
  by hand alike, holding a bullet list of `prefix:` followed by the namespace URI as a link, sorted
  by prefix then namespace. The empty prefix is shown as `:`.

## R9. The front page

Written by the extension, for any site, when the site has no root document of its own
(`root_doc`, any suffix) and lists vocabularies: a marked file holding the site's `project` as its
title and a toctree of the index and every document of the site's own, listed by name. A glob
would warn when it matches nothing, as it does in a site with no `docs/`, and `*` never matches a
document in a subdirectory. A site that adds a front page of its own gets the
generated one deleted by `clean`, as a marked file the build no longer produces.

## R10. Theme default and dependencies

Furo registers itself through the `sphinx.html_themes` entry point, so `html_theme = "furo"`
needs no import. deptry reports a dependency nothing imports (DEP002); `furo` is listed in
`[tool.deptry.per_rule_ignores]` with a comment saying it is a theme Sphinx loads by name.

## What already exists

- Writing, collision checks and clean-up of generated sources: this repo, `GeneratedPages`.
- Copy file names and alternate links: this repo, `RdfCopies`.
- Table-of-contents navigation: Sphinx (`toctree`) and Furo. Nothing new.
- Theme selection: Sphinx (`html_theme`). One default set.
- Reading `pyproject.toml`: the standard library, `tomllib`.
- The command's build: Sphinx, `sphinx.cmd.build.build_main`.
- Argument parsing: the standard library, `argparse`.
- Prefix list: rdflib, `Graph.namespaces()` with `bind_namespaces="none"`.
- New code: the settings layer (`config-inited`), the command, the whole-vocabulary writer, two
  fields.
