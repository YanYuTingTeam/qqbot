from typing import List
from botpy.message import GroupMessage
import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.sendMessage import sendMessage
from app.db_helper import get_all_members

async def handle_command(args: List[str], message: GroupMessage) -> str:
    members = get_all_members(message.group_openid)
    if not members:
        await sendMessage.text("暂无成员数据，请先使用 /refreshlist 刷新", message)
        return
    lines = []
    for m in members:
        card = m.get("group_card") or m.get("nickname", "")
        qq = m.get("qq_number", "")
        lines.append(f"{card}({qq})")
    await sendMessage.text("\n".join(lines), message)