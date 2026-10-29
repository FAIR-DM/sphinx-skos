from pathlib import Path

from babel.messages.mofile import write_mo
from babel.messages.pofile import read_po

extensions = ["sphinx_skos"]
language = "de"
skos_vocabularies = ["vocabularies/*.ttl"]
skos_base_uri = "https://example.org/vocab/"


def setup(app):
    here = Path(__file__).parent
    with (here / "locale/de/LC_MESSAGES/sphinx_skos.po").open("rb") as po:
        catalog = read_po(po, locale="de")
    with (here / "locale/de/LC_MESSAGES/sphinx_skos.mo").open("wb") as mo:
        write_mo(mo, catalog)
    app.add_message_catalog("sphinx_skos", str(here / "locale"))
html_theme = "basic"
