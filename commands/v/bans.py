import asyncio
import aiohttp
from typing import List, Dict, Any
from botpy.message import GroupMessage
import sys
import requests
from urllib.parse import quote
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from extension.picMaker import *
from extension.image import *
from extension.string import *
from app.sendMessage import sendMessage
from app.yytbans import yytbans

async def handle_command(args: List[str], message: GroupMessage) -> str:
    import importlib
    run_path = os.getcwd()
    sys.path.insert(0, run_path)
    config_path = f"commands.v.config"
    if config_path in sys.modules:
        del sys.modules[config_path]
    config = importlib.import_module(config_path)
    if message.author.member_openid not in config.whitelist:
        await sendMessage.text("你没有权限使用这个命令!",message)
        return
    extra_params = {}
    _parts = []
    i = 0
    while i < len(args):
        if args[i].startswith("--"):
            param_name = args[i].lstrip("--")
            if i + 1 < len(args) and not args[i+1].startswith("--"):
                param_value = args[i+1]
                extra_params[param_name] = param_value
                i += 2
            else:
                extra_params[param_name] = None
                i += 1
        else:
            _parts.append(args[i])
            i += 1
    fullstr = " ".join(_parts).strip()
    
    #if not fullstr:
    #    await sendMessage.text("请提供歌曲名", message)
    #    return ""
    
    p = int(extra_params.get("p", 1))
    t = int(extra_params.get("t", 10))
    if t > 10:
        await sendMessage.text(f"单页最大10条结果!", message)
        return
    
    api_url = f"https://www.mcyyt.top/api/bans/list.php?p={p}&t={t}"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, timeout=aiohttp.ClientTimeout(10)) as response:
                if response.status != 200:
                    await sendMessage.text(f"请求失败 -> code{response.status}", message)
                    return ""
                data = await response.json()
            if data["success"] == "false":
                await sendMessage.text(f"请求失败", message)
                return ""
            img_path = await yytbans(data, p, t)
            await sendMessage.image(img_path, message)
            if os.path.exists(img_path):
                os.remove(img_path)
                
    except asyncio.TimeoutError:
        raise asyncio.TimeoutError("拒绝响应, 回源似乎出现问题")
    except aiohttp.ClientError as e:
        raise aiohttp.ClientError(e)
    except KeyError as e:
        raise KeyError(e)
    except Exception as e:
        if str(e)=="invalid file_info":
            raise Exception("制图时遇到问题, 请重新请求该命令. 若还是出现问题, 请联系bot开发者")
        else:
            raise Exception(e)