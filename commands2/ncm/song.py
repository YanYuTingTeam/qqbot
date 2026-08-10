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
from extension.string import *
from extension.audio import *
from app.sendMessage import sendMessage

async def getSlk(session: aiohttp.ClientSession, id: int) -> str:
    try:
        async with session.get(f"https://api.aermini.top/silk/?id={id}", timeout=aiohttp.ClientTimeout(5)) as response:
            if response.status != 200:
                return "undefined"
            data = await response.text()
            return data
    except Exception:
        return "error"

async def handle_command(args: List[str], message: GroupMessage) -> str:
    if len(args)<1:
        await sendMessage.text("请提供ID", message)
        return ""
    #try:
    #    m=args[0]/2
    id = args[0]
    if len(args)>1:
        q = args[1]
    else:
        q="320k"
    if not id:
        await sendMessage.text("在获取ID时遇到问题, 请联系bot开发者修改源码", message)
        return ""
    
    api_url = f"https://api.aermini.top/wy/url/?id={id}&q={q}&key=**HIDDEN**"
    await sendMessage.text(f'正在生成, 请稍等 ({id})', message, 2)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, timeout=aiohttp.ClientTimeout(20)) as response:
                #if response.status != 200:
                #    await sendMessage.text(f"请求失败 -> code{response.status}", message)
                #    return ""
                data = await response.json()
                slk = await getSlk(session, id)

            if data.get("code",-1) == -1:
                await sendMessage.text(f"请求失败, 请检查api是否出现问题", message)
                return ""
            if not data.get("code",-1) == 200:
                await sendMessage.text(f'请求失败({data["code"]}) -> {data["message"]})', message)
                return ""
            if not data.get("url",""):
                await sendMessage.text(f"暂无该歌曲音源", message)
                return ""
            else:
                await sendMessage.audio(data["url"], message, 3)
                #await sendMessage.audioTest(f"https://api.aermini.top/silk/?id={id}", message, 3)
                #await sendMessage.audioT(f"{slk}", message, 3)
                
            
            # artist_tasks = []
            # artist_positions = []
            # songs = data.get("result", {}).get("songs", [])
            # 
            # for song_idx, song in enumerate(songs):
            #     artists = song.get("ar", [])
            #     for artist_idx, artist in enumerate(artists):
            #         artist_id = artist.get("id")
            #         if artist_id:
            #             artist_positions.append((song_idx, artist_idx, artist_id))
            #             artist_tasks.append(get_artist_avatar(session, artist_id))

            # avatar_results = await asyncio.gather(*artist_tasks)

            # for idx, (song_idx, artist_idx, artist_id) in enumerate(artist_positions):
            #     avatar = avatar_results[idx]
            #     if avatar:
            #         data["result"]["songs"][song_idx]["ar"][artist_idx]["img"] = avatar
            
            #img_path = await ncmDetail(data, id)
            #await sendMessage.image(img_path, message)
            #if os.path.exists(img_path):
            #    os.remove(img_path)
                
    except asyncio.TimeoutError:
        raise asyncio.TimeoutError()
    except aiohttp.ClientError as e:
        raise aiohttp.ClientError(e)
    except KeyError as e:
        raise KeyError(e)
    except Exception as e:
        raise Exception(e)
    
    return ""
