
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from extension.picMaker import *

true = True

async def yytbwxp(json):
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    usefont = r"C:\Users\Administrator\Desktop\qqbot\font\MiSans_Demibold.ttf"
    test_bg_path = "assets/bwbgxp.png"
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

    if json["data"]["bowuse"] == 0:
        bs = "0%"
    else:
        bs = str(round(json["data"]["bowHit"]/json["data"]["bowuse"]*100, 2))+"%"

    bowMiss = int(json["data"]["bowuse"])-int(json["data"]["bowhit"])

    maker.text(
        x="16.5%",
        y="23.5%",
        size="72px",
        font_path=usefont,
        color="#FFFFFF",
        opacity=1.0,
        align="left",
        content=json["playername"]
    )
    maker.text(
        x="16.5%",
        y="32.5%",
        size="64px",
        font_path=usefont,
        color="#FFFFFF",
        opacity=1.0,
        align="left",
        content=get_current_time()
    )
    maker.text(
        x="42%",
        y="10.2%",
        size="56px",
        font_path=usefont,
        color="#FFFFFF",
        opacity=1.0,
        align="left",
        content=json["uuid"]
    )
    maker.text(
        x="16.5%",
        y="47.8%",
        size="96px",
        font_path=usefont,
        color="#FFFFFF",
        opacity=1.0,
        align="left",
        content=json["data"]["kills"]
    )
    maker.text(
        x="16.5%",
        y="56.05%",
        size="96px",
        font_path=usefont,
        color="#FFFFFF",
        opacity=1.0,
        align="left",
        content=json["data"]["deaths"]
    )

    maker.text(
        x="16.5%",
        y="64.3%",
        size="96px",
        font_path=usefont,
        color="#FFFFFF",
        opacity=1.0,
        align="left",
        content=kd
    )

    maker.text(
        x="16.5%",
        y="72.5%",
        size="96px",
        font_path=usefont,
        color="#FFFFFF",
        opacity=1.0,
        align="left",
        content=json["data"]["destroyedBeds"]
    )

    maker.text(
        x="18.8%",
        y="80.7%",
        size="96px",
        font_path=usefont,
        color="#FFFFFF",
        opacity=1.0,
        align="left",
        content=bp
    )

    maker.text(
        x="48%",
        y="23.3%",
        size="96px",
        font_path=usefont,
        color="#FFFFFF",
        opacity=1.0,
        align="left",
        content=json["data"]["rank"]
    )

    maker.text(
        x="48%",
        y="31.6%",
        size="96px",
        font_path=usefont,
        color="#FFFFFF",
        opacity=1.0,
        align="left",
        content=json["data"]["score"]
    )
    maker.text(
        x="48%",
        y="47.8%",
        size="96px",
        font_path=usefont,
        color="#FFFFFF",
        opacity=1.0,
        align="left",
        content=json["data"]["gamesPlayed"]
    )
    maker.text(
        x="48%",
        y="56.05%",
        size="96px",
        font_path=usefont,
        color="#FFFFFF",
        opacity=1.0,
        align="left",
        content=json["data"]["wins"]
    )
    maker.text(
        x="48%",
        y="64.3%",
        size="96px",
        font_path=usefont,
        color="#FFFFFF",
        opacity=1.0,
        align="left",
        content=json["data"]["loses"]
    )
    maker.text(
        x="48%",
        y="72.5%",
        size="96px",
        font_path=usefont,
        color="#FFFFFF",
        opacity=1.0,
        align="left",
        content=wl
    )
    maker.text(
        x="52.4%",
        y="80.5%",
        size="96px",
        font_path=usefont,
        color="#FFFFFF",
        opacity=1.0,
        align="left",
        content=json["data"]["mvps"]
    )
    maker.text(
        x="79%",
        y="23.5%",
        size="96px",
        font_path=usefont,
        color="#FFFFFF",
        opacity=1.0,
        align="left",
        content=json["data"]["level"]
    )

    maker.text(
        x="81.1%",
        y="31.5%",
        size="96px",
        font_path=usefont,
        color="#FFFFFF",
        opacity=1.0,
        align="left",
        content=json["data"]["levelScore"]
    )
    maker.text(
        x="79%",
        y="47.8%",
        size="96px",
        font_path=usefont,
        color="#FFFFFF",
        opacity=1.0,
        align="left",
        content=json["data"]["bowuse"]
    )
    maker.text(
        x="79%",
        y="56.05%",
        size="96px",
        font_path=usefont,
        color="#FFFFFF",
        opacity=1.0,
        align="left",
        content=json["data"]["bowhit"]
    )
    maker.text(
        x="79%",
        y="64.3%",
        size="96px",
        font_path=usefont,
        color="#FFFFFF",
        opacity=1.0,
        align="left",
        content=bowMiss
    )
    maker.text(
        x="81.3%",
        y="72.5%",
        size="96px",
        font_path=usefont,
        color="#FFFFFF",
        opacity=1.0,
        align="left",
        content=bs
    )
    maker.text(
        x="79%",
        y="80.75%",
        size="96px",
        font_path=usefont,
        color="#FFFFFF",
        opacity=1.0,
        align="left",
        content=json["data"]["QMan"]
    )

    # return maker.save(f"custom_result.jpg")
    return maker.save(f"yyt_bw_{int(round(time.time() * 1000))}.png")

#yytbw({
#        "success": true,
#        "uuid": "5601946c-0156-37ab-91e5-b75f5c78c730",
#        "playername": "AerMini",
#        "data": {
#            "kills": 11,
#            "deaths": 3,
#            "wins": 10,
#            "loses": 3,
#            "score": 412,
#            "destroyedBeds": 18,
#            "kdr": 3.67,
#            "gamesPlayed": 13,
#            "winRate": 76.92,
#            "rank": 3,
#            "QMan": 0,
#            "bowuse": 0,
#            "bowHit": 0,
#            "bowMiss": 0,
#            "mvps": 0,
#            "level": "青铜",
#            "levelScore": 1000
#        }
#    })