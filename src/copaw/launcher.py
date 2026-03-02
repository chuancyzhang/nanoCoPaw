import asyncio
from getpass import getpass

from .config import load_config, set_runtime_config
from .providers import list_providers, update_provider_settings, set_active_llm
from .app.channels import ChannelManager
from .app.channels.utils import make_process_from_runner
from .app.runner import AgentRunner


def _ask_bool(prompt: str, default: bool = False) -> bool:
    suffix = "Y/n" if default else "y/N"
    while True:
        value = input(f"{prompt} [{suffix}] ").strip().lower()
        if not value:
            return default
        if value in ("y", "yes"):
            return True
        if value in ("n", "no"):
            return False


def _ask_text(prompt: str, default: str | None = None) -> str:
    if default is None:
        return input(f"{prompt}: ").strip()
    value = input(f"{prompt} [{default}]: ").strip()
    return value or default


def _configure_channels() -> None:
    config = load_config()

    if _ask_bool("启用钉钉"):
        ch = config.channels.dingtalk
        ch.enabled = True
        ch.bot_prefix = _ask_text("钉钉 Bot Prefix", ch.bot_prefix or "[BOT] ")
        ch.client_id = _ask_text("钉钉 Client ID")
        ch.client_secret = getpass("钉钉 Client Secret: ").strip()
    if _ask_bool("启用飞书"):
        ch = config.channels.feishu
        ch.enabled = True
        ch.bot_prefix = _ask_text("飞书 Bot Prefix", ch.bot_prefix or "[BOT] ")
        ch.app_id = _ask_text("飞书 App ID")
        ch.app_secret = getpass("飞书 App Secret: ").strip()
        ch.encrypt_key = _ask_text("飞书 Encrypt Key", ch.encrypt_key or "")
        ch.verification_token = _ask_text(
            "飞书 Verification Token",
            ch.verification_token or "",
        )
    if _ask_bool("启用 QQ"):
        ch = config.channels.qq
        ch.enabled = True
        ch.bot_prefix = _ask_text("QQ Bot Prefix", ch.bot_prefix or "")
        ch.app_id = _ask_text("QQ App ID")
        ch.client_secret = getpass("QQ Client Secret: ").strip()
    if _ask_bool("启用 Discord"):
        ch = config.channels.discord
        ch.enabled = True
        ch.bot_prefix = _ask_text("Discord Bot Prefix", ch.bot_prefix or "[BOT] ")
        ch.bot_token = getpass("Discord Bot Token: ").strip()
        ch.http_proxy = _ask_text("Discord HTTP Proxy", ch.http_proxy or "")
        ch.http_proxy_auth = _ask_text(
            "Discord HTTP Proxy Auth",
            ch.http_proxy_auth or "",
        )
    if _ask_bool("启用 iMessage"):
        ch = config.channels.imessage
        ch.enabled = True
        ch.bot_prefix = _ask_text("iMessage Bot Prefix", ch.bot_prefix or "[BOT] ")
        ch.db_path = _ask_text("iMessage DB Path", ch.db_path)
        ch.poll_sec = float(_ask_text("iMessage Poll Sec", str(ch.poll_sec)))

    set_runtime_config(config)


def _configure_llm() -> None:
    providers = list_providers()
    print("\n可用 LLM 提供商：")
    for idx, p in enumerate(providers, start=1):
        print(f"{idx}. {p.name} ({p.id})")
    while True:
        sel = _ask_text("选择提供商编号")
        if sel.isdigit() and 1 <= int(sel) <= len(providers):
            provider = providers[int(sel) - 1]
            break
    api_key = getpass(f"{provider.name} API Key: ").strip()
    base_url = _ask_text(f"{provider.name} Base URL", provider.default_base_url)
    update_provider_settings(provider.id, api_key=api_key, base_url=base_url)

    models = provider.models
    if not models:
        model_id = _ask_text("模型 ID")
    else:
        print("\n可用模型：")
        for idx, m in enumerate(models, start=1):
            print(f"{idx}. {m.name} ({m.id})")
        while True:
            sel = _ask_text("选择模型编号")
            if sel.isdigit() and 1 <= int(sel) <= len(models):
                model_id = models[int(sel) - 1].id
                break
    set_active_llm(provider.id, model_id)


async def _run_channels() -> None:
    runner = AgentRunner()
    await runner.start()
    config = load_config()
    channel_manager = ChannelManager.from_config(
        process=make_process_from_runner(runner),
        config=config,
        on_last_dispatch=None,
    )
    await channel_manager.start_all()
    try:
        await asyncio.Event().wait()
    finally:
        await channel_manager.stop_all()
        await runner.stop()


def main() -> None:
    print("nanoCoPaw 二进制启动配置")
    _configure_llm()
    _configure_channels()
    print("已启动，使用 Ctrl+C 退出")
    try:
        asyncio.run(_run_channels())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
