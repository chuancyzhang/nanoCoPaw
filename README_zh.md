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

## 不做什么

- 不提供 Web 控制台  
- 不使用配置文件  
- 不包含定时任务、MCP、Skills 市场  

## 快速开始

```bash
pip install nanocopaw
nanocopaw
```

启动后依次配置：
1. LLM 提供商与模型  
2. 频道凭据  

配置保存到本地，与 exe 位于同一目录。


## 许可证

nanoCoPaw 采用 [Apache License 2.0](LICENSE) 开源协议。
