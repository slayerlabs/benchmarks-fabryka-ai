"""Packaging contract: the installed distribution and the importable package agree."""

from importlib import metadata, resources

import codesota


def test_version_matches_installed_metadata() -> None:
    assert codesota.__version__ == metadata.version("codesota")


def test_package_ships_type_marker() -> None:
    assert resources.files("codesota").joinpath("py.typed").is_file()


def test_package_declares_no_unconditional_dependencies() -> None:
    # A runtime dependency arrives with the code that needs it, in the same reviewed PR. The catalog and the
    # validator need none; the runner's evaluation stack is the `eval` extra.
    requirements = metadata.requires("codesota") or []
    assert requirements
    assert all("extra == 'eval'" in r.replace('"', "'") for r in requirements), requirements
