from __future__ import annotations


def add_script_prefix_if_available(value):
    if value.startswith(("http://", "https://", "/")):
        return value
    try:
        from djo.urls import get_script_prefix
    except ImportError:
        return value
    return f"{get_script_prefix()}{value}"


def set_script_prefix_if_available(force_script_name):
    try:
        from djo.urls import set_script_prefix
    except ImportError:
        return
    set_script_prefix("/" if force_script_name is None else force_script_name)
