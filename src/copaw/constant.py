# -*- coding: utf-8 -*-
import os
import sys
from pathlib import Path

def _resolve_working_dir() -> Path:
    base = Path(sys.executable) if sys.executable else Path.cwd()
    return base.resolve().parent


WORKING_DIR = _resolve_working_dir()

HEARTBEAT_FILE = os.environ.get("COPAW_HEARTBEAT_FILE", "HEARTBEAT.md")
HEARTBEAT_DEFAULT_EVERY = "30m"
HEARTBEAT_DEFAULT_TARGET = "main"
HEARTBEAT_TARGET_LAST = "last"

# Env key for app log level (used by CLI and app load for reload child).
LOG_LEVEL_ENV = "COPAW_LOG_LEVEL"

# Skills directories
# Active skills directory (activated skills that agents use)
ACTIVE_SKILLS_DIR = WORKING_DIR / "active_skills"
# Customized skills directory (user-created skills)
CUSTOMIZED_SKILLS_DIR = WORKING_DIR / "customized_skills"

# Memory directory
MEMORY_DIR = WORKING_DIR / "memory"

# Custom channel modules (installed via `copaw channels install`); manager
# loads BaseChannel subclasses from here.
CUSTOM_CHANNELS_DIR = WORKING_DIR / "custom_channels"

# Memory compaction configuration
MEMORY_COMPACT_KEEP_RECENT = int(
    os.environ.get("COPAW_MEMORY_COMPACT_KEEP_RECENT", "3"),
)

MEMORY_COMPACT_RATIO = float(
    os.environ.get("COPAW_MEMORY_COMPACT_RATIO", "0.7"),
)

ALLOWED_CHANNELS = ("dingtalk", "feishu", "qq", "discord", "imessage")


def get_available_channels() -> tuple[str, ...]:
    return ALLOWED_CHANNELS
