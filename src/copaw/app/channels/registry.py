# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .base import BaseChannel
from .dingtalk import DingTalkChannel
from .discord_ import DiscordChannel
from .feishu import FeishuChannel
from .imessage import IMessageChannel
from .qq import QQChannel

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

_BUILTIN: dict[str, type[BaseChannel]] = {
    "imessage": IMessageChannel,
    "discord": DiscordChannel,
    "dingtalk": DingTalkChannel,
    "feishu": FeishuChannel,
    "qq": QQChannel,
}


BUILTIN_CHANNEL_KEYS = frozenset(_BUILTIN.keys())


def get_channel_registry() -> dict[str, type[BaseChannel]]:
    """Built-in channel classes."""
    return dict(_BUILTIN)
