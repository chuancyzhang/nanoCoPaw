# nanoCoPaw

**二进制优先、频道唯一的 AI 助手。**  
启动时交互配置，只在钉钉、飞书、QQ、Discord、iMessage 五个渠道对话。

## 哲学

1. 分叉即物种：代码即真理，配置是幻象  
2. 机中之魂：无仪表盘、无日志，只由 AI 自省  
3. 技能原子化：只保留此刻有用的代码  
4. 二进制即终局：每次编译都是新的自己  

## nanoCoPaw 做什么

- 启动时提示配置 LLM 与频道凭据  
- 仅接入五个频道  
- 在频道中进行对话  
- 聊天内容自动落库（SQLite + FTS）  
- 基于 SKILL.md + impl.py 自动加载技能，支持 Claude Skill 脚本  

## 不做什么

- 不提供 Web 控制台  
- 不包含定时任务、MCP、Skills 市场  

## 快速开始

```bash
pip install nanocopaw
nanocopaw
```

启动后依次配置：
1. LLM 提供商与模型  
2. 频道凭据  

配置保存到 config.json。

## LLM 支持

- OpenAI 兼容协议（OpenAI / DeepSeek）
- Anthropic 协议

## 数据与存储

- 聊天历史：WORKING_DIR/chat_history/chat.db（SQLite + FTS）
- 记忆文件：WORKING_DIR/memories.md

## Skills

- 内置技能：src/copaw/skills
- 用户技能：WORKING_DIR/skills
- AI 技能：WORKING_DIR/ai_skills
- Claude Skill 兼容：若技能目录包含 SKILL.md + scripts/（无 impl.py），
  自动暴露脚本为 run_<script> 工具


## 许可证

nanoCoPaw 采用 [Apache License 2.0](LICENSE) 开源协议。
