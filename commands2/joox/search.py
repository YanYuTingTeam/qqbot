import asyncio
import aiohttp
from typing import List
from botpy.message import GroupMessage
import sys
import os
from urllib.parse import quote
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.sendMessage import sendMessage

def _escape_md_cell(text: str) -> str:
    """转义markdown表格单元格中的特殊字符"""
    if text is None:
        return ""
    return str(text).replace("|", "\\|").replace("\n", " ")

async def handle_command(args: List[str], message: GroupMessage) -> str:
    song_name = " ".join(args).strip()
    if not song_name:
        await sendMessage.text("请提供歌曲名", message)
        return ""
    
    api_url = f"https://api.aermini.top/joox/search/?q={quote(song_name)}"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, timeout=aiohttp.ClientTimeout(10)) as response:
                if response.status != 200:
                    await sendMessage.text(f"请求失败 -> code{response.status}", message)
                    return ""
                data = await response.json()
        
        tracks_raw = data.get("tracks", [])
        # tracks是单元素数组的列表, 每个元素形如 [track_obj]
        tracks = [t[0] for t in tracks_raw if isinstance(t, list) and len(t) > 0]
        
        if not tracks:
            await sendMessage.text("未找到相关歌曲", message)
            return ""
        
        lines = []
        lines.append("| 序号 | 歌曲名 | 歌曲ID | 歌手 | 专辑 |")
        lines.append("| --- | --- | --- | --- | --- |")
        for idx, track in enumerate(tracks, 1):
            name = _escape_md_cell(track.get("name", ""))
            song_id = _escape_md_cell(track.get("id", ""))
            artist_list = track.get("artist_list", [])
            if artist_list:
                artists = _escape_md_cell("/".join([a.get("name", "") for a in artist_list]))
            else:
                artists = "未知"
            album = _escape_md_cell(track.get("album_name", ""))
            lines.append(f"| {idx} | {name} | {song_id} | {artists} | {album} |")
        
        table = "\n".join(lines)
        header = f"JOOX 搜索结果: {song_name}\n共找到 {len(tracks)} 首\n\n"
        await sendMessage.text(header + table, message)
        
    except asyncio.TimeoutError:
        raise asyncio.TimeoutError()
    except aiohttp.ClientError as e:
        raise aiohttp.ClientError(e)
    except Exception as e:
        raise Exception(e)
    
    return ""
