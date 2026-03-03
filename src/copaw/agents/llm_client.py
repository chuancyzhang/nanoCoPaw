from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional


class LLMClient:
    def __init__(
        self,
        provider_id: str,
        model: str,
        base_url: str,
        api_key: str,
        timeout: int = 60,
    ):
        self.provider_id = provider_id
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def chat(self, messages: List[dict], tools: Optional[List[dict]] = None) -> dict:
        if self.provider_id == "anthropic":
            return self._chat_anthropic(messages, tools)
        return self._chat_openai(messages, tools)

    def _chat_openai(
        self,
        messages: List[dict],
        tools: Optional[List[dict]] = None,
    ) -> dict:
        url = f"{self.base_url}/chat/completions"
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        resp = self._post_json(url, payload, headers)
        choice = (resp.get("choices") or [{}])[0]
        message = choice.get("message") or {}
        content = message.get("content") or ""
        tool_calls = message.get("tool_calls") or []
        reasoning_content = message.get("reasoning_content")
        return {
            "content": content,
            "tool_calls": tool_calls,
            "reasoning_content": reasoning_content,
            "raw": resp,
        }

    def _chat_anthropic(
        self,
        messages: List[dict],
        tools: Optional[List[dict]] = None,
    ) -> dict:
        url = f"{self.base_url}/messages"
        system_text = ""
        anthro_messages: List[dict] = []
        for msg in messages:
            role = msg.get("role")
            if role == "system":
                system_text = msg.get("content") or ""
                continue
            anthro_messages.append(self._to_anthropic_message(msg))
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": anthro_messages,
            "max_tokens": 1024,
        }
        if system_text:
            payload["system"] = system_text
        if tools:
            payload["tools"] = [
                {
                    "name": t["function"]["name"],
                    "description": t["function"]["description"],
                    "input_schema": t["function"]["parameters"],
                }
                for t in tools
            ]
        headers = {
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }
        if self.api_key:
            headers["x-api-key"] = self.api_key
        resp = self._post_json(url, payload, headers)
        content_blocks = resp.get("content") or []
        content = ""
        tool_calls = []
        for block in content_blocks:
            if block.get("type") == "text":
                content += block.get("text") or ""
            elif block.get("type") == "tool_use":
                tool_calls.append(
                    {
                        "id": block.get("id"),
                        "type": "function",
                        "function": {
                            "name": block.get("name"),
                            "arguments": json.dumps(block.get("input") or {}),
                        },
                    }
                )
        return {"content": content, "tool_calls": tool_calls, "raw": resp}

    def _to_anthropic_message(self, msg: dict) -> dict:
        role = msg.get("role")
        content = msg.get("content") or ""
        if role == "tool":
            tool_call_id = msg.get("tool_call_id") or ""
            return {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_call_id,
                        "content": content,
                    }
                ],
            }
        tool_calls = msg.get("tool_calls") or []
        if role == "assistant" and tool_calls:
            blocks = []
            if content:
                blocks.append({"type": "text", "text": content})
            for call in tool_calls:
                func = call.get("function") or {}
                name = func.get("name")
                args = func.get("arguments") or "{}"
                try:
                    args_obj = json.loads(args)
                except json.JSONDecodeError:
                    args_obj = {}
                blocks.append(
                    {
                        "type": "tool_use",
                        "id": call.get("id") or "",
                        "name": name,
                        "input": args_obj,
                    }
                )
            return {"role": "assistant", "content": blocks}
        return {"role": role, "content": content}

    def _post_json(self, url: str, payload: dict, headers: dict) -> dict:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
                return json.loads(raw)
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {e.code}: {raw}") from e
