from typing import List
from botpy.message import GroupMessage
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.sendMessage import sendMessage
from extension.motd4 import motd

async def handle_command(args: List[str], message: GroupMessage) -> str:
    platform = 0 if int(args[0]) == 0 else 1
    re = await motd(host=args[1], port=19132, platform=platform)
    await sendMessage.text(str(re), message)