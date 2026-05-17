from typing import List
from botpy.message import GroupMessage  
import sys
import os
import aiohttp
import asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.sendMessage import sendMessage

async def handle_command(args: List[str], message: GroupMessage) -> str:
    api_url = f"https://list.sweetdreamparty.cn/api/latest"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, timeout=aiohttp.ClientTimeout(10)) as response:
                if response.status != 200:
                    await sendMessage.text(f"请求失败 -> code{response.status}", message)
                data = await response.json()
                await sendMessage.text(f'房间号: {data["room_id"]} | 在线人数: {data["current"]}/{data["max"]}', message)
    except asyncio.TimeoutError:
        await sendMessage.text("请求超时.", message)
    except aiohttp.ClientError as e:
        await sendMessage.text(f"网络请求错误：{str(e)}", message)
    except KeyError as e:
        await sendMessage.text(f"缺失字段：{str(e)}", message)
    except Exception as e:
        await sendMessage.text(f"未知错误：{str(e)}", message)