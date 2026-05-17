import asyncio
import aiohttp
from typing import List
from botpy.message import GroupMessage
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.sendMessage import sendMessage
from extension.picMaker import *
from extension.image import *
from extension.string import *
from app.yytbw import yytbw
from app.yytsw import yytsw

async def handle_command(args: List[str], message: GroupMessage) -> str:
    if len(args) < 1:
        await sendMessage.text("请提供模式名.",message)
    if args[0] == 'bw':
        try:
            if not int(args[1]) > 0:
                await sendMessage.text("请输入正确的排名(109&1).",message)
        except:
            await sendMessage.text("请输入正确的排名(111&2).",message)
        top = args[1]
        api_url = f"https://www.mcyyt.top/api/bedwars/classic/top/?rank={top}"
 
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, timeout=aiohttp.ClientTimeout(10)) as response:
                    if response.status != 200:
                        await sendMessage.text(f"请求失败 -> code{response.status}",message)
                    data = await response.json()
                    if not data.get("success"):
                        await sendMessage.text(f"未找到排行第 {top} 名玩家的数据",message)
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
                raise Exception("制图时遇到问题, 请重新请求该命令。 若还是出现问题, 请联系bot开发者")
            else:
                raise Exception(e)
    if args[0] == 'bwxp':
        try:
            if not int(args[1]) > 0:
                await sendMessage.text("请输入正确的排名(109&1).",message)
        except:
            await sendMessage.text("请输入正确的排名(111&2).",message)
        top = args[1]
        api_url = f"https://www.mcyyt.top/api/bedwars/xp/top/?rank={top}"
 
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, timeout=aiohttp.ClientTimeout(10)) as response:
                    if response.status != 200:
                        await sendMessage.text(f"请求失败 -> code{response.status}",message)
                    data = await response.json()
                    if not data.get("success"):
                        await sendMessage.text(f"未找到排行第 {top} 名玩家的数据",message)
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
                raise Exception("制图时遇到问题, 请重新请求该命令。 若还是出现问题, 请联系bot开发者")
            else:
                raise Exception(e)
    if args[0] == 'sw':
        try:
            if not int(args[1]) > 0:
                await sendMessage.text("请输入正确的排名(109&1).",message)
        except:
            await sendMessage.text("请输入正确的排名(111&2).",message)
        top = args[1]
        print(top)
        api_url = f"https://www.mcyyt.top/api/skywars/solo/top/?rank={top}"
 
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, timeout=aiohttp.ClientTimeout(10)) as response:
                    if response.status != 200:
                        await sendMessage.text(f"请求失败 -> code{response.status}",message)
                    data = await response.json()
                    if not data.get("success"):
                        await sendMessage.text(f"未找到排行第 {top} 名玩家的数据",message)
                    img_path = await yytsw(data)
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