from typing import List
from botpy.message import GroupMessage  
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.sendMessage import sendMessage

async def handle_command(args: List[str], message: GroupMessage) -> str:
    await sendMessage.text("小烟雨 BOT - JOOX菜单\n" \
    "使用命令请先艾特 @小烟雨\n" \
    " ( 括号 ) 内的参数可空\n" \
    "/joox search <歌名> - 搜索音乐, 返回歌曲列表(歌曲名/ID/歌手/专辑)\n" \
    "/joox song <歌曲ID> - 返回歌曲文件(语音)",message)
