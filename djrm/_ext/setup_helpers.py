from __future__ import annotations

from djrm._ext.imports import is_expected_missing_module


def add_script_prefix_if_available(value):
    if value.startswith(("http://", "https://", "/")):
        return value
    try:
        from djrm.urls import get_script_prefix
    except ModuleNotFoundError as error:
        if not is_expected_missing_module(error, "djrm.urls"):
            raise
        return value
    return f"{get_script_prefix()}{value}"


def set_script_prefix_if_available(force_script_name):
    try:
        from djrm.urls import set_script_prefix
    except ModuleNotFoundError as error:
        if not is_expected_missing_module(error, "djrm.urls"):
            raise
        return
    set_script_prefix("/" if force_script_name is None else force_script_name)
