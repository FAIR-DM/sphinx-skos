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
: Registers the two settings, the `skos` domain and the build handlers. Sphinx calls it when the
  site lists `sphinx_skos` in `extensions`.

`generate_pages(app)`
: Connected to Sphinx's `builder-inited` event. Loads the vocabulary files into a `Vocabularies`,
  works out a `GeneratedPages` from them, writes the page sources, and stores both on the
  `SKOSDomain`.

`find_outdated(app, env, added, changed, removed)`
: Connected to Sphinx's `env-get-outdated` event. When the fingerprint of the vocabulary files
  differs from the one the environment was last read with, it stores the new one and names every
  document of the site as outdated, so a rebuild gives what a clean build gives.

`find_site_documents(app)`
: The names of the site's own documents: every document in the source directory whose file does
  not start with the generated-page marker line.

## Module `sphinx_skos.vocabularies`

`Vocabularies(patterns, confdir)`
: The site's vocabulary files read into one `rdflib.Graph`. Its attributes are `patterns`, `graph`,
  `fingerprint` (a SHA-256 digest of the files read) and `resources` (the kind of each vocabulary,
  concept and collection, by URI). Its methods read SKOS facts from the graph: `title(uri, language)`,
  `labels(uri, property_)` for the preferred or alternative labels, `definitions(uri)` and
  `notations(uri)`. Labels and definitions come as `Label`s sorted by language tag, then text.
  `read_literals(uri, predicate)` reads any property's literals the same way.

`Kind`
: The kind of a resource: `"vocabulary"`, `"concept"` or `"collection"`.

`Label`
: A piece of text and its language: `text`, and `language`, which is an empty string when the text
  has no language tag.

`LabelProperty`
: Which labels to read: `"prefLabel"` or `"altLabel"`.

## Module `sphinx_skos.pages`

`GeneratedPages(vocabularies, base_uri, source_suffix, site_documents)`
: The page of every resource that can have one. `docname_for(uri)` gives a resource's document
  name, or `None` when it has no page. `write(srcdir)` writes the page sources. `clean(srcdir,
  builder, skip)` deletes the generated sources whose resource is gone and, for an HTML builder,
  their output file and copied source.

## Module `sphinx_skos.domain`

`SKOSDomain`
: The `skos` domain. It holds the three directives, and the `vocabularies` and `pages` of the
  build in progress, and the `fingerprint` of the vocabulary files the environment was last read
  with in its `data`.

## Module `sphinx_skos.directives`

`ResourceDirective`
: The base of the three directives. It takes a resource URI as its one argument. `fields(uri)`
  returns the field list shown under the page title, which a subclass extends. `field(name,
  *values)` builds one field and `label_values(labels)` the paragraphs for labels with their
  languages. `vocabularies` is the `Vocabularies` of the build in progress.

`VocabularyDirective`, `ConceptDirective`, `CollectionDirective`
: The `skos:vocabulary`, `skos:concept` and `skos:collection` directives. A concept's page shows
  its URI, preferred and alternative labels, definitions and notations. A field appears only when
  the concept has a value for it, and hidden labels are never shown. The names of the fields are
  translated through the `sphinx_skos` message catalogue.
