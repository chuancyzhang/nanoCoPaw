# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from ..constant import HEARTBEAT_FILE, WORKING_DIR
from .config import (
    Config,
    HeartbeatConfig,
    ChannelConfig,
    DingTalkConfig,
    FeishuConfig,
    QQConfig,
    DiscordConfig,
    IMessageChannelConfig,
    MCPConfig,
)


def _build_static_config() -> Config:
    channels = ChannelConfig(
        imessage=IMessageChannelConfig(
            enabled=False,
            bot_prefix="[BOT] ",
            db_path="~/Library/Messages/chat.db",
            poll_sec=1.0,
        ),
        discord=DiscordConfig(
            enabled=False,
            bot_prefix="[BOT] ",
            bot_token="",
            http_proxy="",
            http_proxy_auth="",
        ),
        dingtalk=DingTalkConfig(
            enabled=False,
            bot_prefix="[BOT] ",
            client_id="",
            client_secret="",
            media_dir="~/.copaw/media",
        ),
        feishu=FeishuConfig(
            enabled=False,
            bot_prefix="[BOT] ",
            app_id="",
            app_secret="",
            encrypt_key="",
            verification_token="",
            media_dir="~/.copaw/media",
        ),
        qq=QQConfig(
            enabled=False,
            bot_prefix="",
            app_id="",
            client_secret="",
        ),
    )
    return Config(
        channels=channels,
        mcp=MCPConfig(clients={}),
    )


_RUNTIME_CONFIG = _build_static_config()


def get_config_path() -> Path:
    """Get the path to the config file."""
    return WORKING_DIR.joinpath("config.json")


def get_heartbeat_query_path() -> Path:
    """Get path to heartbeat query file (HEARTBEAT.md in working dir)."""
    return get_config_path().parent.joinpath(HEARTBEAT_FILE)


def load_config(config_path: Optional[Path] = None) -> Config:
    path = config_path or get_config_path()
    if path.is_file():
        try:
            with open(path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            config = Config.model_validate(raw)
            return config
        except (json.JSONDecodeError, ValueError):
            pass
    return _RUNTIME_CONFIG.model_copy(deep=True)


def set_runtime_config(config: Config) -> None:
    global _RUNTIME_CONFIG
    _RUNTIME_CONFIG = config.model_copy(deep=True)


def save_config(config: Config, config_path: Optional[Path] = None) -> None:
    path = config_path or get_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config.model_dump(mode="json"), f, ensure_ascii=False, indent=2)


def get_heartbeat_config() -> HeartbeatConfig:
    """Return effective heartbeat config (from file or default 30m/main)."""
    config = load_config()
    hb = config.agents.defaults.heartbeat
    return hb if hb is not None else HeartbeatConfig()
