
import time
import sys
import os
import asyncio
import aiohttp
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from extension.picMaker import *
from extension.string import *
from extension.getcolor import *

false=False
true=True

async def get_artist_avatar(session: aiohttp.ClientSession, artist_id: int) -> str:
    try:
        async with session.get(f"https://zm.wwoyun.cn/artist/detail?id={artist_id}", timeout=aiohttp.ClientTimeout(5)) as response:
            if response.status != 200:
                return ""
            data = await response.json()
            avatar = data.get("data", {}).get("artist", {}).get("avatar", "")
            return avatar
    except Exception:
        return ""
    
async def get_song_love(session: aiohttp.ClientSession, id: int) -> str:
    try:
        async with session.get(f"https://zm.wwoyun.cn/song/red/count?id={id}", timeout=aiohttp.ClientTimeout(5)) as response:
            if response.status != 200:
                return "undefined"
            data = await response.json()
            loves = data["data"]["count"]
            return loves
    except Exception:
        return "error"
    
async def get_song_comment(session: aiohttp.ClientSession, id: int) -> str:
    try:
        async with session.get(f"https://zm.wwoyun.cn/comment/music?id={id}&limit=0", timeout=aiohttp.ClientTimeout(5)) as response:
            if response.status != 200:
                return "undefined"
            data = await response.json()
            comments = data["total"]
            return comments
    except Exception:
        return "error"

async def ncmDetail(result: object, id: int):
    usefont = r"C:\Users\Administrator\Desktop\qqbot\font\MiSans_Demibold.ttf"
    heavyfont = r"C:\Users\Administrator\Desktop\qqbot\font\MISANS-HEAVY.TTF"
    maxStrLenth = 600

    songs = result.get("songs", [])
    song_list_str=""
    for idx, song in enumerate(songs, start=1):
        artists = song.get("ar", [])
        artist_names = " / ".join([artist.get("name", "未知歌手") for artist in artists])
        song_info = f"{artist_names}"
        if song_list_str:
            song_list_str += "\n" + song_info
        else:
            song_list_str = song_info

    songinfo_bg_path = "assets/ncm_songInfo.png"
    async with aiohttp.ClientSession() as session:
        artist_tasks = []
        artist_positions = []
        songs = result.get("songs", [])

        for song_idx, song in enumerate(songs):
            artists = song.get("ar", [])
            for artist_idx, artist in enumerate(artists):
                artist_id = artist.get("id")
                if artist_id:
                    artist_positions.append((song_idx, artist_idx, artist_id))
                    artist_tasks.append(get_artist_avatar(session, artist_id))

        avatar_results = await asyncio.gather(*artist_tasks)

        for idx, (song_idx, artist_idx, artist_id) in enumerate(artist_positions):
            avatar = avatar_results[idx]
            if avatar:
                result["songs"][song_idx]["ar"][artist_idx]["img"] = avatar
        songComments=await get_song_comment(session, result["songs"][0]["id"])
        songLoves=await get_song_love(session, result["songs"][0]["id"])
    try:
        color_result = get_color_data(result["songs"][0]["al"]["picUrl"]+"?param=300x300")
    except Exception as e:
        return {"error": f"{str(e)}"}

    maker = ImageMaker(songinfo_bg_path)
    # artist
    line_spacing = 80
    start_x = 432
    start_y = 212
    single_line_max_width = 2*maxStrLenth
    avatar_size = 64
    avatar_radius = 200
    text_margin_left = 10
    font_size = "48px"
    max_text_width = single_line_max_width - avatar_size - text_margin_left
    item_spacing = 80
    maker.color_block(
        x="50%",
        y="29%",
        width="96pw",
        height="48ph",
        color="#FFFFFF",
        opacity=0.3,
        radius=[60,60,60,60],
    )
    maker.text(
        x="400px",
        y="100px",
        size="72px",
        font_path=heavyfont,
        color="#FFFFFF",
        opacity=1.0,
        align="left",
        content=f"{maker.truncate_text_by_width(result["songs"][0]["name"],maxStrLenth,"72px",heavyfont,"..") if maker.get_text_size("72px",heavyfont,result["songs"][0]["name"])[0] > 2*maxStrLenth else result["songs"][0]["name"]}"
    )

    maker.text(
        x="50%",
        y="336px",
        size="24px",
        font_path=heavyfont,
        color="#FFFFFF",
        opacity=1.0,
        align="center",
        #content=f"{maker.truncate_text_by_width(c,1200,"56px",usefont,"..") if maker.get_text_size("56px",usefont,c)[0] > 1200 else c}"
        content=f"ID: {result["songs"][0]["id"]}"
    )

    maker.text(
        x="60px",
        y=f"86%",
        size="28px",
        font_path=usefont,
        color="#FFFFFF",
        opacity=1.0,
        align="left",
        content=f"音乐详情 @小烟雨 ncm detail <歌曲ID>"
    )
    maker.text(
        x="60px",
        y=f"93%",
        size="28px",
        font_path=usefont,
        color="#FFFFFF",
        opacity=1.0,
        align="left",
        content=f"播放音乐 @小烟雨 ncm song <歌曲ID>"
    )

    maker.image(
        x="200px",
        y="200px",
        width="300px",
        height="300px",
        radius=[60,60,60,60],
        opacity=1.0,
        img_path=result["songs"][0]["al"]["picUrl"]+"?param=300x300"
    )

    maker.color_block(
        x="50%",
        y="420px",
        width="96pw",
        height="12ph",
        color="#FFFFFF",
        opacity=0.3,
        radius=[200,200,200,200],
    )

    maker.image(
        x="100px",
        y="420px",
        width="64px",
        height="64px",
        #radius=[60,60,60,60],
        opacity=1.0,
        img_path=r"C:\Users\Administrator\Desktop\qqbot\assets\BxAlbum.png"
    )

    maker.text(
        x="52%",
        y="414px",
        size="36px",
        font_path=heavyfont,
        color="#FFFFFF",
        opacity=1.0,
        align="center",
        content=f"《{maker.truncate_text_by_width(result["songs"][0]["al"]["name"],2.3*maxStrLenth,"36px",heavyfont,"..") if maker.get_text_size("36px",heavyfont,result["songs"][0]["al"]["name"])[0] > 2.3*maxStrLenth else result["songs"][0]["al"]["name"]}》"
    )

    maker.color_block(
        x="12%",
        y="515px",
        width="20pw",
        height="12ph",
        color="#FFFFFF",
        opacity=0.3,
        radius=[100,100,100,100],
    )

    maker.image(
        x="100px",
        y="515px",
        width="52px",
        height="52px",
        #radius=[60,60,60,60],
        opacity=1.0,
        img_path=r"C:\Users\Administrator\Desktop\qqbot\assets\ZondiconsTime.png"
    )

    maker.text(
        x="221px",
        y="504px",
        size="36px",
        font_path=heavyfont,
        color="#FFFFFF",
        opacity=1.0,
        align="center",
        #content=f"{maker.truncate_text_by_width(c,1200,"56px",usefont,"..") if maker.get_text_size("56px",usefont,c)[0] > 1200 else c}"
        content=songTime(float(result["songs"][0]["dt"]))
    )

    maker.color_block(
        x="32.5%",
        y="515px",
        width="20pw",
        height="12ph",
        color="#EC9898",
        opacity=0.3,
        radius=[100,100,100,100],
    )

    maker.image(
        x="450px",
        y="515px",
        width="52px",
        height="52px",
        #radius=[60,60,60,60],
        opacity=1.0,
        img_path=r"C:\Users\Administrator\Desktop\qqbot\assets\BxsHeart.png"
    )

    maker.text(
        x="571px",
        y="504px",
        size="36px",
        font_path=heavyfont,
        color="#FFFFFF",
        opacity=1.0,
        align="center",
        #content=f"{maker.truncate_text_by_width(c,1200,"56px",usefont,"..") if maker.get_text_size("56px",usefont,c)[0] > 1200 else c}"
        content=songLoves
    )

    maker.color_block(
        x="53%",
        y="515px",
        width="20pw",
        height="12ph",
        color="#91FFDA",
        opacity=0.3,
        radius=[100,100,100,100],
    )

    maker.image(
        x="800px",
        y="515px",
        width="52px",
        height="52px",
        #radius=[60,60,60,60],
        opacity=1.0,
        img_path=r"C:\Users\Administrator\Desktop\qqbot\assets\MdiComment.png"
    )

    maker.text(
        x="921px",
        y="504px",
        size="36px",
        font_path=heavyfont,
        color="#FFFFFF",
        opacity=1.0,
        align="center",
        #content=f"{maker.truncate_text_by_width(c,1200,"56px",usefont,"..") if maker.get_text_size("56px",usefont,c)[0] > 1200 else c}"
        content=songComments
    )

    maker.color_block(
        x="45%",
        y="92%",
        width="64px",
        height="64px",
        color=color_result["main"],
        opacity=1.0,
        radius=[10,10,10,10],
    )

    maker.color_block(
        x="50%",
        y="92%",
        width="64px",
        height="64px",
        color=color_result["bg"],
        opacity=1.0,
        radius=[10,10,10,10],
    )

    maker.color_block(
        x="55%",
        y="92%",
        width="64px",
        height="64px",
        color=color_result["theme"],
        opacity=1.0,
        radius=[10,10,10,10],
    )

    artists = result["songs"][0]["ar"]
    if not artists:
        pass
    #arlenth = maker.get_text_size("48px",usefont,c)[0]
    #c="STRINGstringSTRINGstringSTRINGstringSTRINGstringSTRINGstringSTRINGstring"
    #c=result["songs"][0]["ar"][0]["name"]
    #maker.image(
    #    x="432px",
    #    y="212px",
    #    width="64px",
    #    height="64px",
    #    radius=[200,200,200,200],
    #    opacity=1.0,
    #    img_path=result["songs"][0]["ar"][0]["img"]+"?param=300x300"
    #)
    #maker.text(
    #        x=f"476px",
    #        y=f"200px",
    #        size="48px",
    #        font_path=usefont,
    #        color="#C4C4C4",
    #        opacity=1.0,
    #        align="left",
    #        content=f"{maker.truncate_text_by_width(c,2*maxStrLenth,"48px",usefont,"..") if maker.get_text_size("48px",usefont,c)[0] #> 2*maxStrLenth else c}"
    #    )

    current_x = start_x
    current_y = start_y

    for idx, artist in enumerate(artists):
        artist_name = artist.get("name", "未知歌手")
        artist_avatar = artist.get("img", "") + "?param=300x300" if artist.get("img") else ""
        normal_height = get_text_bbox(usefont, font_size, "你")[1]
        font_size_num = int(font_size.replace("px", ""))
        text_width, text_height, text_offset_y = get_text_bbox(usefont, font_size, artist_name)

        max_text_width = single_line_max_width - avatar_size - text_margin_left
        if text_width > max_text_width:
            show_name = maker.truncate_text_by_width(
                artist_name, max_text_width, font_size, usefont, ".."
            )
            text_width, text_height, text_offset_y = get_text_bbox(usefont, font_size, show_name)
        else:
            show_name = artist_name

        item_total_width = avatar_size + text_margin_left + text_width

        if current_x + item_total_width > start_x + single_line_max_width and idx > 0:
            current_x = start_x
            current_y += line_spacing

        if artist_avatar:
            maker.image(
                x=f"{current_x}px",
                y=f"{current_y}px",
                width=f"{avatar_size}px",
                height=f"{avatar_size}px",
                radius=[avatar_radius]*4,
                opacity=1.0,
                img_path=artist_avatar
            )

        text_x = current_x + avatar_size + text_margin_left
        text_y = current_y + (normal_height)/2 - (normal_height-text_height)/2 -30

        maker.text(
            x=f"{text_x}px",
            y=f"{text_y}px",
            size=font_size,
            font_path=usefont,
            color="#C4C4C4",
            opacity=1.0,
            align="left",
            content=show_name
        )

        current_x += item_total_width + item_spacing

    return maker.save(f"ncm_search_{int(round(time.time() * 1000))}.png")