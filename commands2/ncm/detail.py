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
from app.musicGetInfo import ncmDetail

async def handle_command(args: List[str], message: GroupMessage) -> str:
    if len(args)<1:
        await sendMessage.text("请提供ID", message)
        return ""
    #try:
    #    m=args[0]/2
    id = args[0]
    
    api_url = f"https://zm.wwoyun.cn/song/detail?ids={id}"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, timeout=aiohttp.ClientTimeout(10)) as response:
                if response.status != 200:
                    await sendMessage.text(f"请求失败 -> code{response.status}", message)
                    return ""
                data = await response.json()
            
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
            
            img_path = await ncmDetail(data, id)
            await sendMessage.image(img_path, message)
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
    
    return ""