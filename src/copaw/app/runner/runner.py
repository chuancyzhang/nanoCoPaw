# -*- coding: utf-8 -*-
# pylint: disable=unused-argument too-many-branches too-many-statements
import asyncio
import json
import logging
from pathlib import Path

from dotenv import load_dotenv

from .chat_storage import ChatStorage
from .query_error_dump import write_query_error_dump
from .schemas import (
    AgentRequest,
    Message,
    MessageEvent,
    MessageType,
    ResponseEvent,
    Role,
    RunStatus,
    TextContent,
)
from .session import SafeJSONSession
from ..channels.schema import DEFAULT_CHANNEL
from ...constant import WORKING_DIR
from ...agents import MinimalAgent

logger = logging.getLogger(__name__)


def _content_to_plain(content):
    if content is None:
        return None
    if isinstance(content, dict):
        return content
    if isinstance(content, (list, tuple)):
        return [_content_to_plain(c) for c in content]
    if hasattr(content, "type"):
        data = {"type": str(getattr(content, "type"))}
        for key in (
            "text",
            "refusal",
            "image_url",
            "video_url",
            "data",
            "format",
            "file_url",
            "filename",
            "file_id",
        ):
            val = getattr(content, key, None)
            if val is not None and val != "":
                data[key] = val
        if hasattr(content, "data") and isinstance(getattr(content, "data"), dict):
            data["data"] = getattr(content, "data")
        return data
    return str(content)


def _serialize_content(content):
    if content is None:
        return ""
    if isinstance(content, (dict, list, tuple)) or hasattr(content, "type"):
        return json.dumps(_content_to_plain(content), ensure_ascii=False)
    return str(content)


def _msg_to_dict(msg):
    if isinstance(msg, dict):
        return msg
    role = getattr(msg, "role", None) or "assistant"
    content = _serialize_content(getattr(msg, "content", None))
    out = {"role": role, "content": content}
    return out


def _content_parts_to_text(parts):
    if not parts:
        return ""
    texts = []
    for p in parts:
        if isinstance(p, dict):
            ptype = p.get("type")
            if ptype == "text" and p.get("text"):
                texts.append(p["text"])
            elif ptype in ("image", "audio", "video", "file"):
                texts.append(f"[{ptype}]")
            continue
        ptype = getattr(p, "type", None)
        if ptype and str(ptype).endswith("text") and getattr(p, "text", None):
            texts.append(p.text)
        elif getattr(p, "text", None):
            texts.append(p.text)
    return "\n".join([t for t in texts if t])


class AgentRunner:
    def __init__(self) -> None:
        self.framework_type = "custom"
        self.session = None
        self.chat_storage = None

    async def query_handler(
        self,
        msgs,
        request: AgentRequest = None,
        **kwargs,
    ):
        """
        Handle agent query.
        """

        agent = None

        try:
            session_id = request.session_id
            user_id = request.user_id
            channel = getattr(request, "channel", DEFAULT_CHANNEL)
            conversation_id = f"{channel}:{session_id}"

            logger.info(
                "Handle agent query:\n%s",
                json.dumps(
                    {
                        "session_id": session_id,
                        "user_id": user_id,
                        "channel": channel,
                        "msgs_len": len(msgs) if msgs else 0,
                        "msgs_str": str(msgs)[:300] + "...",
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
            )

            agent = MinimalAgent(
                workspace_dir=WORKING_DIR,
                chat_storage=self.chat_storage,
                conversation_id=conversation_id,
            )

            logger.debug(
                f"Agent Query msgs {msgs}",
            )

            await self.session.load_session_state(
                session_id=session_id,
                user_id=user_id,
                agent=agent,
            )

            if self.chat_storage and msgs:
                incoming = [_msg_to_dict(m) for m in msgs]
                self.chat_storage.append_messages(
                    conversation_id,
                    incoming,
                    meta={"channel": channel, "user_id": user_id},
                )

            user_text = ""
            if msgs:
                first = msgs[0]
                content_parts = getattr(first, "content", None) or []
                user_text = _content_parts_to_text(content_parts)
            result = agent.generate(user_text)
            generated = result.get("generated") or []
            final_text = result.get("content") or ""
            message = Message(
                type=MessageType.MESSAGE,
                role=Role.ASSISTANT,
                content=[TextContent(text=final_text)],
            )
            yield MessageEvent(
                object="message",
                status=RunStatus.Completed,
                type=message.type,
                role=message.role,
                content=message.content,
            )
            yield ResponseEvent(
                object="response",
                status=RunStatus.Completed,
                output=[message],
                error=None,
            )

        except asyncio.CancelledError:
            if agent is not None:
                await agent.interrupt()
            raise
        except Exception as e:
            debug_dump_path = write_query_error_dump(
                request=request,
                exc=e,
                locals_=locals(),
            )
            path_hint = (
                f"\n(Details:  {debug_dump_path})" if debug_dump_path else ""
            )
            logger.exception(f"Error in query handler: {e}{path_hint}")
            if debug_dump_path:
                setattr(e, "debug_dump_path", debug_dump_path)
                if hasattr(e, "add_note"):
                    e.add_note(
                        f"(Details:  {debug_dump_path})",
                    )
                suffix = f"\n(Details:  {debug_dump_path})"
                e.args = (
                    (f"{e.args[0]}{suffix}" if e.args else suffix.strip()),
                ) + e.args[1:]
            raise
        finally:
            if agent is not None:
                await self.session.save_session_state(
                    session_id=session_id,
                    user_id=user_id,
                    agent=agent,
                )
            if agent is not None and self.chat_storage:
                if "generated" in locals() and generated:
                    self.chat_storage.append_messages(
                        conversation_id,
                        generated,
                        meta={"channel": channel, "user_id": user_id},
                    )

    async def init_handler(self, *args, **kwargs):
        """
        Init handler.
        """
        # Load environment variables from .env file
        env_path = Path(__file__).resolve().parents[4] / ".env"
        if env_path.exists():
            load_dotenv(env_path)
            logger.debug(f"Loaded environment variables from {env_path}")
        else:
            logger.debug(
                f".env file not found at {env_path}, "
                "using existing environment variables",
            )

        session_dir = str(WORKING_DIR / "sessions")
        self.session = SafeJSONSession(save_dir=session_dir)
        history_dir = WORKING_DIR / "chat_history"
        self.chat_storage = ChatStorage(history_dir / "chat.db")

    async def shutdown_handler(self, *args, **kwargs):
        return None

    async def start(self):
        await self.init_handler()

    async def stop(self):
        await self.shutdown_handler()

    async def stream_query(self, request: AgentRequest):
        async for event in self.query_handler(
            msgs=request.input,
            request=request,
        ):
            yield event
