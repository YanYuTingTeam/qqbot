
import time
import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from extension.picMaker import *

true = True

async def yytgbw(json):
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    usefont = r"C:\Users\Administrator\Desktop\qqbot\font\MiSans_Demibold.ttf"
    test_bg_path = "assets/bwbggun.png"
    maker = ImageMaker(test_bg_path)

    if json["data"]["deaths"] == 0:
        kd = "0"
    else:
        kd = round(json["data"]["kills"]/json["data"]["deaths"], 2)

    if json["data"]["gamesPlayed"] == 0:
        wl = "0%"
        bp = "0"
    else:
        wl = str(round(json["data"]["wins"]/json["data"]["gamesPlayed"]*100, 2))+"%"
        bp = round(json["data"]["destroyedBeds"]/json["data"]["gamesPlayed"], 2)

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
        y="29.3%", # -5.4
        size="96px",
        font_path=usefont,
        color="#FFFFFF",
        opacity=1.0,
        align="left",
        content=json["data"]["kills"]
    )
    maker.text(
        x="49%",
        y="39.6%",
        size="96px",
        font_path=usefont,
        color="#FFFFFF",
        opacity=1.0,
        align="left",
        content=json["data"]["deaths"]
    )

    maker.text(
        x="49%",
        y="49.8%",
        size="96px",
        font_path=usefont,
        color="#FFFFFF",
        opacity=1.0,
        align="left",
        content=kd
    )
    maker.text(
        x="49%",
        y="60.1%",
        size="96px",
        font_path=usefont,
        color="#FFFFFF",
        opacity=1.0,
        align="left",
        content=json["data"]["destroyedBeds"]
    )
    maker.text(
        x="50.5%",
        y="70.4%",
        size="96px",
        font_path=usefont,
        color="#FFFFFF",
        opacity=1.0,
        align="left",
        content=bp
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
        content=json["data"]["score"]
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
        content=json["data"]["loses"]
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
    return maker.save(f"yyt_gbw_{int(round(time.time() * 1000))}.png")

#asyncio.run(yytgbw({
#    "success": true,
#    "playername": "AerMini",
#    "uuid": "5601946c-0156-37ab-91e5-b75f5c78c730",
#    "data": {
#        "rank": 2,
#        "wins": 15,
#        "loses": 5,
#        "kills": 62,
#        "deaths": 97,
#        "score": 323,
#        "destroyedBeds": 9,
#        "kdr": 0.64,
#        "gamesPlayed": 20,
#        "winRate": 75
#    }
#}))