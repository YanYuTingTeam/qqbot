from typing import List
from botpy.message import GroupMessage
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.motdall import todo
from app.sendMessage import sendMessage

async def handle_command(args: List[str], message: GroupMessage) -> str:
    ms = 3
    await sendMessage.text(f"正在使用方法{ms}请求数据, 请稍等 (大约10秒)", message, 2)
    img_path = await todo(ms)
    await sendMessage.image(img_path, message, 3)
    if os.path.exists(img_path):
        os.remove(img_path)
    return ""