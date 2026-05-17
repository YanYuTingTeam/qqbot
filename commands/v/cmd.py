import asyncio
import aiohttp
from typing import List, Dict, Any
from botpy.message import GroupMessage
import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from extension.picMaker import get_current_time
from others.getServers import sendrequest, get_all_instances
from app.sendMessage import sendMessage
import importlib

async def handle_command(args: List[str], message: GroupMessage) -> str:
    run_path = os.getcwd()
    sys.path.insert(0, run_path)
    config_path = f"commands.v.config"
    if config_path in sys.modules:
        del sys.modules[config_path]
    config = importlib.import_module(config_path)

    if message.author.member_openid not in config.opera:
        await sendMessage.text("你没有权限使用这个命令!", message)
        return
    if len(args) < 1:
        await sendMessage.text("参数错误.\n无参数请求你大巴", message)
        return
    if len(args) < 2:
        await sendMessage.text("参数错误.\n已对目标服务器执行滚木", message)
        return

    target_rule = args[0].strip()
    run_command = " ".join(args[1:]).strip()
    try:
        all_instances = await get_all_instances()
        if not all_instances['success']:
            await sendMessage.text(f"获取服务器列表失败 -> {all_instances.get('error', '未知错误')}", message)
            return

        port_uuid_map: Dict[str, str] = {}
        for ins in all_instances['instances']:
            try:
                port = ins['name'].split()[0]
                uuid = ins['uuid']
                port_uuid_map[port] = uuid
            except Exception as e:
                continue

        if not port_uuid_map:
            await sendMessage.text("未获取到任何可用服务器", message)
            return

    except Exception as e:
        await sendMessage.text(f"获取服务器信息异常 -> {repr(e)}", message)
        return

    target_ports = set()
    if target_rule.lower() == "all":
        target_ports = set(port_uuid_map.keys())
    elif "|" in target_rule:
        parts = target_rule.split("|")
        for part in parts:
            part = part.strip()
            if ":" in part:
                try:
                    start, end = part.split(":")
                    start_port = int(start)
                    end_port = int(end)
                    for p in range(start_port, end_port + 1):
                        p_str = str(p)
                        if p_str in port_uuid_map:
                            target_ports.add(p_str)
                except:
                    continue
            else:
                if part in port_uuid_map:
                    target_ports.add(part)
    elif ":" in target_rule:
        try:
            start, end = target_rule.split(":")
            start_port = int(start)
            end_port = int(end)
            for p in range(start_port, end_port + 1):
                p_str = str(p)
                if p_str in port_uuid_map:
                    target_ports.add(p_str)
        except:
            await sendMessage.text("范围格式错误. 不会你就/v help", message)
            return
    else:
        if target_rule in port_uuid_map:
            target_ports.add(target_rule)
        else:
            await sendMessage.text(f"{target_rule} 上没有服务器", message)
            return
    if not target_ports:
        await sendMessage.text("没有匹配到服务器", message)
        return
    
    fail_list = []
    for port in target_ports:
        uuid = port_uuid_map[port]
        try:
            params = {
                'daemonId': config.daemon_id,
                'uuid': uuid,
                'command': run_command
            }
            response = await sendrequest(
                path='api/protected_instance/command',
                method='GET',
                params=params
            )
            status = response.get('data', {}).get('status', 'none')
            if status == 200:
                pass
            else:
                fail_list.append(f"[{port}] 失败 | {json.loads(response['raw_response'])['data']}")
        except asyncio.TimeoutError:
            fail_list.append(f"[{port}] 请求超时")
        except aiohttp.ClientError as e:
            fail_list.append(f"[{port}] 请求错误 -> {repr(e)}")
        except Exception as e:
            fail_list.append(f"[{port}] 异常 -> {repr(e)}")

    result_msg = [
        f"\n===== 命令执行结果 {get_current_time()} =====",
        f"执行命令：{run_command}",
        f"目标服务器：{args[0]}",
    ]

    result_msg.append("")
    result_msg.append(f"失败({len(fail_list)})：")
    if fail_list:
        result_msg.extend(fail_list)
    else:
        result_msg.append("无")
    await sendMessage.text("\n".join(result_msg), message)
    return ""