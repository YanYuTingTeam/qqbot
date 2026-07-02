from typing import List
from botpy.message import GroupMessage  
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.sendMessage import sendMessage

async def handle_command(args: List[str], message: GroupMessage) -> str:
    import importlib
    run_path = os.getcwd()
    sys.path.insert(0, run_path)
    config_path = f"commands2.v.config"
    if config_path in sys.modules:
        del sys.modules[config_path]
    config = importlib.import_module(config_path)
    if message.group_openid!="8E6B4167780F0742FD595F75B568CC4F" and message.author.member_openid not in config.whitelist:
        await sendMessage.text(f"鉴权失败 ({str(message.author.member_openid)[0:4]}{str(message.group_openid)[0:4]}{str(message.author.member_openid)[-1:-5]})",message)
        return
    await sendMessage.text(f"""柠檬熟了""",message)