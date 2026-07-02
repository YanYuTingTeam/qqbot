import asyncio
import aiohttp
from typing import List, Dict, Any
from botpy.message import GroupMessage
import sys
import requests
from urllib.parse import quote
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from others.getServers import get_all_instances
from extension.picMaker import get_current_time
from app.sendMessage import sendMessage

async def handle_command(args: List[str], message: GroupMessage) -> str:
    import importlib
    run_path = os.getcwd()
    sys.path.insert(0, run_path)
    config_path = f"commands2.v.config"
    if config_path in sys.modules:
        del sys.modules[config_path]
    config = importlib.import_module(config_path)
    if message.author.member_openid not in config.whitelist:
        await sendMessage.text("你没有权限使用这个命令!",message)
        return
    all_instances = await get_all_instances()
    scount=0
    messaget=f"烟雨庭 | {get_current_time()}"
    if all_instances['success']:
        for idx, ins in enumerate(all_instances['instances'], 1):
            #print(ins['status_code'])
            #print(ins['online'])
            if (ins['status_code']==3):
                scount+=1
                if ins['online'] !=0:
                    messaget=messaget+"\n"+f"{ins['name']} - {ins['online']}/{ins['max_online']}"
        messaget=messaget+"\n"+f"正在运行 {scount}/{all_instances['count']} 个服务端"
        await sendMessage.text(f"{messaget}", message)
        

        # 2. 演示：获取第一个实例的详情（如果有实例）
        #if all_instances['count'] > 0:
        #    first_uuid = all_instances['instances'][0]['uuid']
        #    print(f"\n=== 获取单个实例详情（UUID: {first_uuid}）===")
        #    single_ins = get_single_instance(first_uuid)
        #    print(f"请求结果: {'成功' if single_ins['success'] else '失败'}")
    else:
        raise Exception(f"获取实例失败: {all_instances['error']}")
    return ""