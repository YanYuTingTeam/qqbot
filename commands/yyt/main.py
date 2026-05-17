from typing import List
from botpy.message import GroupMessage  
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.sendMessage import sendMessage

async def handle_command(args: List[str], message: GroupMessage) -> str:
    await sendMessage.text("《烟雨庭》 - 菜单\n" \
    "使用命令请先艾特 @小烟雨\n" \
    " ( 括号 ) 内的参数可空\n" \
    "/yyt online - 查看在线人数\n" \
    "/yyt bw <玩家名> - 查询起床战争战绩\n" \
    "/yyt bwxp <玩家名> - 查询起床·无限火力战绩\n" \
    "/yyt gbw <玩家名> - 查询枪械起床战绩\n" \
    "/yyt sw <玩家名> - 查询空岛战争战绩\n" \
    "/yyt top <模式名> <排名> - 查询某模式的第n名玩家战绩(仅限bw, bwxp)",message)