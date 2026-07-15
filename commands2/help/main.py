from typing import List
from botpy.message import GroupMessage  
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.sendMessage import sendMessage

async def handle_command(args: List[str], message: GroupMessage) -> str:
    await sendMessage.text("小烟雨 BOT - 菜单\n" \
    " ( 括号 ) 内的参数可空\n" \
    "/yyt 《烟雨庭》相关总命令\n" \
    "/abw AerBedWars相关总命令\n" \
    "/motd (main <1..4>) 使用方法<1..4>返回所有《花雨庭》还原服信息\n" \
    "/v 《烟雨庭》志愿者总命令\n" \
    "/sd SweetDream相关总命令\n" \
    "/ncm 网易云相关总命令\n" \
    "上述命令可以直接请求，也可以 /.. help",message)