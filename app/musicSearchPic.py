
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

async def ncmSearchResult(result: object, page: int = 1, songNum: int = 0):
    usefont = r"C:\Users\Administrator\Desktop\qqbot\font\MiSans_Demibold.ttf"
    heavyfont = r"C:\Users\Administrator\Desktop\qqbot\font\MISANS-HEAVY.TTF"
    lenth = result["result"]["songCount"]
    maxStrLenth = 600
    #ioffset = (page-1)*8
    ioffset = 0

    songs = result.get("result", {}).get("songs", [])
    song_list_str=""
    for idx, song in enumerate(songs, start=1):
        artists = song.get("ar", [])
        artist_names = " / ".join([artist.get("name", "未知歌手") for artist in artists])
        song_info = f"{artist_names}"
        if song_list_str:
            song_list_str += "\n" + song_info
        else:
            song_list_str = song_info

    array = song_list_str.split('\n')
    test_bg_path = "assets/ncm_search.png"
    songinfo_bg_path = "assets/ncm_songInfo.png"
    if songNum==0:
        maker = ImageMaker(test_bg_path)
        maker.text(
            x="50%",
            y="3%",
            size="72px",
            font_path=usefont,
            color="#FFFFFF",
            opacity=1.0,
            align="center",
            content=f"共有 {lenth} 条搜索结果"
        )
        maker.text(
            x="50%",
            y="7%",
            size="46px",
            font_path=usefont,
            color="#FFFFFF",
            opacity=1.0,
            align="center",
            content=f"每页仅显示 8 条结果"
        )
        maker.text(
            x="8.2%",
            y=f"96%",
            size="48px",
            font_path=heavyfont,
            color="#FFFFFF",
            opacity=1.0,
            align="left",
            content=f"@小烟雨 ncm search <歌名> (--page <页码>) (--song 编号)"
        )

        if lenth==0 or len(array[ioffset:])==0:
            maker.text(
                x="50%",
                y="50%",
                size="72px",
                font_path=usefont,
                color="#FFFFFF",
                opacity=1.0,
                align="center",
                content=f"没有任何搜索结果哦~"
            )
            maker.text(
                x="8.2%",
                y=f"93%",
                size="48px",
                font_path=heavyfont,
                color="#FFFFFF",
                opacity=1.0,
                align="left",
                content=f"第 {page} 页没有任何内容~"
            )
        else:
            maker.text(
                x="8.2%",
                y=f"93%",
                size="48px",
                font_path=heavyfont,
                color="#FFFFFF",
                opacity=1.0,
                align="left",
                content=f"正在显示第 {page} 页 (第{ioffset+1}-{page*8 if len(array[ioffset:])>8 else ioffset+len(array[ioffset:])}条)~"
            )
            if (len(array)-ioffset)>8:
                print(1)
                y_offset = 10
                for i in range(0,8):
                    maker.color_block(
                        x="50%",
                        y=f"{14+(i)*y_offset}%",
                        width="90pw",
                        height="9ph",
                        color="#FFFFFF",
                        opacity=0.3,
                        radius=[30,30,30,30],
                    )
                    maker.text(
                        x="8.2%",
                        y=f"{13+(i)*y_offset}%",
                        size="96px",
                        font_path=heavyfont,
                        color="#FFA137",
                        opacity=1.0,
                        align="left",
                        content=f"{(i+ioffset)+1}"
                    )
                    maker.image(
                        x="12%",
                        y=f"{14+(i)*y_offset}%",
                        width="180px",
                        height="180px",
                        radius=[20,20,20,20],
                        opacity=1.0,
                        img_path=result["result"]["songs"][(i+ioffset)]["al"]["picUrl"]+"?param=160x160"
                    )
                    # 歌名
                    maker.text(
                        x=f"19.5%",
                        y=f"{12+(i)*y_offset}%",
                        size="64px",
                        font_path=usefont,
                        color="#FFFFFF",
                        opacity=1.0,
                        align="left",
                        content=f"{maker.truncate_text_by_width(result["result"]["songs"][(i+ioffset)]["name"],maxStrLenth,"64px",usefont,"..") if maker.get_text_size("64px",usefont,result["result"]["songs"][(i+ioffset)]["name"])[0] > maxStrLenth else result["result"]["songs"][(i+ioffset)]["name"]}"
                        #content=result["result"]["songs"][(i+ioffset)]["name"]
                    )
                    # 歌手
                    maker.text(
                        x=f"19.5%",
                        y=f"{15+(i)*y_offset}%",
                        size="48px",
                        font_path=usefont,
                        color="#C4C4C4",
                        opacity=1.0,
                        align="left",
                        content=f"{maker.truncate_text_by_width(array[(i+ioffset)],maxStrLenth,"48px",usefont,"..") if maker.get_text_size("48px",usefont,array[(i+ioffset)])[0] > maxStrLenth else array[(i+ioffset)]}"
                        #content=array[(i+ioffset)]
                        #content=result["result"]["songs"][(i+ioffset)]["name"]
                    )
                    # 专辑
                    maker.text(
                        x=f"94%",
                        y=f"{12+(i)*y_offset}%",
                        size="48px",
                        font_path=usefont,
                        color="#C4C4C4",
                        opacity=1.0,
                        align="right",
                        content=f"{maker.truncate_text_by_width(result["result"]["songs"][(i+ioffset)]["al"]["name"],maxStrLenth,"48px",usefont,"..") if maker.get_text_size("48px",usefont,result["result"]["songs"][(i+ioffset)]["al"]["name"])[0] > maxStrLenth else result["result"]["songs"][(i+ioffset)]["al"]["name"]}"
                        #content=result["result"]["songs"][(i+ioffset)]["al"]["name"]
                    )
                    # 时长
                    maker.text(
                        x=f"94%",
                        y=f"{15+(i)*y_offset}%",
                        size="48px",
                        font_path=usefont,
                        color="#C4C4C4",
                        opacity=1.0,
                        align="right",
                        #content=f"{maker.truncate_text_by_width(c,1200,"56px",usefont,"..") if maker.get_text_size("56px",usefont,c)[0] > 1200 else c}"
                        content=songTime(float(result["result"]["songs"][(i+ioffset)]["dt"]))
                    )
            else:
                y_offset = 10
                for i, c in enumerate(array[ioffset:]):
                    maker.color_block(
                        x="50%",
                        y=f"{14+(i)*y_offset}%",
                        width="90pw",
                        height="9ph",
                        color="#FFFFFF",
                        opacity=0.3,
                        radius=[30,30,30,30],
                    )
                    maker.text(
                        x="8.2%",
                        y=f"{13+(i)*y_offset}%",
                        size="96px",
                        font_path=heavyfont,
                        color="#FFA137",
                        opacity=1.0,
                        align="left",
                        content=f"{(i)+1}"
                    )
                    maker.image(
                        x="12%",
                        y=f"{14+(i)*y_offset}%",
                        width="180px",
                        height="180px",
                        radius=[20,20,20,20],
                        opacity=1.0,
                        img_path=result["result"]["songs"][(i+ioffset)]["al"]["picUrl"]+"?param=160x160"
                    )
                    # 歌名
                    maker.text(
                        x=f"19.5%",
                        y=f"{12+(i)*y_offset}%",
                        size="64px",
                        font_path=usefont,
                        color="#FFFFFF",
                        opacity=1.0,
                        align="left",
                        content=f"{maker.truncate_text_by_width(result["result"]["songs"][(i+ioffset)]["name"],maxStrLenth,"64px",usefont,"..") if maker.get_text_size("64px",usefont,result["result"]["songs"][(i+ioffset)]["name"])[0] > maxStrLenth else result["result"]["songs"][(i+ioffset)]["name"]}"
                        #content=result["result"]["songs"][(i+ioffset)]["name"]
                    )
                    # 歌手
                    maker.text(
                        x=f"19.5%",
                        y=f"{15+(i)*y_offset}%",
                        size="48px",
                        font_path=usefont,
                        color="#C4C4C4",
                        opacity=1.0,
                        align="left",
                        content=f"{maker.truncate_text_by_width(c,maxStrLenth,"48px",usefont,"..") if maker.get_text_size("48px",usefont,c)[0] > maxStrLenth else c}"
                        #content=c
                        #content=result["result"]["songs"][(i+ioffset)]["name"]
                    )
                    # 专辑
                    maker.text(
                        x=f"94%",
                        y=f"{12+(i)*y_offset}%",
                        size="48px",
                        font_path=usefont,
                        color="#C4C4C4",
                        opacity=1.0,
                        align="right",
                        content=f"{maker.truncate_text_by_width(result["result"]["songs"][(i+ioffset)]["al"]["name"],maxStrLenth,"48px",usefont,"..") if maker.get_text_size("48px",usefont,result["result"]["songs"][(i+ioffset)]["al"]["name"])[0] > maxStrLenth else result["result"]["songs"][(i+ioffset)]["al"]["name"]}"
                        #content=result["result"]["songs"][(i+ioffset)]["al"]["name"]
                    )
                    # 时长
                    maker.text(
                        x=f"94%",
                        y=f"{15+(i)*y_offset}%",
                        size="48px",
                        font_path=usefont,
                        color="#C4C4C4",
                        opacity=1.0,
                        align="right",
                        #content=f"{maker.truncate_text_by_width(c,1200,"56px",usefont,"..") if maker.get_text_size("56px",usefont,c)[0] > 1200 else c}"
                        content=songTime(float(result["result"]["songs"][(i+ioffset)]["dt"]))
                    )
    else:
        async with aiohttp.ClientSession() as session:
            artist_tasks = []
            artist_positions = []
            songs = result.get("result", {}).get("songs", [])

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
                    result["result"]["songs"][song_idx]["ar"][artist_idx]["img"] = avatar
            songComments=await get_song_comment(session, result["result"]["songs"][(songNum-1)]["id"])
            songLoves=await get_song_love(session, result["result"]["songs"][(songNum-1)]["id"])
        try:
            color_result = get_color_data(result["result"]["songs"][(songNum-1)]["al"]["picUrl"]+"?param=300x300")
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
            content=f"{maker.truncate_text_by_width(result["result"]["songs"][(songNum-1)]["name"],3*maxStrLenth,"72px",heavyfont,"..") if maker.get_text_size("72px",heavyfont,result["result"]["songs"][(songNum-1)]["name"])[0] > 3*maxStrLenth else result["result"]["songs"][(songNum-1)]["name"]}"
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
            content=f"ID: {result["result"]["songs"][(songNum-1)]["id"]}"
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
            img_path=result["result"]["songs"][(songNum-1)]["al"]["picUrl"]+"?param=300x300"
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
            content=f"《{maker.truncate_text_by_width(result["result"]["songs"][(songNum-1)]["al"]["name"],2.3*maxStrLenth,"36px",heavyfont,"..") if maker.get_text_size("36px",heavyfont,result["result"]["songs"][(songNum-1)]["al"]["name"])[0] > 2.3*maxStrLenth else result["result"]["songs"][(songNum-1)]["al"]["name"]}》"
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
            content=songTime(float(result["result"]["songs"][(songNum-1)]["dt"]))
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

        artists = result["result"]["songs"][(songNum-1)]["ar"]
        if not artists:
            pass
        #arlenth = maker.get_text_size("48px",usefont,c)[0]
        #c="STRINGstringSTRINGstringSTRINGstringSTRINGstringSTRINGstringSTRINGstring"
        #c=result["result"]["songs"][0]["ar"][0]["name"]
        #maker.image(
        #    x="432px",
        #    y="212px",
        #    width="64px",
        #    height="64px",
        #    radius=[200,200,200,200],
        #    opacity=1.0,
        #    img_path=result["result"]["songs"][0]["ar"][0]["img"]+"?param=300x300"
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

#asyncio.run(ncmSearchResult({"result":{"songs":[{"no":1,"rt":"","copyright":1,"fee":1,"hr":{"br":1666804,"fid":0,"size":35172410,"vd":-66883,"sr":48000},"privilege":{"flag":1545476,"code":0,"dlLevel":"none","subp":1,"fl":0,"fee":1,"dl":0,"plLevel":"none","maxBrLevel":"jymaster","rightSource":0,"maxbr":999000,"id":1903876057,"sp":7,"payed":0,"st":0,"chargeInfoList":[{"rate":128000,"chargeType":1},{"rate":192000,"chargeType":1},{"rate":320000,"chargeType":1},{"rate":999000,"chargeType":1},{"rate":1999000,"chargeType":1}],"freeTrialPrivilege":{"userConsumable":false,"resConsumable":true},"downloadMaxbr":999000,"downloadMaxBrLevel":"jymaster","cp":1,"preSell":false,"playMaxBrLevel":"jymaster","cs":false,"toast":false,"playMaxbr":999000,"flLevel":"none","pl":0},"mst":9,"pst":0,"pop":100,"dt":168813,"rtype":0,"s_id":0,"rtUrls":[],"resourceState":true,"id":1903876057,"sq":{"br":898474,"fid":0,"size":18959345,"vd":-66883,"sr":48000},"st":0,"cd":"01","publishTime":1639670400000,"cf":"","originCoverType":1,"h":{"br":320000,"fid":0,"size":6754605,"vd":-66888,"sr":48000},"mv":0,"al":{"picUrl":"http://p4.music.126.net/tuWLl2YkJfe6EOvdnpg9rw==/109951169398455370.jpg","name":"先说谎的人先说谎的人先说谎的人先说谎的人先说谎的人先说谎的人先说谎的人先说谎的人先说谎的人先说谎的人先说谎的人先说谎的人","tns":[],"pic_str":"109951169398455370","id":137562590,"pic":109951169398455380},"l":{"br":128000,"fid":0,"size":2701869,"vd":-62593,"sr":48000},"m":{"br":192000,"fid":0,"size":4052781,"vd":-64282,"sr":48000},"version":17,"cp":7001,"alia":[],"djId":0,"single":0,"ar": [
#  {
#    "img": "http://p3.music.126.net/G2kq-NIoODip5BKfQQ26IQ==/109951171498892287.jpg",
#    "name": "h3R3",
#    "tns": [],
#    "alias": ["刘清云"],
#    "id": 12631485,
#    "alia": ["刘清云"]
#  },
#  {
#    "img": "http://p3.music.126.net/G2kq-NIoODip5BKfQQ26IQ==/109951171498892287.jpg",
#    "name": "张鑫",
#    "tns": [],
#    "alias": [],
#    "id": 28085427
#  }
#],"ftype":0,"t":0,"v":51,"name":"先说谎的人","mark":17716748288}],"songCount":301},"code":200,"trp":{"rules":["search_tab_song::1903876057::searchAlg$isGlobalQuality$1"]}},1,1))