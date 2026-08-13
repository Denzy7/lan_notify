# Overwritten by the release workflow just before building, using the
# exact tag being released (see .github/workflows/release.yml), so the
# compiled exe always reports the tag it was actually built from.
#
# This default is what a plain source checkout / `python -m client.main`
# reports - i.e. "not an official release build".
__version__ = "v0.0.2"
