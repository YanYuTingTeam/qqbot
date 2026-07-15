from typing import List
from botpy.message import GroupMessage
import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.sendMessage import sendMessage
from extension.request import get, post

async def handle_command(args: List[str], message: GroupMessage) -> str:
    await sendMessage.text(f"{await get(f"**HIDDEN BASE**/player/info?name={args[0]}")}", message)
    return