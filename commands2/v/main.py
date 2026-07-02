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
    if message.author.member_openid not in config.whitelist:
        await sendMessage.text("你没有权限使用这个命令!",message)
        return
    await sendMessage.text("《烟雨庭》志愿者团队 - 菜单\n" \
    "使用命令请先艾特 @小烟雨\n" \
    " ( 括号 ) 内的参数可空\n" \
    "/v get 查看个人QQ信息\n" \
    "/v ban <玩家名> (--r <理由>) (--t <时间，如 7d>) 封禁玩家\n" \
    "/v unban <玩家名> 解封玩家\n" \
    "/v view <举报编号> 查看举报信息\n" \
    "/v statu 查看子服信息(仅显示有人的子服)\n" \
    "/v cmd <port> <command> 使子服批量执行命令\n" \
    "格式 port1~port2: (port1):(port2) 或 all 或 <表达式1>|<表达式2>\n" \
    "    比如 25565|25566|25569:29999\n" \
    "/v bans (--t <条数>) (--p <页码>) 查看封禁列表\n" \
    "\n" \
    "初次使用请先/v get然后等待加白!",message)