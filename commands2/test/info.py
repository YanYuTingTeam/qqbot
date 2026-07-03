from typing import List
from botpy.message import GroupMessage
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.sendMessage import sendMessage
from app.db_helper import get_user_info

async def handle_command(args: List[str], message: GroupMessage) -> str:
    info = get_user_info(message.group_openid, message.author.member_openid)
    if not info:
        await sendMessage.text("未找到你的信息，请先使用 /refreshlist 刷新成员列表", message)
        return
    card = info.get("group_card") or info.get("nickname", "")
    qq = info.get("qq_number", "")
    nick = info.get("nickname", "")
    avatar = info.get("avatar_url", "")
    role = info.get("role", 0)
    text = f"昵称: {nick}\n群名片: {card}\nQQ号: {qq}\n头像: {avatar}\n角色: {role}"
    await sendMessage.text(text, message)