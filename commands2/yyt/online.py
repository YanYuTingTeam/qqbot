from typing import List
from botpy.message import GroupMessage  
import sys
import os
import aiohttp
import asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.sendMessage import sendMessage

async def handle_command(args: List[str], message: GroupMessage) -> str:
    api_url = f"https://www.mcyyt.cn/api/getServer/?id=**HIDDEN**"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, timeout=aiohttp.ClientTimeout(10)) as response:
                if response.status != 200:
                    await sendMessage.text(f"请求失败 -> code{response.status}", message)
                data = await response.json()
                if not data.get("success"):
                    await sendMessage.text(f"服务器未正确响应", message)
                await sendMessage.text("全服在线人数: "+str(data["online"]), message)
    except asyncio.TimeoutError:
        raise asyncio.TimeoutError()
    except aiohttp.ClientError as e:
        raise aiohttp.ClientError(e)
    except KeyError as e:
        raise KeyError(e)
    except Exception as e:
        raise Exception(e)

 