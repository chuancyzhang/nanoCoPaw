"""Deprecated agentscope model factory (kept for backward compatibility)."""


def create_model_and_formatter(*args, **kwargs):
    raise RuntimeError("agentscope has been removed; use MinimalAgent instead.")
