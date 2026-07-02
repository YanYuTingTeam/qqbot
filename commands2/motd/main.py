from typing import List
from botpy.message import GroupMessage
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.motdall import todo
from app.sendMessage import sendMessage

async def handle_command(args: List[str], message: GroupMessage) -> str:
    ms = 1
    try:
        if len(args) >= 1:
            ms = int(args[0])
    except Exception:
        await sendMessage.text(f"方法参数非法", message, 2)
        return
    if ms > 4 or ms < 1:
        await sendMessage.text(f"方法{ms}不存在", message, 2)
        return
    await sendMessage.text(f"正在使用方法{ms}请求数据, 请稍等 (大约10秒)", message, 2)
    img_path = await todo(ms)
    await sendMessage.image(img_path, message, 3)
    if os.path.exists(img_path):
        os.remove(img_path)
    return ""