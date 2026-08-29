from typing import List
from botpy.message import GroupMessage
import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.sendMessage import sendMessage
from extension.request import get, post

async def handle_command(args: List[str], message: GroupMessage) -> str:
    import importlib
    run_path = os.getcwd()
    sys.path.insert(0, run_path)
    config_path = f"commands2.v.config"
    if config_path in sys.modules:
        del sys.modules[config_path]
    config = importlib.import_module(config_path)
    if message.author.member_openid not in config.whitelist:
        await sendMessage.text("你没有权限使用这个命令!",message)
        return
    await sendMessage.text(f"{await get(f"**HIDDEN BASE**/player/info?name={args[0]}")}", message)
    return