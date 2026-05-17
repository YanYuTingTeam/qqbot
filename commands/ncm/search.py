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
from app.musicSearchPic import ncmSearchResult

async def handle_command(args: List[str], message: GroupMessage) -> str:
    extra_params = {}
    song_name_parts = []
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
            song_name_parts.append(args[i])
            i += 1
    song_name = " ".join(song_name_parts).strip()
    print (song_name)
    if not song_name:
        await sendMessage.text("请提供歌曲名", message)
        return ""
    
    page = int(extra_params.get("page", 1))
    t = int(extra_params.get("song", 0))
    
    api_url = f"https://zm.wwoyun.cn/cloudsearch?keywords={quote(song_name)}&offset={(page-1)*8}&limit=8"
    
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
            
            img_path = await ncmSearchResult(data, page, t)
            qt = data["result"]["songs"][t]["id"] if t>0 else ""
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