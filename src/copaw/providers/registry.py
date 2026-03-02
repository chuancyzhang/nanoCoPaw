# -*- coding: utf-8 -*-
"""Built-in provider definitions and registry."""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Type

from agentscope.model import ChatModelBase, OpenAIChatModel

from .models import ModelInfo, ProviderDefinition

if TYPE_CHECKING:
    from .models import ProvidersData

DEEPSEEK_MODELS: List[ModelInfo] = [
    ModelInfo(id="deepseek-reasoner", name="DeepSeek Reasoner"),
    ModelInfo(id="deepseek-chat", name="DeepSeek Chat"),
]

PROVIDER_OPENAI = ProviderDefinition(
    id="openai",
    name="OpenAI",
    default_base_url="https://api.openai.com/v1",
    api_key_prefix="sk-",
    models=[],
)

PROVIDER_ANTHROPIC = ProviderDefinition(
    id="anthropic",
    name="Anthropic",
    default_base_url="https://api.anthropic.com/v1",
    api_key_prefix="sk-ant-",
    models=[],
    chat_model="AnthropicChatModel",
)

PROVIDER_DEEPSEEK = ProviderDefinition(
    id="deepseek",
    name="DeepSeek",
    default_base_url="https://api.deepseek.com",
    api_key_prefix="sk-",
    models=DEEPSEEK_MODELS,
)

_BUILTIN_IDS: frozenset[str] = frozenset(
    [
        "openai",
        "anthropic",
        "deepseek",
    ],
)

PROVIDERS: dict[str, ProviderDefinition] = {
    PROVIDER_OPENAI.id: PROVIDER_OPENAI,
    PROVIDER_ANTHROPIC.id: PROVIDER_ANTHROPIC,
    PROVIDER_DEEPSEEK.id: PROVIDER_DEEPSEEK,
}


def get_provider(provider_id: str) -> Optional[ProviderDefinition]:
    return PROVIDERS.get(provider_id)


def get_provider_chat_model(
    provider_id: str,
    providers_data: Optional[ProvidersData] = None,
) -> str:
    """Get chat model name for a provider, checking JSON settings first.

    Args:
        provider_id: Provider identifier.
        providers_data: Optional ProvidersData. If None, will load from JSON.

    Returns:
        Chat model class name, defaults to "OpenAIChatModel".
    """
    if providers_data is None:
        from .store import load_providers_json

        providers_data = load_providers_json()

    settings = providers_data.providers.get(provider_id)
    if settings and settings.chat_model:
        return settings.chat_model

    provider_def = get_provider(provider_id)
    if provider_def:
        return provider_def.chat_model

    return "OpenAIChatModel"


def list_providers() -> List[ProviderDefinition]:
    return list(PROVIDERS.values())


def is_builtin(provider_id: str) -> bool:
    return provider_id in _BUILTIN_IDS


_CHAT_MODEL_MAP: dict[str, Type[ChatModelBase]] = {
    "OpenAIChatModel": OpenAIChatModel,
}


def get_chat_model_class(chat_model_name: str) -> Type[ChatModelBase]:
    """Get chat model class by name.

    Args:
        chat_model_name: Name of the chat model class (e.g., "OpenAIChatModel")

    Returns:
        Chat model class, defaults to OpenAIChatModel if not found.
    """
    try:
        from agentscope.model import AnthropicChatModel

        _CHAT_MODEL_MAP["AnthropicChatModel"] = AnthropicChatModel
    except Exception:
        pass
    return _CHAT_MODEL_MAP.get(chat_model_name, OpenAIChatModel)
