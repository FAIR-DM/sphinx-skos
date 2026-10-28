import pytest
from sphinx.testing.util import SphinxTestApp


class TestExtension:
    @pytest.mark.sphinx("dirhtml", testroot="basic")
    def test_a_site_listing_the_extension_builds_without_warnings(
        self, app: SphinxTestApp
    ) -> None:
        app.build()

        assert "sphinx_skos" in app.extensions
        assert app.warning.getvalue() == ""
