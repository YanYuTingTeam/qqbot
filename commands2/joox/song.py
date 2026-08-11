import asyncio
import aiohttp
from typing import List
from botpy.message import GroupMessage
import sys
import os
from urllib.parse import quote
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from extension.audio import *
from app.sendMessage import sendMessage

async def handle_command(args: List[str], message: GroupMessage) -> str:
    if len(args) < 1:
        await sendMessage.text("请提供ID", message)
        return ""
    
    song_id = args[0]
    # joox的id含有 + / = 等字符, 需要URI编码
    encoded_id = quote(song_id, safe='')
    
    try:
        async with aiohttp.ClientSession() as session:
            # 1. 获取歌曲详情, 拿到songmid
            detail_url = f"https://api.aermini.top/joox/detail/?id={encoded_id}"
            async with session.get(detail_url, timeout=aiohttp.ClientTimeout(10)) as response:
                if response.status != 200:
                    await sendMessage.text(f"请求详情失败 -> code{response.status}", message)
                    return ""
                detail_data = await response.json()
            
            song_name = detail_data.get("name", "")
            artist_list = detail_data.get("artist_list", [])
            artists = "、".join([a.get("name", "") for a in artist_list]) if artist_list else "未知"
            await sendMessage.text(f'正在生成{song_name}-{artists}({song_id}), 请稍后', message, 2)
            
            songmid = detail_data.get("songmid", "")
            if not songmid:
                await sendMessage.text("未获取到songmid, 可能该歌曲不可用", message)
                return ""
            
            # 2. 用songmid获取播放链接
            url_api = f"https://api.aermini.top/joox/url/v2.php?filename=M800{songmid}.mp3&password=**HIDDEN**"
            async with session.get(url_api, timeout=aiohttp.ClientTimeout(20)) as response:
                if response.status != 200:
                    await sendMessage.text(f"获取播放链接失败 -> code{response.status}", message)
                    return ""
                url_data = await response.json()
            
            if url_data.get("code") != 200:
                await sendMessage.text(
                    f'获取播放链接失败({url_data.get("code")}) -> {url_data.get("msg", "")}',
                    message
                )
                return ""
            
            play_url = url_data.get("url", "")
            if not play_url:
                await sendMessage.text("暂无该歌曲音源", message)
                return ""
            
            # 3. 转换为语音发送
            await sendMessage.audio(play_url, message, 3)
            
    except asyncio.TimeoutError:
        raise asyncio.TimeoutError()
    except aiohttp.ClientError as e:
        raise aiohttp.ClientError(e)
    except Exception as e:
        raise Exception(e)
    
    return ""
