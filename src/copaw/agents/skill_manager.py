import inspect
import importlib.util
import os
import re
import shlex
import subprocess
import sys
import time
from pathlib import Path


class SkillManager:
    def __init__(self, workspace_dir: str | Path | None = None):
        self.workspace_dir = (
            str(workspace_dir) if workspace_dir is not None else os.getcwd()
        )
        self._init_skill_dirs()
        self.tools = {}
        self.tool_definitions = []
        self.tool_to_skill_map = {}
        self.skill_prompts_brief = []
        self.skill_prompts_full = {}
        self.loaded_skills_meta = {}
        self.last_load_time = 0.0
        self.load_skills()

    def _init_skill_dirs(self):
        self.builtin_skills_dir = str(
            Path(__file__).resolve().parents[1] / "skills"
        )
        self.user_skills_dir = str(Path(self.workspace_dir) / "skills")
        self.user_ai_skills_dir = str(Path(self.workspace_dir) / "ai_skills")
        self.skills_dirs = [
            self.builtin_skills_dir,
            self.user_skills_dir,
            self.user_ai_skills_dir,
        ]

    def set_workspace_dir(self, workspace_dir: str | Path):
        self.workspace_dir = str(workspace_dir)
        self._init_skill_dirs()

    def check_for_updates(self):
        try:
            for skills_dir in self.skills_dirs:
                if not os.path.exists(skills_dir):
                    continue
                for skill_name in os.listdir(skills_dir):
                    if skill_name.startswith("."):
                        continue
                    skill_path = os.path.join(skills_dir, skill_name)
                    if not os.path.isdir(skill_path):
                        continue
                    md_path = os.path.join(skill_path, "SKILL.md")
                    if os.path.exists(md_path):
                        if os.path.getmtime(md_path) > self.last_load_time:
                            return True
                    impl_path = os.path.join(skill_path, "impl.py")
                    if os.path.exists(impl_path):
                        if os.path.getmtime(impl_path) > self.last_load_time:
                            return True
                    scripts_dir = os.path.join(skill_path, "scripts")
                    if os.path.isdir(scripts_dir):
                        if os.path.getmtime(scripts_dir) > self.last_load_time:
                            return True
        except Exception:
            return False
        return False

    def load_skills(self):
        self.tools = {}
        self.tool_definitions = []
        self.tool_to_skill_map = {}
        self.skill_prompts_brief = []
        self.skill_prompts_full = {}
        self.loaded_skills_meta = {}
        try:
            self.last_load_time = os.path.getmtime(self.workspace_dir)
        except Exception:
            self.last_load_time = time.time()
        for skills_dir in self.skills_dirs:
            if not os.path.exists(skills_dir):
                continue
            for skill_name in os.listdir(skills_dir):
                if skill_name.startswith(".") or skill_name == "__pycache__":
                    continue
                skill_path = os.path.join(skills_dir, skill_name)
                if not os.path.isdir(skill_path):
                    continue
                md_path = os.path.join(skill_path, "SKILL.md")
                if os.path.exists(md_path):
                    self._parse_skill_md(md_path, skill_name)
                impl_path = os.path.join(skill_path, "impl.py")
                if os.path.exists(impl_path):
                    self._load_implementation(skill_name, impl_path)
                else:
                    scripts_dir = os.path.join(skill_path, "scripts")
                    if os.path.isdir(scripts_dir):
                        self._load_claude_scripts(skill_name, skill_path, scripts_dir)

    def _parse_skill_md_content(self, md_path):
        try:
            with open(md_path, "r", encoding="utf-8") as f:
                content = f.read()
            match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", content, re.DOTALL)
            if match:
                frontmatter_raw = match.group(1)
                body = match.group(2).strip()
                meta = {}
                for line in frontmatter_raw.split("\n"):
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if ":" in line:
                        key, val = line.split(":", 1)
                        key = key.strip()
                        val = val.strip()
                        if val.startswith("[") and val.endswith("]"):
                            inner = val[1:-1]
                            if not inner.strip():
                                val = []
                            else:
                                val = [
                                    v.strip().strip("\"'")
                                    for v in inner.split(",")
                                ]
                        else:
                            val = val.strip("\"'")
                        meta[key] = val
                return meta, body
            return {}, content
        except Exception:
            return {}, ""

    def _parse_skill_md(self, md_path, skill_name):
        meta, body = self._parse_skill_md_content(md_path)
        if meta:
            self.loaded_skills_meta[skill_name] = meta
        prompt_content = body
        if meta and "experience" in meta:
            exp_list = meta["experience"]
            if isinstance(exp_list, list) and exp_list:
                exp_text = "\n\n### 🧠 Learned Experience\n"
                exp_text += "The following lessons were learned:\n"
                for exp in exp_list:
                    exp_text += f"- {exp}\n"
                prompt_content += exp_text
        if prompt_content:
            self.skill_prompts_full[skill_name] = prompt_content
        brief_lines = []
        brief_lines.append(f"[Skill] {meta.get('name') or skill_name}")
        if meta.get("description"):
            brief_lines.append(f"description: {meta.get('description')}")
        if meta.get("description_cn"):
            brief_lines.append(f"description_cn: {meta.get('description_cn')}")
        if meta.get("license"):
            brief_lines.append(f"license: {meta.get('license')}")
        if meta.get("security_level"):
            brief_lines.append(f"security_level: {meta.get('security_level')}")
        allowed_tools = meta.get("allowed-tools")
        if isinstance(allowed_tools, list):
            brief_lines.append(f"allowed-tools: {', '.join(allowed_tools)}")
        elif allowed_tools:
            brief_lines.append(f"allowed-tools: {allowed_tools}")
        if brief_lines:
            self.skill_prompts_brief.append("\n".join(brief_lines))

    def _quote(self, text: str) -> str:
        return "\"" + text.replace("\"", "\\\"") + "\""

    def _load_implementation(self, skill_name, impl_path):
        try:
            spec = importlib.util.spec_from_file_location(
                f"skills.{skill_name}",
                impl_path,
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            for name, func in inspect.getmembers(module, inspect.isfunction):
                if name.startswith("_"):
                    continue
                self.tools[name] = func
                self.tool_to_skill_map[name] = skill_name
                tool_def = self._build_tool_definition(name, func)
                if tool_def:
                    self.tool_definitions.append(tool_def)
        except Exception:
            return

    def _load_claude_scripts(self, skill_name, skill_path, scripts_dir):
        for file in os.listdir(scripts_dir):
            if file.startswith(".") or file.startswith("__"):
                continue
            file_path = os.path.join(scripts_dir, file)
            if not os.path.isfile(file_path):
                continue
            base_name = os.path.splitext(file)[0]
            tool_name = f"run_{base_name.replace('-', '_')}"

            def _run_script(args: str = "", _file=file):
                script_path = os.path.join(scripts_dir, _file)
                cmd = []
                if _file.endswith(".py"):
                    cmd = [sys.executable, script_path]
                elif _file.endswith(".sh"):
                    cmd = ["bash", script_path]
                elif _file.endswith(".js"):
                    cmd = ["node", script_path]
                else:
                    cmd = [script_path]
                if args:
                    cmd.extend(shlex.split(args))
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=skill_path,
                )
                output = result.stdout or ""
                if result.stderr:
                    output += "\n[STDERR]\n" + result.stderr
                return output

            _run_script.__name__ = tool_name
            _run_script.__doc__ = (
                f"Executes the {_file} script from the Claude skill."
            )
            self.tools[tool_name] = _run_script
            self.tool_to_skill_map[tool_name] = skill_name
            tool_def = self._build_tool_definition(tool_name, _run_script)
            if tool_def:
                self.tool_definitions.append(tool_def)

    def _build_tool_definition(self, name, func):
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
        return {
            "type": "function",
            "function": {
                "name": name,
                "description": func.__doc__.strip().split("\n")[0]
                if func.__doc__
                else f"Tool {name}",
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }

    def get_skill_of_tool(self, tool_name):
        return self.tool_to_skill_map.get(tool_name)

    def get_tool_definitions(self):
        return list(self.tool_definitions)

    def get_system_prompts(self):
        return "\n\n".join(self.skill_prompts_brief)

    def get_full_skill_prompt(self, skill_name):
        return self.skill_prompts_full.get(skill_name)

    def get_agent_tools(self):
        return list(self.tools.values())

    def call_tool(self, name, args, context=None):
        if name not in self.tools:
            return f"Error: Tool '{name}' not found."
        func = self.tools[name]
        try:
            sig = inspect.signature(func)
        except Exception:
            return func(**args)
        if "workspace_dir" in sig.parameters:
            args["workspace_dir"] = self.workspace_dir
        if context and "_context" in sig.parameters:
            args["_context"] = context
        try:
            return func(**args)
        except Exception as e:
            return f"Error executing {name}: {str(e)}"

    def update_skill_experience(self, skill_name, experience_text, replace=False):
        return self.update_skill(skill_name, experience=experience_text, replace_experience=replace)

    def update_skill(
        self,
        skill_name,
        description=None,
        instructions=None,
        experience=None,
        replace_experience=False,
    ):
        skill_path = None
        for s_dir in self.skills_dirs:
            p = os.path.join(s_dir, skill_name)
            if os.path.isdir(p):
                skill_path = p
                break
        if not skill_path:
            return False, f"Skill '{skill_name}' not found."
        md_path = os.path.join(skill_path, "SKILL.md")
        if not os.path.exists(md_path):
            return False, f"SKILL.md not found for '{skill_name}'."
        try:
            with open(md_path, "r", encoding="utf-8") as f:
                content = f.read()
            match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", content, re.DOTALL)
            if not match:
                return False, "Invalid SKILL.md format."
            frontmatter_raw = match.group(1)
            body = match.group(2)
            lines = frontmatter_raw.split("\n")
            new_lines = []
            desc_updated = False
            exp_updated = False
            for line in lines:
                if description and line.strip().startswith("description:"):
                    new_lines.append(f"description: {description}")
                    desc_updated = True
                elif experience and line.strip().startswith("experience:"):
                    if replace_experience:
                        if isinstance(experience, list):
                            quoted_exp = [self._quote(e) for e in experience]
                            new_lines.append(
                                f"experience: [{', '.join(quoted_exp)}]"
                            )
                        else:
                            quoted_exp = self._quote(experience)
                            new_lines.append(f"experience: [{quoted_exp}]")
                    else:
                        key, val = line.split(":", 1)
                        val = val.strip()
                        current_exp = []
                        if val.startswith("[") and val.endswith("]"):
                            inner = val[1:-1]
                            if inner.strip():
                                current_exp = [
                                    v.strip().strip("\"'")
                                    for v in inner.split(",")
                                ]
                        to_add = (
                            experience if isinstance(experience, list) else [experience]
                        )
                        for item in to_add:
                            if item not in current_exp:
                                current_exp.append(item)
                        quoted_exp = [self._quote(e) for e in current_exp]
                        new_lines.append(
                            f"experience: [{', '.join(quoted_exp)}]"
                        )
                    exp_updated = True
                else:
                    new_lines.append(line)
            if description and not desc_updated:
                new_lines.insert(0, f"description: {description}")
            if experience and not exp_updated:
                if isinstance(experience, list):
                    quoted_exp = [self._quote(e) for e in experience]
                    new_lines.append(f"experience: [{', '.join(quoted_exp)}]")
                else:
                    quoted_exp = self._quote(experience)
                    new_lines.append(f"experience: [{quoted_exp}]")
            new_frontmatter = "\n".join(new_lines)
            new_body = instructions if instructions is not None else body
            new_content = f"---\n{new_frontmatter}\n---\n{new_body}"
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            return True, f"Skill '{skill_name}' updated."
        except Exception as e:
            return False, f"Failed to update skill: {e}"

    def create_skill(
        self,
        skill_name,
        tool_name,
        description,
        description_cn,
        code,
        ai_generated=True,
    ):
        base_dir = (
            self.user_ai_skills_dir if ai_generated else self.user_skills_dir
        )
        os.makedirs(base_dir, exist_ok=True)
        skill_path = os.path.join(base_dir, skill_name)
        if os.path.exists(skill_path):
            return False, f"Skill '{skill_name}' already exists."
        os.makedirs(skill_path, exist_ok=True)
        md_path = os.path.join(skill_path, "SKILL.md")
        impl_path = os.path.join(skill_path, "impl.py")
        frontmatter_lines = [
            "---",
            f"name: {skill_name}",
            f"description: {description}",
            f"description_cn: {description_cn}",
            f"tool_name: {tool_name}",
            "experience: []",
            "---",
        ]
        content = "\n".join(frontmatter_lines) + "\n\n" + (code or "")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(content)
        with open(impl_path, "w", encoding="utf-8") as f:
            f.write(code or "")
        self.load_skills()
        return True, f"Skill '{skill_name}' created."
