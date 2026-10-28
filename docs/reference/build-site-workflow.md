# Build site workflow

`.github/workflows/build-site.yml` is a reusable GitHub Actions workflow. A job calls it with
`uses: FAIR-DM/sphinx-skos/.github/workflows/build-site.yml@<release>` and grants it
`contents: read`, `pages: write` and `id-token: write`.

It builds the site with `sphinx-build -b dirhtml -W --keep-going`, uploads it as the
`github-pages` artifact and, unless `deploy` is false, deploys it to the repository's GitHub
Pages site in the `github-pages` environment. One deployment runs at a time.

## Inputs

| Input | Type | Default | Meaning |
|---|---|---|---|
| `docs-dir` | string | `docs` | The directory that holds the site's `conf.py`. |
| `python-version` | string | `3.13` | The Python version to build with. |
| `packages` | string | `sphinx-skos` | The packages to install, as requirement specifiers separated by spaces. Not used when `dependency-group` is set. |
| `dependency-group` | string | empty | A dependency group in the repository's `pyproject.toml`. When set, the project's dependencies and that group are installed from `uv.lock` with `uv sync --locked`. |
| `deploy` | boolean | `true` | Whether to deploy the site after building it. |

## Outputs

| Output | Meaning |
|---|---|
| `page-url` | The address of the deployed site. Empty when `deploy` is false. |

## Jobs

| Job | Runs | Permissions |
|---|---|---|
| Build site | Always | `contents: read` |
| Deploy site | When `deploy` is true | `pages: write`, `id-token: write` |
