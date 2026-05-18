from __future__ import annotations

import importlib.metadata

import nsidc.icesat2gis as m


def test_version() -> None:
    assert importlib.metadata.version("nsidc-icesat2gis") == m.__version__
