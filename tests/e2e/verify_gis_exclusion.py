from importlib.util import find_spec


def main() -> int:
    assert find_spec("djrm.contrib.gis") is None
    try:
        import djrm.contrib.gis  # type: ignore[import-not-found]  # noqa: F401
    except ModuleNotFoundError as error:
        assert error.name == "djrm.contrib.gis"
    else:  # pragma: no cover - this package is intentionally excluded.
        raise AssertionError("djrm.contrib.gis unexpectedly imported")
    print("DJRM_GIS_EXCLUSION_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
