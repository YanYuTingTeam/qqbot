import asyncio
import aiohttp
from typing import List
from botpy.message import GroupMessage
import sys
import os
from urllib.parse import quote
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.sendMessage import sendMessage

# 音质映射: 前缀 -> (扩展名, 中文名)
QUALITY_MAP = {
    "M500": ("mp3", "标准"),
    "M800": ("mp3", "极高"),
    "F000": ("flac", "无损"),
    "RS01": ("flac", "Hi-Res"),
    "Q0M0": ("flac", "全景声"),
    "AIM0": ("flac", "母带"),
}

def _is_song_id(s: str) -> bool:
    """判断输入是歌曲id还是songmid. 歌曲id含有 + / = 等base64字符"""
    return '=' in s or '+' in s or '/' in s

async def handle_command(args: List[str], message: GroupMessage) -> str:
    if not args:
        await sendMessage.text("用法: /joox d <歌曲ID或songmid> <音质>\n输入 /joox d help 查看支持的音质", message)
        return ""
    
    if args[0].lower() == "help":
        lines = ["JOOX 支持的音质:"]
        for prefix, (_, name) in QUALITY_MAP.items():
            lines.append(f"{prefix}  {name}")
        await sendMessage.text("\n".join(lines), message)
        return ""
    
    if len(args) < 2:
        await sendMessage.text("请提供音质参数\n输入 /joox d help 查看支持的音质", message)
        return ""
    
    target = args[0]
    quality = args[1].upper()
    
    if quality not in QUALITY_MAP:
        await sendMessage.text(f"不支持的音质: {quality}\n输入 /joox d help 查看支持的音质", message)
        return ""
    
    ext, quality_name = QUALITY_MAP[quality]
    
    try:
        async with aiohttp.ClientSession() as session:
            songmid = target
            song_name = ""
            artists = ""
            
            # 如果传入的是歌曲id(含base64特殊字符), 需要先获取详情拿到songmid
            if _is_song_id(target):
                encoded_id = quote(target, safe='')
                detail_url = f"https://api.aermini.top/joox/detail/?id={encoded_id}"
                async with session.get(detail_url, timeout=aiohttp.ClientTimeout(10)) as response:
                    if response.status != 200:
                        await sendMessage.text(f"请求详情失败 -> code{response.status}", message)
                        return ""
                    detail_data = await response.json()
                
                songmid = detail_data.get("songmid", "")
                song_name = detail_data.get("name", "")
                artist_list = detail_data.get("artist_list", [])
                artists = "、".join([a.get("name", "") for a in artist_list]) if artist_list else "未知"
                
                if not songmid:
                    await sendMessage.text("未获取到songmid, 可能该歌曲不可用", message)
                    return ""
            
            # 获取播放链接
            url_api = f"https://api.aermini.top/joox/url/v2.php?filename={quality}{songmid}.{ext}&password=**HIDDEN**"
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
            
            # 发送带按钮的消息
            if song_name:
                title = f"{song_name}-{artists}"
            else:
                title = f"{songmid}"
            md_content = f"JOOX 播放\n{title}\n音质: {quality} {quality_name}"
            await sendMessage.buttonLink(md_content, play_url, message)
            
    except asyncio.TimeoutError:
        raise asyncio.TimeoutError()
    except aiohttp.ClientError as e:
        raise aiohttp.ClientError(e)
    except Exception as e:
        raise Exception(e)
    
    return ""
