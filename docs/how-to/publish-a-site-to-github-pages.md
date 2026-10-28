# Publish a site to GitHub Pages

Build the site and deploy it to GitHub Pages from the repository that holds the vocabulary files,
on every push to its default branch. Do this when the site builds on your own machine and should
be published at the repository's Pages address.

## Before you start

You need a site that builds as described in
[Publish vocabulary files as a site](publish-vocabulary-files.md), in a GitHub repository. In the
repository's **Settings → Pages**, set **Source** to **GitHub Actions**.

## Steps

1. Add a workflow file, such as `.github/workflows/site.yml`, with a job that calls the workflow
   sphinx-skos ships. Pin it to a release.

   ```yaml
   name: Site

   on:
     push:
       branches: [main]
     pull_request:

   jobs:
     site:
       uses: FAIR-DM/sphinx-skos/.github/workflows/build-site.yml@v0.4.0
       permissions:
         contents: read
         pages: write
         id-token: write
       with:
         packages: sphinx-skos==0.4.0 furo
         deploy: ${{ github.event_name == 'push' }}
   ```

   `packages` lists everything the build needs besides Sphinx: sphinx-skos, the theme and any
   other extension in `conf.py`. `deploy` builds pull requests without deploying them. The job
   grants all three permissions even when it does not deploy, or the run does not start.

2. If the repository manages its dependencies with uv and keeps the site's in a dependency
   group, name the group instead of `packages`. The group and the project's own dependencies are
   installed from `uv.lock`, and the run fails when `uv.lock` is out of date.

   ```yaml
       with:
         dependency-group: docs
         deploy: ${{ github.event_name == 'push' }}
   ```

3. If `conf.py` is not in `docs`, name its directory with `docs-dir`.

4. Push the workflow to the default branch. The run builds the site with warnings treated as
   errors and deploys it. The deployment's address is on the run's summary page, under
   **Deploy site**.

## Run steps of your own after the build

The built site is uploaded as the `github-pages` artifact. A job that `needs` the site job can
download it, for example to check its links.

```yaml
  check:
    needs: site
    runs-on: ubuntu-latest
    steps:
      - uses: actions/download-artifact@v8
        with:
          name: github-pages
      - run: tar -xf artifact.tar
```

To deploy the site somewhere else, set `deploy: false` and deploy the artifact from a job of your
own.

## The result

Every push to the default branch publishes the site at the repository's Pages address. A build
warning fails the run, and nothing is deployed. Every input is listed in
[Build site workflow](../reference/build-site-workflow.md).
