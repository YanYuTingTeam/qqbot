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
from others.getServers import sendrequest
from others.getServers import get_all_instances
from app.sendMessage import sendMessage

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
    if len(args)<1:
        await sendMessage.text("请提供要封禁的玩家名",message)
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

    did = extra_params.get("did", config.daemon_id)
    btime = extra_params.get("t", "")
    breason = extra_params.get("r", "由于不正当的游戏行为被踢出游戏！")
    if btime=="":
        await sendMessage.text("请提供封禁时间!",message)
        return

    if btime=="-1": btime = ""
    itid = extra_params.get("itid", "**HIDDEN**")
    
    try:
        respone = await sendrequest(
            path='api/protected_instance/command',
            method='GET',
            params={
                'daemonId': did,
                'uuid': itid,
                'command': f'ban {fullstr} {btime} {breason}'
            }
        )
        if respone['data']['status']==200:
            await sendMessage.text(f"你已成功对玩家 {fullstr} 执行封禁\n时间 {btime if btime!="" else "永久"}\n理由 {breason}\n执行人 {message.author.member_openid}\n时间 {get_current_time()}",message)
            return
        else:
            await sendMessage.text(f"对 {fullstr} 执行封禁时遇到问题\n执行人 {message.author}\n时间 {get_current_time()}\n代码 {respone['data']['status']}\n原文 {respone['data']['data']}",message)
            return 
    except asyncio.TimeoutError:
        raise asyncio.TimeoutError()
    except aiohttp.ClientError as e:
        raise aiohttp.ClientError(e)
    except KeyError as e:
        raise KeyError(e)
    except Exception as e:
        raise Exception(e)