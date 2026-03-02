# -*- coding: utf-8 -*-
"""nanoCoPaw minimal agent module."""

__all__ = ["MinimalAgent", "create_model_and_formatter"]


def __getattr__(name: str):
    if name == "MinimalAgent":
        from .minimal_agent import MinimalAgent

        return MinimalAgent
    if name == "create_model_and_formatter":
        from .model_factory import create_model_and_formatter

        return create_model_and_formatter
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
