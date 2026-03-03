# -*- coding: utf-8 -*-
"""Built-in provider definitions and registry."""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

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




def list_providers() -> List[ProviderDefinition]:
    return list(PROVIDERS.values())


def is_builtin(provider_id: str) -> bool:
    return provider_id in _BUILTIN_IDS


