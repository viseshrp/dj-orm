from __future__ import annotations


def set_script_prefix_if_available(force_script_name):
    try:
        from djo.urls import set_script_prefix
    except ImportError:
        return

    set_script_prefix("/" if force_script_name is None else force_script_name)
