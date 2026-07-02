from typing import List
from botpy.message import GroupMessage  
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.sendMessage import sendMessage

async def handle_command(args: List[str], message: GroupMessage) -> str:
    await sendMessage.text("小烟雨 BOT - SD菜单\n" \
    "使用命令请先艾特 @小烟雨\n" \
    " ( 括号 ) 内的参数可空\n" \
    "/sd online - 查看SweetDream在线人数",message)