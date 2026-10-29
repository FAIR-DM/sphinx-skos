# Python API

The classes and functions in the `sphinx_skos` package. A site needs none of them to publish its
vocabularies: the [settings](settings.md) are the whole interface for that. They are here for a
site or a package that needs different behaviour, which it gets by subclassing one class and
overriding one method. Before 1.0.0 they can change in a minor release, and the changelog says
when they do.

Every module that warns does so through its own `logger`, from `sphinx.util.logging`, so its
warnings take part in Sphinx's warning handling, including `-W`.

## Module `sphinx_skos`

`setup(app)`
: Registers the three settings, the `skos` domain, the `DownloadLinks` post-transform and the
  build handlers. Sphinx calls it when the
  site lists `sphinx_skos` in `extensions`.

`generate_pages(app)`
: Connected to Sphinx's `builder-inited` event. Loads the vocabulary files into a `Vocabularies`,
  works out a `GeneratedPages` from them, writes the page sources, and stores both on the
  `SKOSDomain`.

`find_outdated(app, env, added, changed, removed)`
: Connected to Sphinx's `env-get-outdated` event. When the fingerprint of the vocabulary files,
  or the extension's version, differs from the one the environment was last read with, it stores
  the new one and names every document of the site as outdated, so a rebuild gives what a clean
  build gives, including after the extension is upgraded.

`write_copies(app, pagename, templatename, context, doctree)`
: Connected to Sphinx's `html-page-context` event. For a page the extension generated, under a
  builder that writes HTML, it writes the page's [RDF copies](rdf-copies.md) and adds an
  `<link rel="alternate">` element for each to the page's `metatags`. Under `dirhtml` a
  vocabulary's page also gets its whole-vocabulary files. Other pages are left alone.

`release_shadowed_pages(app, config)`
: Connected to Sphinx's `config-inited` event. Deletes each generated source beside a file of the
  site's own for the same document with another suffix, so that Sphinx does not warn about two
  files for one document.

`find_site_documents(app)`
: The names of the site's own documents: every document in the source directory whose file does
  not start with the generated-page marker line.

## Module `sphinx_skos.settings`

`SiteSettings`
: Reads the site's [settings table](settings.md#the-pyprojecttoml-table) and chooses its default
  theme. `apply(app, config)` is connected to Sphinx's `config-inited` event, before Sphinx reads
  the theme: it sets each setting the table holds unless `conf.py` or `-D` set it, then sets
  `html_theme` to `furo` unless the site set a theme. `find_table(confdir)` gives the table of
  the nearest `pyproject.toml` and its directory, or `None`. `set_by_site(config, name)` says
  whether `conf.py` or `-D` set a value, which comparing with the default cannot tell.

## Module `sphinx_skos.cli`

`main(argv=None)`
: The `sphinx-skos` command: parses the `build` subcommand and its options, builds the site of the
  current directory and returns the exit code. `argv` is the command line without the program
  name, `sys.argv` when omitted. See the [command reference](command.md).

`SiteBuild(root, output, fail_on_warning)`
: One build of the site that `root` holds. `run()` builds it with `dirhtml` and returns Sphinx's
  exit code, or 2 when the project has neither a `[tool.sphinx-skos]` table nor a `docs/conf.py`.
  `conf_py` is the path of the project's `docs/conf.py`, whether or not the file exists.

## Module `sphinx_skos.vocabularies`

`Vocabularies(patterns, confdir, base_uri)`
: The site's vocabulary files read into one `rdflib.Graph`. A relative IRI in a file resolves against
  `base_uri` (default `""`: it stays relative). Its attributes are `patterns`, `base_uri`, `graph`,
  `fingerprint` (a SHA-256 digest of the files read) and `resources` (the kind of each vocabulary,
  concept and collection, by URI). A file's namespace prefixes are bound in `graph` too, unless
  an earlier file bound the same prefix. Its methods read SKOS facts from the graph:
  `title(uri, language)`, `labels(uri, property_)` for the preferred or alternative labels and
  `definitions(uri)`. Labels and definitions come as `Label`s sorted by language tag, then text.
  `read_literals(uri, predicate)` reads any property's literals the same way, and
  `choose(labels, language)` picks the label in `language`, else the first.
  `statements(subject)` gives every object of every property a resource or blank node states,
  by property, leaving out hidden labels. `name(uri, language)` gives the text a link to a URI
  shows: a resource's title, else the first of the `NAME_PROPERTIES` the files state for it,
  else the URI. `curie(uri)` gives a URI as a prefixed name, or the URI when no prefix covers it.
  `sort_values(values, language)` puts the objects of a property in the order a page shows them,
  and `blank_key(blank, seen)` gives the text blank nodes are ordered by, made from what they
  state because their identifiers change from build to build.

  The methods that return resources give URIs sorted by title, then URI, and take the site's
  `language` for the title: `vocabularies_of(concept, language)` (by `skos:inScheme`,
  `skos:topConceptOf` or the vocabulary's `skos:hasTopConcept`), `collections_of(concept,
  language)`, `relations(concept, property_, language)` for broader, narrower or related stated on
  either concept, and `concepts_in(vocabulary, language)` and `collections_in(vocabulary, language)` (a collection is in
  a vocabulary when it states `skos:inScheme` for it or a member is a concept in it),
  `members_of(collection, language)` (list order for an ordered collection, else by title), and
  `mappings(concept, language)`, which gives each mapping property the concept
  uses with its `Target`s. `sort_by_title(uris, language)` applies that order to any URIs.
  `uri_objects(subject, predicate)` and `uri_subjects(predicate, object_)` read the URIs a
  property points at or comes from. `listed_members(collection)` gives an ordered collection's
  members in list order and `all_members(collection)` every member it names.

`Vocabularies.files`
: Each file that could be read as its own `rdflib.Graph`, in file order, holding the prefixes that
  file declares and no others. `vocabulary_files(uri, language)` gives the files with a statement
  whose subject is a vocabulary or one of its concepts or collections, `vocabulary_graph(uri,
  language)` the union of their graphs, and `declared_prefixes(uri, language)` the distinct
  `(prefix, namespace)` pairs they declare, sorted by prefix and then namespace.

`Vocabularies.own_rdf(uri)`
: A resource's own RDF as a new graph: every triple with the resource as subject and those of the
  blank nodes they reach, with the namespace prefixes of the vocabulary files.

`Kind`
: The kind of a resource: `"vocabulary"`, `"concept"` or `"collection"`.

`Label`
: A piece of text and its language: `text`, and `language`, which is an empty string when the text
  has no language tag.

`LabelProperty`
: Which labels to read: `"prefLabel"` or `"altLabel"`.

`RelationProperty`
: Which relation to read: `"broader"`, `"narrower"` or `"related"`.

`Target`
: What a mapping link points at: `value`, and `is_uri`, which is false for a literal written where
  a URI belongs.

## Module `sphinx_skos.pages`

`GeneratedPages(vocabularies, base_uri, directory, language, source_suffix, site_documents, project, root_doc)`
: The page of every resource that can have one, in the `skos_directory` directory.
  `has_directory(directory)` says whether a directory is usable and warns when it is not.
  `docname_for(uri)` gives a resource's document
  name, or `None` when it has no page. `members_of(vocabulary)` gives the concepts and then the
  collections of a vocabulary that have a page, and `toctree_text(uris, option)` gives a
  `toctree` directive listing their pages; a vocabulary's source holds one, hidden.
  `index_text()` gives the source of the index page, at `index_docname`, that lists every
  vocabulary and, hidden, the concepts and collections no vocabulary lists. `front_page_text()`
  gives the source of the front page, at `front_docname`, which exists only when the site has no
  document at `root_doc`: the `project` as title and a list of the index and then every document of
  the site's own. `toctree_of(docnames, option)` gives a `toctree` directive listing documents.
  `write(srcdir)` writes the page sources, the index and the front page, each through `write_source(srcdir, docname, text, subject)`, which leaves a file of the site's own alone. `clean(srcdir,
  builder, skip)` deletes the generated sources whose resource is gone and, for an HTML builder,
  their output file, RDF copies, whole-vocabulary files (under `dirhtml`) and copied source.
  `find_generated(srcdir, suffixes, skip)` lists the generated sources in a source directory and
  `release_shadowed(srcdir, suffixes, skip)` deletes those that a file of the site's own with
  another suffix shadows. `uri_for(docname)` gives the resource a
  generated document is the page of, or `None`; its `uris` attribute holds them all.

## Module `sphinx_skos.copies`

`RdfCopies(vocabularies)`
: Writes the [RDF copies](rdf-copies.md) of a page. `write(uri, outfile)` serialises a resource's
  own RDF in every format beside the page's output file, `paths(outfile)` says where the copies
  of a page are and `alternate_links(outfile)` gives the `<link rel="alternate">` elements that
  name them. `whole_paths(outdir, docname)` says where a vocabulary's whole files are and
  `write_whole(uri, outdir, docname, language)` writes the graph of the vocabulary's files
  there.

`CopyFormat`, `COPY_FORMATS`
: A format a copy is written in: `suffix`, `rdflib_format`, `media_type` and `label`, the name a
  download link shows. `COPY_FORMATS` lists
  the four.

## Module `sphinx_skos.domain`

`SKOSDomain`
: The `skos` domain. It holds the three directives, and the `vocabularies` and `pages` of the
  build in progress, and the `fingerprint` of the vocabulary files and the extension `version` the
  environment was last read with in its `data`.

## Module `sphinx_skos.directives`

`ResourceDirective`
: The base of the three directives. It takes a resource URI as its one argument. `fields(uri)`
  returns the field list shown under the page title: the URI, then the fields `facts(uri)` gives,
  which a subclass extends, then the fields of `metadata_properties()`, then `other_fields`
  for every property no other field shows. `shown` names the properties a kind's own fields
  show, so they are left out of the other fields. `text_properties()` and
  `metadata_properties()` give the name of each labelled field and the property it shows, and
  `property_facts(subject, properties)` reads them. `other_fields(subject, shown, seen)` builds
  one field for each other property, named by a link to it. `values(values, seen)` gives the
  paragraphs for the objects of a property, `literal_value(literal)` a literal's text and tag,
  and `label_values(labels)` the paragraphs for labels with their languages.
  `field(name, *values)` builds one field, named by text or by a link; a list value is placed as it is. `link(uri)` shows a URI
  as a cross-reference to its page, as a link to itself by its `name` when it has no page, or as
  plain text when its scheme is `javascript`, `data` or `vbscript`; `uri_reference(uri, text)`
  makes that last choice. `links(uris)` does so for each URI and `target_links(targets)` for each
  `Target` of a mapping link. `download_field()` builds the last field of a generated page: a link
  for each format of an RDF copy, with no target yet. `vocabularies` is the `Vocabularies` of the build in progress and
  `pages` its `GeneratedPages`.

`VocabularyDirective`, `ConceptDirective`, `CollectionDirective`
: The `skos:vocabulary`, `skos:concept` and `skos:collection` directives. Each shows every
  statement its resource carries except hidden labels, as the [directives
  reference](directives.md#what-is-shown) sets out. A vocabulary adds links to its concepts and
  collections and, from `prefix_list(uri)`, a bullet list of the namespace prefixes its files declare, a collection links to its members, and a concept links to its vocabulary,
  collections, broader, narrower and related concepts, with one field for each mapping property
  it uses. The names of the labelled fields are translated through the `sphinx_skos` message
  catalogue.

`DownloadLinks`
: A Sphinx post-transform. As a page is resolved for writing, it points each link of the download
  field at the page's RDF copies, or at the vocabulary's whole files under `dirhtml`, relative to
  the page, and removes the field under a builder that does not write HTML.

`translate`
: The function the directives pass their fixed text through: `sphinx.locale.get_translation`
  for the `sphinx_skos` catalogue. A site that registers a `sphinx_skos` catalogue with
  `app.add_message_catalog` gets the field names in its `language`. To extract the messages with
  babel, give `-k translate`.
