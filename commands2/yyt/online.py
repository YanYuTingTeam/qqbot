from typing import List
from botpy.message import GroupMessage  
import sys
import os
import aiohttp
import asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.sendMessage import sendMessage
from extension.request import get, post

async def handle_command(args: List[str], message: GroupMessage) -> str:
    #api_url = f"https://www.mcyyt.cn/api/getServer/?id=**HIDDEN**"
    try:
        data = await get(f"**HIDDEN BASE**/player/list?t=0")
        await sendMessage.text("全服在线人数: "+str(data["data"]["total"]), message)
    except asyncio.TimeoutError:
        raise asyncio.TimeoutError()
    except aiohttp.ClientError as e:
        raise aiohttp.ClientError(e)
    except KeyError as e:
        raise KeyError(e)
    except Exception as e:
        raise Exception(e)

 