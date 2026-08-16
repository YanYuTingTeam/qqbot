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


async def is_audio_url(session: aiohttp.ClientSession, url: str) -> bool:
    """
    检测直链是否返回有效音频。
    如果返回的是 XML 错误页（例如 NoSuchKey），则判定为无效。
    """
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(15)) as resp:
            if resp.status != 200:
                return False

            # 读取前 128 字节，音频文件一般是二进制，而 XML 错误页是文本
            chunk = await resp.content.read(128)
            stripped = chunk.lstrip()

            # 出现 XML 错误页特征则无效
            if stripped.startswith(b'<?xml') or b'<Error>' in stripped or b'NoSuchKey' in stripped:
                return False

            # 根据 Content-Type 辅助判断
            ctype = resp.headers.get('Content-Type', '').lower()
            if 'audio' in ctype or 'mpeg' in ctype or 'octet-stream' in ctype:
                return True

            return False
    except Exception:
        return False


async def fetch_play_url(
    session: aiohttp.ClientSession,
    quality: str,
    songmid: str
) -> str:
    """请求指定音质的播放地址，返回直链，失败返回空字符串"""
    url_api = (
        f"https://api.aermini.top/joox/url/v2.php"
        f"?filename={quality}{songmid}.mp3&password=**HIDDEN**"
    )

    try:
        async with session.get(url_api, timeout=aiohttp.ClientTimeout(20)) as response:
            if response.status != 200:
                return ""
            data = await response.json()

        if data.get("code") != 200:
            return ""

        return data.get("url", "")
    except Exception:
        return ""


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
            await sendMessage.text(
                f'正在生成{song_name} - {artists}({song_id}), 请稍后',
                message,
                2
            )

            songmid = detail_data.get("songmid", "")
            if not songmid:
                await sendMessage.text("未获取到songmid, 可能该歌曲不可用", message)
                return ""

            # 2. 优先尝试 M800，如果直链是 XML 错误页，再回退到 M500
            play_url = None
            for quality in ("M800", "M500"):
                candidate = await fetch_play_url(session, quality, songmid)
                if not candidate:
                    continue

                # 3. 检测直链是否为有效音频
                if await is_audio_url(session, candidate):
                    play_url = candidate
                    break

            if not play_url:
                await sendMessage.text("暂无该歌曲可用音源", message)
                return ""

            # 4. 发送语音
            await sendMessage.audio(play_url, message, 3)

    except asyncio.TimeoutError:
        raise asyncio.TimeoutError()
    except aiohttp.ClientError as e:
        raise aiohttp.ClientError(e)
    except Exception as e:
        raise Exception(e)

    return ""