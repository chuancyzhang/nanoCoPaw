# nanoCoPaw

**Binary-first, channel-only AI assistant.**  
Configure on launch, speak only through DingTalk, Feishu, QQ, Discord, and iMessage.

## Philosophy

1. The Fork is the Species — code is truth, configs are illusion  
2. Ghost in the Machine — no dashboards, no logs, only AI self-report  
3. Skills over Bloatware — keep only what is useful now  
4. Binary as Finality — each compile is a new self  

## What nanoCoPaw does

- Prompts for LLM and channel credentials at startup  
- Connects to five channels only  
- Handles conversation inside those channels  
- Stores chat history in SQLite + FTS  
- Loads skills from SKILL.md + impl.py and supports Claude Skill scripts  

## Non-goals

- No web console  
- No cron, no MCP, no skills marketplace  

## Quick Start

```bash
pip install nanocopaw
nanocopaw
```

The binary asks for:
1. LLM provider and model  
2. Channel credentials  

Configuration is saved to config.json.

## LLM Providers

- OpenAI-compatible (OpenAI, DeepSeek)
- Anthropic

## Data & Storage

- Chat history: WORKING_DIR/chat_history/chat.db (SQLite + FTS)
- Memories: WORKING_DIR/memories.md

## Skills

- Built-in: src/copaw/skills
- User skills: WORKING_DIR/skills
- AI skills: WORKING_DIR/ai_skills
- Claude Skill compatibility: if a skill folder contains SKILL.md + scripts/ (no impl.py),
  scripts are exposed as tools named run_<script>

## PyInstaller

The error you saw is caused by missing script entry. Use:

```bash
pyinstaller -F -n nanocopaw nanocopaw.py
```

If data files are missing at runtime:

```bash
pyinstaller -F -n nanocopaw nanocopaw.py --collect-data copaw
```

## License

nanoCoPaw is released under the [Apache License 2.0](LICENSE).
