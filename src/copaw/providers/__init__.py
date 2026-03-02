# -*- coding: utf-8 -*-
"""Provider management — models, registry + persistent store."""

from .models import (
    ActiveModelsInfo,
    ModelInfo,
    ModelSlotConfig,
    ProviderDefinition,
    ProviderInfo,
    ProviderSettings,
    ProvidersData,
    ResolvedModelConfig,
)
from .registry import (
    PROVIDERS,
    get_chat_model_class,
    get_provider,
    get_provider_chat_model,
    list_providers,
)
from .store import (
    get_active_llm_config,
    load_providers_json,
    mask_api_key,
    save_providers_json,
    set_active_llm,
    update_provider_settings,
)

__all__ = [
    "ActiveModelsInfo",
    "ModelInfo",
    "ModelSlotConfig",
    "ProviderDefinition",
    "ProviderInfo",
    "ProviderSettings",
    "ProvidersData",
    "ResolvedModelConfig",
    "PROVIDERS",
    "get_chat_model_class",
    "get_provider",
    "get_provider_chat_model",
    "list_providers",
    "get_active_llm_config",
    "load_providers_json",
    "mask_api_key",
    "save_providers_json",
    "set_active_llm",
    "update_provider_settings",
]
