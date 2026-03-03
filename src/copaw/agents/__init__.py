# -*- coding: utf-8 -*-
"""nanoCoPaw agent module."""

__all__ = ["MinimalAgent"]


def __getattr__(name: str):
    if name == "MinimalAgent":
        from .minimal_agent import MinimalAgent

        return MinimalAgent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
