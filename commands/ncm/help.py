from typing import List
from botpy.message import GroupMessage  
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.sendMessage import sendMessage

async def handle_command(args: List[str], message: GroupMessage) -> str:
    await sendMessage.text("小烟雨 BOT - NCM菜单\n" \
    "使用命令请先艾特 @小烟雨\n" \
    " ( 括号 ) 内的参数可空\n" \
    "/ncm search <歌名> (--page <页码>) (--song <编号>) - 搜索音乐. 携带编号时，视为查看当前页码第n首歌的详细信息\n" \
    "/ncm detail <歌曲ID> - 返回歌曲详情\n" \
    "/ncm song <歌曲ID> - 返回歌曲文件(语音)",message)