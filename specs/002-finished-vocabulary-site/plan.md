# Implementation Plan: A finished vocabulary site out of the box

**Feature**: `002-finished-vocabulary-site` · **Spec**: [`spec.md`](./spec.md) · **Research**:
[`research.md`](./research.md)

## Summary

Generated pages move into one directory with an index and become part of the table-of-contents
tree. A settings layer reads `[tool.sphinx-skos]` under the site's `conf.py` and makes Furo the
theme when the site chooses none. Each generated page offers its RDF as page content, and a
vocabulary's page offers whole-vocabulary files and lists its namespace prefixes. A
`sphinx-skos build` command builds a site from `pyproject.toml` alone.

## Technical context

Python 3.12+, Sphinx 9.0–9.2, rdflib 7.6, Furo (now a runtime dependency), `tomllib` and
`argparse` from the standard library. Tests build real sites with `sphinx.testing`; the command is
tested by calling its entry point in a temporary project directory.

## Constitution check

- **I Testing**: every task is test-first; tests read built output, warnings by what they name,
  fields by their data. Pass.
- **II Simplicity / III Anti-abstraction**: toctrees are written into the generated sources rather
  than built as nodes; the command wraps `build_main`. One new module for the command, one for the
  settings layer. Pass.
- **IV Integration-first**: every story is tested by building a site. Pass.
- **V Security**: downloads and prefixes are reference and text nodes; the generated sources hold
  only document names and the site's own `project`, which is the site's text, not a vocabulary's.
  The index's title and the front page's title are written into reStructuredText: `project` is
  escaped for reStructuredText before it is written (T012). Pass.
- **VII Dependencies**: Furo becomes a dependency because the spec makes it the default theme
  (FR-009); deptry's DEP002 is waived for it by name with the reason. Pass.
- **VIII i18n**: `Download`, `Namespace prefixes` and the index's title `Vocabularies` go through
  `translate`. Pass.
- **IX Cohesion**: `SiteSettings` (settings layer) and `SiteBuild` (command) are classes;
  `GeneratedPages` and `RdfCopies` grow methods. Pass.
- **X, XI, XIII**: amended by this feature (spec, *Amendments*); T014 lands the amendments. Pass
  once amended.
- **XIV**: below 1.0.0 the address move is a minor release; recorded in `CHANGELOG.md`. Pass.

## Design

### Settings (`sphinx_skos/settings.py`, new): `SiteSettings`

Connected to `config-inited` at priority 400 (before Sphinx's own handlers read the theme).

- `set_by_site(config, name)`: whether `conf.py` or `-D` set `name`, from `config.overrides` and
  `config._raw_config`. The one place that reads the private attribute, with the reason in its
  docstring (research R4).
- `find_table(confdir)`: the nearest `pyproject.toml` from `confdir` upward that has
  `[tool.sphinx-skos]`; returns the table and its directory, or `None`.
- `apply(app, config)`: for each key of the table (`title`, `base-uri`, `vocabularies`,
  `directory`), set the mapped setting unless `set_by_site`; relative `vocabularies` patterns made
  absolute against the table's directory; an unknown key warns naming it. Then, unless
  `set_by_site(config, "html_theme")`, set `html_theme = "furo"`.

`Vocabularies` already resolves absolute patterns as they are (`find_files`), so no change there.

### Generated pages (`sphinx_skos/pages.py`)

- New setting `skos_directory` (`str`, default `"vocabularies"`, rebuild `env`), registered in
  `setup()`.
- `GeneratedPages.__init__` takes the directory; `find_docname` returns
  `<directory>/<address>`. A directory that is empty, absolute, or has an empty, `.` or `..`
  segment warns naming `skos_directory` and yields no page (FR-018).
- The index document `<directory>/index` and, when the site has no root document, the root
  document are reserved before any resource is placed, so a resource at address `index` collides
  as any other address would.
- `source_text` loses `:orphan:`. A vocabulary's source gains, after its directive, a hidden
  toctree listing `concepts_in` then `collections_in` (with the site's `language`), as absolute
  document names, for those that have a page.
- New `index_text()`: the marker, the title `Vocabularies` (translated) and a `:maxdepth: 1`
  toctree of every vocabulary with a page, sorted by title, then a hidden toctree of every concept
  and collection with a page that no vocabulary lists.
- New `front_page_text(project)`: the marker, `project` as title, and a toctree of
  `<directory>/index` and, under `:glob:`, `*`.
- `write()` writes the index, and the front page when it is due, through the same
  write-when-changed and never-over-the-site's-own path as every page.
- `clean()` is unchanged; it already removes every marked file the build no longer produces,
  including pages at the old addresses and a front page the site has replaced.
- `uri_for` and the directives are unchanged: the index and front page have no URI.

`find_site_documents` in `__init__.py` already excludes marked files, so the site's own root
document is found by checking `root_doc` against it.

### RDF copies and downloads (`sphinx_skos/copies.py`, `sphinx_skos/vocabularies.py`, `sphinx_skos/directives.py`)

- `Vocabularies.load` parses with `Graph(bind_namespaces="none")` and keeps the per-file graph in
  `self.files: dict[Path, Graph]`, in file order. `own_prefixes` is then exactly what the file
  declares, which also drops rdflib's default prefixes from the Turtle copies; the copies'
  prefixes test is checked against that.
- `Vocabularies.vocabulary_files(uri, language)`: the files with a statement whose subject is the
  scheme or one of its concepts or collections.
- `Vocabularies.vocabulary_graph(uri, language)`: the union of those files' graphs, with every
  file's declared prefixes bound.
- `Vocabularies.declared_prefixes(uri, language)`: the sorted, distinct `(prefix, namespace)`
  pairs those files declare.
- `RdfCopies.whole_paths(outdir, docname)`: `<outdir>/<docname without a trailing /index><suffix>`
  per format. `RdfCopies.write_whole(uri, outdir, docname)` serialises `vocabulary_graph` there.
  `write_copies` in `__init__.py` calls it for a vocabulary's generated page when the builder is
  `dirhtml` (research R7). `GeneratedPages.remove_output` also removes a gone vocabulary's whole
  files.
- `ResourceDirective` gains a `Download` field, last, on the resource's generated page under an
  HTML builder only: four references labelled `Turtle`, `JSON-LD`, `RDF/XML`, `N-Triples`. Their
  targets are the copy file names from `RdfCopies.paths(builder.get_outfilename(docname))`, or for
  a vocabulary under `dirhtml` the whole files, relative to the page.
- `VocabularyDirective` gains a `Namespace prefixes` field, by hand and generated alike, when the
  vocabulary's files declare any: a bullet list, each item `prefix:` then the namespace URI as a
  link. Empty prefix shown as `:`.

### The command (`sphinx_skos/cli.py`, new): `SiteBuild`

`[project.scripts] sphinx-skos = "sphinx_skos.cli:main"`. `main(argv=None)` parses `build
[-o OUTPUT] [-W]` with `argparse` and returns `SiteBuild(root=Path.cwd(), ...).run()`.

- `run()`: if `pyproject.toml` has no `[tool.sphinx-skos]` table and `docs/conf.py` does not
  exist, print a message naming both and return 2. Otherwise build with `build_main` as research
  R6 sets out, and return its exit code.
- Source directory: `docs/` if it exists, else `_build/source/` (created). Output default
  `_build/site/`, doctrees `_build/doctrees/`, all under `root`.

### Documentation

- `docs/how-to/publish-vocabulary-files.md` rewritten around `sphinx-skos build`.
- New `docs/how-to/add-vocabulary-pages-to-a-site.md`: `conf.py` site, the index in a toctree,
  `.gitignore`, moving from 0.3.
- `docs/reference/settings.md`: `skos_directory`, the `[tool.sphinx-skos]` table and the order
  settings are read in, the Furo default.
- New `docs/reference/command.md`: `sphinx-skos build` and its options.
- `docs/reference/rdf-copies.md`: whole-vocabulary files.
- `docs/reference/directives.md`: the `Download` and `Namespace prefixes` fields.
- README quickstart and scope, CHANGELOG, `CONTEXT.md`, GOALS, CONSTITUTION, new ADR superseding
  ADR 0001, and the feature 001 specification (T014).

## Order

US2 first: the directory and the index are what the navigation, the front page and the command
stand on. Then US3 (toctrees), US4 (downloads, prefixes), US1 (settings layer, Furo, front page,
command).
