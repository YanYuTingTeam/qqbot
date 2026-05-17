
import time
import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from extension.picMaker import *

true = True

async def yytsw(json):
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    usefont = r"C:\Users\Administrator\Desktop\qqbot\font\MiSans_Demibold.ttf"
    test_bg_path = "assets/swbg.png"
    maker = ImageMaker(test_bg_path)

    if json["data"]["deaths"] == 0:
        kd = "0"
    else:
        kd = round(json["data"]["kills"]/json["data"]["deaths"], 2)

    if json["data"]["gamesPlayed"] == 0:
        wl = "0%"
    else:
        wl = str(round(json["data"]["wins"]/json["data"]["gamesPlayed"]*100, 2))+"%"

    maker.text(
        x="16.5%",
        y="30%",
        size="72px",
        font_path=usefont,
        color="#FFFFFF",
        opacity=1.0,
        align="left",
        content=json["playername"]
    )
    maker.text(
        x="16.5%",
        y="40.5%",
        size="64px",
        font_path=usefont,
        color="#FFFFFF",
        opacity=1.0,
        align="left",
        content=get_current_time()
    )
    maker.text(
        x="42%",
        y="12.9%",
        size="56px",
        font_path=usefont,
        color="#FFFFFF",
        opacity=1.0,
        align="left",
        content=json["uuid"]
    )
    maker.text(
        x="49%",
        y="34.7%",
        size="96px",
        font_path=usefont,
        color="#FFFFFF",
        opacity=1.0,
        align="left",
        content=json["data"]["kills"]
    )
    maker.text(
        x="49%",
        y="45%",
        size="96px",
        font_path=usefont,
        color="#FFFFFF",
        opacity=1.0,
        align="left",
        content=json["data"]["deaths"]
    )

    maker.text(
        x="49%",
        y="55.2%",
        size="96px",
        font_path=usefont,
        color="#FFFFFF",
        opacity=1.0,
        align="left",
        content=kd
    )
    maker.text(
        x="49%",
        y="65.5%",
        size="96px",
        font_path=usefont,
        color="#FFFFFF",
        opacity=1.0,
        align="left",
        content=json["data"]["escapes"]
    )

    maker.text(
        x="16.5%",
        y="60%",
        size="96px",
        font_path=usefont,
        color="#FFFFFF",
        opacity=1.0,
        align="left",
        content=json["data"]["rank"]
    )

    maker.text(
        x="16.5%",
        y="71%",
        size="96px",
        font_path=usefont,
        color="#FFFFFF",
        opacity=1.0,
        align="left",
        content=json["data"]["elo"]
    )
    maker.text(
        x="80%",
        y="34.7%",
        size="96px",
        font_path=usefont,
        color="#FFFFFF",
        opacity=1.0,
        align="left",
        content=json["data"]["gamesPlayed"]
    )
    maker.text(
        x="80%",
        y="45%",
        size="96px",
        font_path=usefont,
        color="#FFFFFF",
        opacity=1.0,
        align="left",
        content=json["data"]["wins"]
    )
    maker.text(
        x="80%",
        y="55.2%",
        size="96px",
        font_path=usefont,
        color="#FFFFFF",
        opacity=1.0,
        align="left",
        content=json["data"]["losses"]
    )
    maker.text(
        x="80%",
        y="65.5%",
        size="96px",
        font_path=usefont,
        color="#FFFFFF",
        opacity=1.0,
        align="left",
        content=wl
    )

    # return maker.save(f"custom_result.jpg")
    return maker.save(f"yyt_sw_{int(round(time.time() * 1000))}.png")

#asyncio.run(yytsw({
#    "success": true,
#    "playername": "AerMini",
#    "uuid": "5601946c-0156-37ab-91e5-b75f5c78c730",
#    "data": {
#        "rank": 1,
#        "wins": 13,
#        "losses": 4,
#        "kills": 8,
#        "deaths": 4,
#        "elo": 1606,
#        "xp": 730,
#        "gamesPlayed": 17,
#        "escapes": 0,
#        "kdr": 2,
#        "winRate": 76.47
#    }
#}))