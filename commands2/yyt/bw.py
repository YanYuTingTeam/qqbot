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
    if len(args) < 1:
        await sendMessage.text("请提供玩家名.", message)
    player_name = args[0]
    if len(player_name) > 16 or len(player_name) < 2 or not check_allowed_chars(player_name):
        await sendMessage.text("请提供正确的玩家名.", message)
    api_url = f"https://www.mcyyt.top/api/bedwars/classic/?name={player_name}"
    await sendMessage.text(f"{sendMessage.at(message.author.member_openid)} 正在请求数据, 请稍等", message, 2)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, timeout=aiohttp.ClientTimeout(10)) as response:
                if response.status != 200:
                    await sendMessage.text(f"请求失败 -> code{response.status}", message)
                data = await response.json()
                if not data.get("success"):
                    await sendMessage.text(f"未找到玩家 {player_name} 的数据", message)
                img_path = await yytbw(data)
                file_url = img_path
                await sendMessage.image(file_url, message)
                if os.path.exists(img_path):
                    os.remove(img_path)
    except asyncio.TimeoutError:
        raise asyncio.TimeoutError()
    except aiohttp.ClientError as e:
        raise aiohttp.ClientError(e)
    except KeyError as e:
        raise KeyError(e)
    except Exception as e:
        if str(e)=="invalid file_info":
            raise Exception("制图时遇到问题, 请重新请求该命令. 若还是出现问题, 请联系bot开发者")
        else:
            raise Exception(e)