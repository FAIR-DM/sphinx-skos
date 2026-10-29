# Command

The `sphinx-skos` command, which sphinx-skos installs with the package.

## sphinx-skos build

```console
sphinx-skos build [-o OUTPUT] [-W]
```

Builds the site described by the project in the current directory, with the `dirhtml` builder.
Run it in the directory that holds `pyproject.toml`. The exit code is Sphinx's: zero when the
site was built, non-zero when the build failed.

| Option                  | Meaning                                                                         |
| ----------------------- | ------------------------------------------------------------------------------- |
| `-o OUTPUT`, `--output` | The directory to write the site to, relative to the current directory. Default `_build/site`. |
| `-W`, `--fail-on-warning` | Make a warning fail the build. Without it, a warning is reported and the build still exits zero. |

### What it builds

The command needs either a `[tool.sphinx-skos]` table in `pyproject.toml` or a `docs/conf.py`. When
it finds neither it builds nothing, prints a message that names both, and exits with code 2.

- **Source directory.** `docs/` when it exists. Otherwise the command uses `_build/source/`, which
  it creates empty, and the site holds only the generated pages and the front page.
- **No `docs/conf.py`.** The command builds with no configuration file, and loads `sphinx_skos` as
  an extension itself. Every setting comes from the [settings table](settings.md#the-pyprojecttoml-table)
  and the defaults, and the site uses Furo.
- **A `docs/conf.py`.** The command builds with it as it is. It lists `sphinx_skos` in its own
  `extensions`, like any Sphinx site, and its values win over the table's. See
  [the order settings are read in](settings.md#the-order-settings-are-read-in).
- **Doctrees.** Written to `_build/doctrees/`.

Every path is relative to the current directory, which is also where the relative patterns of
`vocabularies` are read from.
