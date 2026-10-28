# Show a resource in a page of your own

Put a vocabulary, a concept or a collection into a page you write, such as an introduction
or a guide. Do this when a page of prose needs to show what the vocabulary says.

## Before you start

You need a site that publishes vocabulary files as described in
[Publish vocabulary files as a site](publish-vocabulary-files.md), and the URI of the resource
as it appears in the files.

## Steps

1. Open the page and write the directive where the resource should appear. Use
   `skos:vocabulary`, `skos:concept` or `skos:collection`, with the resource's URI.

   ```rst
   Dates
   =====

   Every date in the data is one of these kinds.

   .. skos:concept:: https://w3id.org/example/vocabularies/date-types/available
   ```

2. Add the page to a `toctree` if it is not in one yet.

3. Build the site and read the build output. A directive whose URI names no resource, or a
   resource of another kind, or that has no URI, prints a warning naming your page. Correct the
   URI or the directive and build again.

## The result

The page shows the resource under its own title, with the same fields and links as its
generated page. The resource still has its generated page, and only that page has
[RDF copies](../reference/rdf-copies.md). The [directives](../reference/directives.md) reference
lists the fields.
