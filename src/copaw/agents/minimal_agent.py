import inspect
import json
import platform
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..constant import WORKING_DIR
from ..providers import get_active_llm_config
from .llm_client import LLMClient
from .skill_generator import SkillGenerator
from .skill_manager import SkillManager


def _read_memories(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def _write_memories(path: Path, content: str, mode: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if mode == "replace":
        path.write_text(content or "", encoding="utf-8")
        return "memories updated"
    if content:
        with path.open("a", encoding="utf-8") as f:
            if path.stat().st_size > 0 and not content.startswith("\n"):
                f.write("\n")
            f.write(content)
    return "memories updated"


def _serialize_content(content):
    if content is None:
        return ""
    if isinstance(content, (dict, list)):
        return json.dumps(content, ensure_ascii=False)
    return str(content)


def _build_tool_definition(name: str, func):
    try:
        sig = inspect.signature(func)
    except Exception:
        return None
    properties = {}
    required = []
    for param_name, param in sig.parameters.items():
        if param_name in {"workspace_dir", "_context"}:
            continue
        param_type = "string"
        description = "Parameter"
        if param.default != inspect.Parameter.empty:
            if isinstance(param.default, bool):
                param_type = "boolean"
            elif isinstance(param.default, int):
                param_type = "integer"
            elif isinstance(param.default, list):
                param_type = "array"
        if param_name == "tasks":
            param_type = "array"
            description = "List of tasks"
        elif param_name in {"limit", "offset"}:
            param_type = "integer"
        elif param_name == "recursive":
            param_type = "boolean"
        prop_def = {"type": param_type, "description": description}
        if param_type == "array":
            prop_def["items"] = {"type": "string"}
        properties[param_name] = prop_def
        if param.default == inspect.Parameter.empty:
            required.append(param_name)
    description = (
        func.__doc__.strip().split("\n")[0]
        if getattr(func, "__doc__", None)
        else f"Tool {name}"
    )
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        },
    }


class MinimalAgent:
    def __init__(
        self,
        name: str = "nanoCoPaw",
        sys_prompt: Optional[str] = None,
        workspace_dir: Optional[Path] = None,
        chat_storage=None,
        conversation_id: Optional[str] = None,
        max_iters: int = 8,
    ):
        self.name = name
        self.workspace_dir = Path(workspace_dir or WORKING_DIR)
        self.chat_storage = chat_storage
        self.conversation_id = conversation_id
        self.skill_manager = SkillManager(workspace_dir=self.workspace_dir)
        self.skill_generator = SkillGenerator()
        self.max_iters = max_iters

        memories_path = self.workspace_dir / "memories.md"

        def read_memories():
            return _read_memories(memories_path)

        def write_memories(content: str, mode: str = "append"):
            if mode not in {"append", "replace"}:
                return "invalid mode"
            return _write_memories(memories_path, content, mode)

        def query_history(query: str, limit: int = 5):
            if not self.chat_storage or not self.conversation_id:
                return "history storage not available"
            results = self.chat_storage.search_messages(
                self.conversation_id,
                query,
                limit=limit,
            )
            if not results:
                return "no matches"
            lines = []
            for item in results:
                content = item.get("content")
                content = _serialize_content(content)
                role = item.get("role") or "assistant"
                lines.append(f"{role}: {content}")
            return "\n".join(lines)

        def update_experience(skill_name: str, experience: str, replace: bool = False):
            ok, msg = self.skill_manager.update_skill_experience(
                skill_name,
                experience,
                replace=replace,
            )
            return msg if ok else msg

        def create_new_skill(
            code: str,
            skill_name: str | None = None,
            tool_name: str | None = None,
            description: str | None = None,
            description_cn: str | None = None,
        ):
            payload = None
            if not skill_name or not tool_name or not description or not description_cn:
                payload = self.skill_generator.refactor_code(code)
                if payload.get("error"):
                    return payload["error"]
                skill_name = skill_name or payload.get("skill_name")
                tool_name = tool_name or payload.get("tool_name")
                description = description or payload.get("description")
                description_cn = description_cn or payload.get("description_cn")
                code = payload.get("code") or code
            if not (skill_name and tool_name and description and description_cn and code):
                return "missing skill fields"
            ok, msg = self.skill_manager.create_skill(
                skill_name,
                tool_name,
                description,
                description_cn,
                code,
                ai_generated=True,
            )
            return msg if ok else msg

        def update_skill(
            skill_name: str,
            description: str | None = None,
            instructions: str | None = None,
            experience: str | None = None,
            replace_experience: bool = False,
        ):
            ok, msg = self.skill_manager.update_skill(
                skill_name,
                description=description,
                instructions=instructions,
                experience=experience,
                replace_experience=replace_experience,
            )
            return msg if ok else msg

        builtin_tools = [
            read_memories,
            write_memories,
            query_history,
            create_new_skill,
            update_experience,
            update_skill,
        ]
        self.tools = {name: fn for name, fn in self.skill_manager.tools.items()}
        for fn in builtin_tools:
            self.tools[fn.__name__] = fn

        self.tool_definitions = list(self.skill_manager.get_tool_definitions())
        for fn in builtin_tools:
            tool_def = _build_tool_definition(fn.__name__, fn)
            if tool_def:
                self.tool_definitions.append(tool_def)

        memory_text = _read_memories(memories_path)
        context_lines = [
            f"当前工作区: {self.workspace_dir}",
            f"操作系统: {platform.system()} {platform.release()}",
            f"Python 版本: {platform.python_version()}",
            f"当前日期: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "能力: 你可以使用 create_new_skill 创建新技能。",
            "策略: 需要长期记忆时使用 write_memories。",
            "策略: 需要历史检索时使用 query_history。",
            "策略: 重要经验沉淀请使用 update_experience。",
        ]
        if memory_text:
            context_lines.append("\n# Memories\n" + memory_text)
        skill_prompt = self.skill_manager.get_system_prompts()
        if skill_prompt:
            context_lines.append("\n# Skills\n" + skill_prompt)
        self.system_prompt = sys_prompt or "\n".join(context_lines)

    def _get_history_messages(self, limit: int = 10, provider_id: str = "") -> list[dict]:
        if not self.chat_storage or not self.conversation_id:
            return []
        history = self.chat_storage.get_recent_messages(
            self.conversation_id,
            limit=limit,
        )
        result = []
        for item in history:
            role = item.get("role") or "assistant"
            if role not in {"user", "assistant", "system", "tool"}:
                continue
            result.append(
                {
                    "role": role,
                    "content": _serialize_content(item.get("content")),
                }
            )
            if provider_id == "deepseek" and item.get("reasoning_content"):
                result[-1]["reasoning_content"] = item.get("reasoning_content")
        return result

    def generate(self, user_text: str) -> dict:
        cfg = get_active_llm_config()
        if not cfg:
            return {
                "content": "⚠️ 未配置 LLM。",
                "generated": [],
            }
        client = LLMClient(
            provider_id=cfg.provider_id,
            model=cfg.model,
            base_url=cfg.base_url,
            api_key=cfg.api_key,
        )
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(self._get_history_messages(provider_id=cfg.provider_id))
        messages.append({"role": "user", "content": user_text})
        generated = []
        for _ in range(self.max_iters):
            resp = client.chat(messages, tools=self.tool_definitions)
            assistant_msg = {
                "role": "assistant",
                "content": resp.get("content") or "",
            }
            if cfg.provider_id == "deepseek" and resp.get("reasoning_content"):
                assistant_msg["reasoning_content"] = resp.get("reasoning_content")
            tool_calls = resp.get("tool_calls") or []
            if tool_calls:
                assistant_msg["tool_calls"] = tool_calls
            messages.append(assistant_msg)
            generated.append(assistant_msg)
            if not tool_calls:
                return {
                    "content": assistant_msg["content"],
                    "generated": generated,
                }
            for call in tool_calls:
                func = call.get("function") or {}
                name = func.get("name") or ""
                args_str = func.get("arguments") or "{}"
                try:
                    args = json.loads(args_str)
                except json.JSONDecodeError:
                    args = {}
                tool_fn = self.tools.get(name)
                if tool_fn:
                    try:
                        result = tool_fn(**args)
                    except Exception as e:
                        result = f"Error executing {name}: {e}"
                else:
                    result = f"Tool '{name}' not found"
                tool_msg = {
                    "role": "tool",
                    "tool_call_id": call.get("id") or name,
                    "content": _serialize_content(result),
                }
                messages.append(tool_msg)
                generated.append(tool_msg)
        return {
            "content": "⚠️ 超过最大工具迭代次数。",
            "generated": generated,
        }
