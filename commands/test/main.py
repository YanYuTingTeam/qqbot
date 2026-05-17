from typing import List, Dict, Any
from botpy.message import GroupMessage
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.sendMessage import sendMessage

async def handle_command(args: List[str], message: GroupMessage) -> str:
    await sendMessage.text(f"收到群消息\n来源 {message.group_openid}\n目标 {message.id}\n事件 {message.event_id}\n请求 test@commands", message)
    return ""