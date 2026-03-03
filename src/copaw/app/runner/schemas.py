from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from typing import Any, List, Optional


class RunStatus(str, Enum):
    Completed = "completed"
    Failed = "failed"
    InProgress = "in_progress"


class MessageType(str, Enum):
    MESSAGE = "message"
    RESPONSE = "response"
    FUNCTION_CALL = "function_call"
    FUNCTION_CALL_OUTPUT = "function_call_output"
    PLUGIN_CALL = "plugin_call"
    PLUGIN_CALL_OUTPUT = "plugin_call_output"
    MCP_TOOL_CALL = "mcp_tool_call"
    MCP_TOOL_CALL_OUTPUT = "mcp_tool_call_output"


class Role(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class ContentType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    FILE = "file"
    REFUSAL = "refusal"
    DATA = "data"


@dataclass
class TextContent:
    type: ContentType = ContentType.TEXT
    text: str = ""


@dataclass
class ImageContent:
    type: ContentType = ContentType.IMAGE
    image_url: str = ""


@dataclass
class VideoContent:
    type: ContentType = ContentType.VIDEO
    video_url: str = ""


@dataclass
class AudioContent:
    type: ContentType = ContentType.AUDIO
    data: str = ""
    format: Optional[str] = None


@dataclass
class FileContent:
    type: ContentType = ContentType.FILE
    file_url: str = ""
    filename: Optional[str] = None
    file_id: Optional[str] = None


@dataclass
class RefusalContent:
    type: ContentType = ContentType.REFUSAL
    refusal: str = ""


@dataclass
class DataContent:
    type: ContentType = ContentType.DATA
    data: Any = None


@dataclass
class Message:
    type: MessageType
    role: Role
    content: List[Any]

    def model_copy(self, update: Optional[dict] = None):
        if not update:
            return replace(self)
        return replace(self, **update)


@dataclass
class AgentRequest:
    session_id: str
    user_id: str
    input: List[Message]
    channel: str
    channel_meta: Optional[dict] = None

    def model_copy(self, update: Optional[dict] = None):
        if not update:
            return replace(self)
        return replace(self, **update)


@dataclass
class AgentResponse:
    output: List[Message]
    error: Optional[Exception] = None


@dataclass
class Event:
    object: str
    status: RunStatus


@dataclass
class MessageEvent(Event):
    type: MessageType
    role: Role
    content: List[Any]


@dataclass
class ResponseEvent(Event):
    output: List[Message]
    error: Optional[Exception] = None
