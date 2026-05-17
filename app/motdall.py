import time
import sys
import os
import asyncio
import base64
from io import BytesIO
from PIL import Image
import tempfile

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from extension.picMaker import *
from extension import motdtest
from extension import motd2
from extension import motd3
from extension import motd4
from extension.string import *

def base64_to_imgpath(b64_data):
    if not b64_data or not b64_data.startswith("data:image/"):
        return None
    try:
        d = b64_data.split(",",1)[1]
        data = base64.b64decode(d)
        im = Image.open(BytesIO(data))
        tmp = tempfile.mktemp(".png")
        im.save(tmp)
        return tmp
    except:
        return None

async def motdall(json_list):
    font_path = r"C:\Users\Administrator\Desktop\qqbot\font\Minecraft_AE.ttf"
    bg_path = "assets/motd_allbg.png"

    maker = ImageMaker(str(bg_path))

    xyall = [
        [1640, 400, 72],
        [1640, 610, 72],
        [1640, 820, 72],
        [1640, 1030, 72],
        [1640, 1940, 72],
        [1640, 2150, 72],
        #[3400, 400, 72],
        [3400, 610, 72],
        [3400, 1480, 72],
        [3400, 2530, 72],
        [3400, 2840, 72],
    ]

    group = [
        {'x':440,'y':1395,'ar':[1,2,3,4]},
        {'x':440,'y':2520,'ar':[5,6]},
        {'x':2184,'y':965,'ar':[7]},
        {'x':2184,'y':1980,'ar':[8]},
        {'x':2184,'y':3204,'ar':[9,10]}
    ]

    for i, server_data in enumerate(json_list):
        if i >= len(xyall):
            break
        
        try:
            status = server_data.get('status', 'offline')
            players = server_data.get('players', {})
            online = players.get('online', 0)
            max_players = players.get('max', 0)

            color = "#00FF00" if status == 'online' else "#FF0000"
            content = f"{online}/{max_players}" if status == 'online' else "✘"

            maker.text(
                x=f"{xyall[i][0]}px",
                y=f"{xyall[i][1]}px",
                size=f"{xyall[i][2]}px",
                font_path=str(font_path),
                color=color,
                opacity=1.0,
                align="right",
                content=content
            )

        except Exception as e:
            maker.text(
                x=f"{xyall[i][0]}px",
                y=f"{xyall[i][1]}px",
                size=f"{xyall[i][2]}px",
                font_path=str(font_path),
                color="#FFFF00",
                align="right",
                content="错误"
            )

    temp_list = []

    for g in group:
        gx = g['x']
        gy = g['y']
        server_ids = g['ar']

        final_ip = "服务器不存在开放的IP"
        final_ico = r"C:\Users\Administrator\Desktop\qqbot\assets\server_ico.png"
        final_motd = "服务器离线"

        for sid in server_ids:
            idx = sid - 1
            if idx < 0 or idx >= len(json_list):
                continue
            data = json_list[idx]
            if data.get("status") == "online":
                motd_str = data.get("motd_clean", "").strip()
                final_ip = data.get("host", "")
                if final_ip == "":
                    final_ip = "服务器不存在开放的IP"
                final_ico = data.get("favicon_url", "")
                if final_ico == "":
                    final_ico = r"C:\Users\Administrator\Desktop\qqbot\assets\server_ico.png"

                final_motd = motd_str[:100]
                break
            


        ico_path = final_ico
        if ico_path.startswith("data:image/png"):
            temp_ico = base64_to_imgpath(ico_path)
            if temp_ico:
                ico_path = temp_ico
                temp_list.append(ico_path)
            else:
                ico_path = r"C:\Users\Administrator\Desktop\qqbot\assets\server_ico.png"
        if not os.path.exists(ico_path):
            ico_path = r"C:\Users\Administrator\Desktop\qqbot\assets\server_ico.png"

        maker.text(
            x=f"{gx}px",
            y=f"{gy-128}px",
            size="80px",
            font_path=str(font_path),
            color="#ffebab",
            opacity=1.0,
            align="left",
            content=final_ip
        )

        #maker.text( # ping
        #    x=f"{gx+1220}px",
        #    y=f"{gy-196}px",
        #    size="64px",
        #    font_path=str(font_path),
        #    color="#52dcff",
        #    opacity=1.0,
        #    align="right",
        #    content=str(data.get("delay"))+"ms" if str(data.get("delay"))+"ms" !="Nonems" else ""
        #)

        maker.image(
            x=f"{gx-170}px",
            y=f"{gy-60}px",
            width="276px",
            height="276px",
            opacity=1.0,
            img_path=str(ico_path)
        )

        maker.text(
            x=f"{gx}px",
            y=f"{gy}px",
            size="56px",
            font_path=str(font_path),
            color="#aaedfd",
            opacity=1.0,
            align="left",
            content=final_motd
        )

    for p in temp_list:
        try: os.remove(p)
        except: pass

    maker.text(
        x=f"200px",
        y=f"3350px",
        size="60px",
        font_path=str(font_path),
        color="#ffffff",
        opacity=1.0,
        align="left",
        content=get_current_time()
    )

    return maker.save(f"motd_all_{int(time.time()*1000)}.png")

async def todo(way: int = 1):
    servers = [
        ('mcyyt.top', 25565),
        ('mc.mcyyt.top', 25565),
        ('mc2.mcyyt.top', 25565),
        ('mc3.mcyyt.top', 25565),
        ('hyt.nccc.top', 25565),
        ('hyt.galastar.icu', 25565),
        #('sq1.hyt.xuebai.xyz', 25565),
        ('frp-ski.com', 44899),
        ('hyt.backup.wanweitool.cn', 25565),
        ('mc.huazhiwu.top', 25590),
        ('mc163.gxeea.xyz', 25565)
    ]
    
    try:
        tasks = []
        for server, port in servers:
            if port:
                if way ==1:
                    task = asyncio.create_task(motd4.motd(server, port))
                elif way ==2:
                    task = asyncio.create_task(motd3.motd(server, port))
                elif way ==3:
                    task = asyncio.create_task(motdtest.motd(server, port))
                else:
                    task = asyncio.create_task(motd2.motd(server, port))
            else:
                if way ==1:
                    task = asyncio.create_task(motd4.motd(server))
                elif way ==2:
                    task = asyncio.create_task(motd3.motd(server))
                elif way ==3:
                    task = asyncio.create_task(motdtest.motd(server))
                else:
                    task = asyncio.create_task(motd2.motd(server))
            tasks.append(task)

        info_list = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i in range(len(info_list)):
            if isinstance(info_list[i], Exception):
                info_list[i] = {
                    "status": "offline", 
                    "players": {"online": 0, "max": 0},
                    "motd_clean": "获取失败",
                    "motd_html": "",
                    "favicon_url": "",
                    "host": ""
                }
        
        return await motdall(info_list)
            
    except Exception as e:
        print(f"程序执行出错: {str(e)}")