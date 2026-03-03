import json

from ..providers import get_active_llm_config

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except Exception:
    OPENAI_AVAILABLE = False


class SkillGenerator:
    def __init__(self):
        cfg = get_active_llm_config()
        self.api_key = cfg.api_key if cfg else ""
        self.base_url = cfg.base_url if cfg else "https://api.deepseek.com"

    def refactor_code(self, code: str) -> dict:
        if not self.api_key or not OPENAI_AVAILABLE:
            return {"error": "LLM not available or API key missing"}
        system_prompt = (
            "You are a Python Expert and Skill Creator.\n"
            "Refactor the provided Python code snippet into a standalone, reusable function.\n"
            "Requirements:\n"
            "1. Extract hardcoded values into function arguments.\n"
            "2. Output must be a valid Python function.\n"
            "3. Provide snake_case tool_name and kebab-case skill_name.\n"
            "4. Provide concise English and Chinese descriptions.\n"
            "Return ONLY a JSON object:\n"
            "{\n"
            '  "skill_name": "example-skill-name",\n'
            '  "tool_name": "example_function_name",\n'
            '  "description": "English description.",\n'
            '  "description_cn": "中文描述。",\n'
            '  "code": "def example_function_name(...):\\n    ..."\n'
            "}\n"
        )
        user_prompt = f"Refactor this code into a reusable skill:\n\n```python\n{code}\n```"
        try:
            client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
            )
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            return {"error": str(e)}

    def generate_skill_from_repo(
        self,
        repo_context: str,
        user_requirement: str,
    ) -> dict:
        if not self.api_key or not OPENAI_AVAILABLE:
            return {"error": "LLM not available or API key missing"}
        system_prompt = (
            "You are an Expert Python Developer and AI Skill Creator.\n"
            "Create a Python wrapper skill for a repository based on analysis context.\n"
            "Strategies:\n"
            "1. If CLI tool, use subprocess to call it.\n"
            "2. If library, import and call its API.\n"
            "Include dependency install check if missing.\n"
            "Return ONLY a JSON object:\n"
            "{\n"
            '  "skill_name": "repo-name-wrapper",\n'
            '  "tool_name": "tool_function_name",\n'
            '  "description": "English description.",\n'
            '  "description_cn": "中文描述。",\n'
            '  "code": "def tool_function_name(...): ..."\n'
            "}\n"
        )
        user_prompt = (
            f"User Requirement: {user_requirement}\n\nRepository Context:\n{repo_context}"
        )
        try:
            client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
            )
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            return {"error": str(e)}
