import asyncio
import aiohttp
from typing import List
from botpy.message import GroupMessage
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from extension.picMaker import *
from extension.image import *
from extension.string import *
from app.sendMessage import sendMessage
from app.yytbw import yytbw

async def handle_command(args: List[str], message: GroupMessage) -> str:
    await sendMessage.text("该玩法的制图暂未开放. 请前往官网查询枪起战绩", message)