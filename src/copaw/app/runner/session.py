# -*- coding: utf-8 -*-
"""Safe JSON session with filename sanitization for cross-platform compatibility."""
import json
import os
import re
from typing import Any


# Characters forbidden in Windows filenames
_UNSAFE_FILENAME_RE = re.compile(r'[\\/:*?"<>|]')


def sanitize_filename(name: str) -> str:
    """Replace characters that are illegal in Windows filenames with ``--``.

    >>> sanitize_filename('discord:dm:12345')
    'discord--dm--12345'
    >>> sanitize_filename('normal-name')
    'normal-name'
    """
    return _UNSAFE_FILENAME_RE.sub("--", name)


class SafeJSONSession:
    def __init__(self, save_dir: str):
        self.save_dir = save_dir

    def _get_save_path(self, session_id: str, user_id: str) -> str:
        os.makedirs(self.save_dir, exist_ok=True)
        safe_sid = sanitize_filename(session_id)
        safe_uid = sanitize_filename(user_id) if user_id else ""
        if safe_uid:
            file_path = f"{safe_uid}_{safe_sid}.json"
        else:
            file_path = f"{safe_sid}.json"
        return os.path.join(self.save_dir, file_path)

    async def load_session_state(self, session_id: str, user_id: str, agent: Any):
        path = self._get_save_path(session_id, user_id)
        if not os.path.exists(path):
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if hasattr(agent, "restore_state"):
                agent.restore_state(data)
        except Exception:
            return

    async def save_session_state(self, session_id: str, user_id: str, agent: Any):
        path = self._get_save_path(session_id, user_id)
        state = {}
        if hasattr(agent, "dump_state"):
            state = agent.dump_state() or {}
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
        except Exception:
            return
