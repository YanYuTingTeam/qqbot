from typing import List
from botpy.message import GroupMessage
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.sendMessage import sendMessage

async def handle_command(args: List[str], message: GroupMessage) -> str:
    await sendMessage.text("临时菜单. 使用 /abw bw <玩家名> 查询战绩",message)