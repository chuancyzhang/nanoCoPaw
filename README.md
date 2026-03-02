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

## Non-goals

- No web console  
- No config files  
- No cron, no MCP, no skills marketplace  

## Quick Start

```bash
pip install nanocopaw
nanocopaw
```

The binary asks for:
1. LLM provider and model  
2. Channel credentials  

Configuration is saved locally alongside the exe.

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
