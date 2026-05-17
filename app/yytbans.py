
import time
import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from extension.picMaker import *
from extension.string import *

true = True
false = False

async def yytbans(json, page, t):
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    usefont = r"C:\Users\Administrator\Desktop\qqbot\font\MiSans_Demibold.ttf"
    test_bg_path = "assets/yytban_nbg.png"
    maker = ImageMaker(test_bg_path)

    #maker.text(
    #    x="60%",
    #    y=f"{offset+336}px",
    #    size="80px",
    #    font_path=usefont,
    #    color="#FFFFFF",
    #    opacity=1.0,
    #    align="left",
    #    content=format_time(c['continue'])
    #)

    for i,c in enumerate(json["data"]):
        offset=i*200+30
        current_y=offset+336
        normal_height = get_text_bbox(usefont, "80px", "你")[1]
        text_width, text_height, text_offset_y = get_text_bbox(usefont, "80px", c["name"])
        text_y = current_y + (normal_height)/2 - (normal_height-text_height)/2 -40
        text_width, text_height2, text_offset_y = get_text_bbox(usefont, "80px", c["reason"])
        text_y2 = current_y + (normal_height)/2 - (normal_height-text_height2)/2 -40
        if c["reason"].find("volunteer") > -1:
            bcolor="#EDF398"
        elif c["reason"].find("-") > 1:
            bcolor="#9CEEEA"
        elif c["reason"] == "由于不正当的游戏行为被踢出游戏！":
            bcolor="#E2AAF8"
        else:
            bcolor="#FFFFFF"
        maker.color_block(
            x="50%",
            y=f"{offset+356}px",
            width="95pw",
            height="180px",
            color=bcolor,
            opacity=0.4,
            radius=[30,30,30,30],
        )
        maker.text(
            x="4%",
            y=f"{offset+336}px",
            size="80px",
            font_path=usefont,
            color="#FFFFFF",
            opacity=1.0,
            align="left",
            content=f"#{c['id']}"
        )
        maker.image(
            x="12%",
            y=f"{offset+356}px",
            width="96px",
            height="96px",
            radius=[18,18,18,18],
            img_path=r"C:\Users\Administrator\Desktop\qqbot\assets\steve.png"
        )
        maker.text(
            x="15%",
            y=f"{text_y}px",
            size="80px",
            font_path=usefont,
            color="#FFFFFF",
            opacity=1.0,
            align="left",
            content=c["name"]
        )
        maker.text(
            x="40%",
            y=f"{offset+336}px",
            size="80px",
            font_path=usefont,
            color="#FFFFFF",
            opacity=1.0,
            align="left",
            content=format_time(c['time'])
        )
        maker.text(
            x="60%",
            y=f"{offset+336}px",
            size="80px",
            font_path=usefont,
            color="#FFFFFF",
            opacity=1.0,
            align="left",
            content=format_time(c['continue'])
        )
        maker.text(
            x="80%",
            y=f"{text_y2}px",
            size="80px",
            font_path=usefont,
            color="#FFFFFF",
            opacity=1.0,
            align="left",
            content=f"{maker.truncate_text_by_width(c["reason"],640,"80px",usefont,"..") if maker.get_text_size("80px",usefont,c['reason'])[0] > 640 else c['reason']}"
        )

    # return maker.save(f"custom_result.jpg")
    return maker.save(f"yyt_bans_{int(round(time.time() * 1000))}.png")

#asyncio.run(yytbans({
#    "success": true,
#    "count": 439,
#    "page": 1,
#    "pageSize": 40,
#    "totalPages": 11,
#    "data": [
#        {
#            "id": 439,
#            "name": "ey_tianyan",
#            "uuid": "1d008938-e832-3e9b-8059-44777cd4201e",
#            "time": 1773051217976,
#            "continue": 1804587217976,
#            "reason": "volunteer:behaviour, reason:killaura",
#            "operater": "Console"
#        },
#        {
#            "id": 438,
#            "name": "ey_tianyan",
#            "uuid": "1d008938-e832-3e9b-8059-44777cd4201e",
#            "time": 1773050759344,
#            "continue": 2088410759344,
#            "reason": "volunteer:chat, reason:porn",
#            "operater": "Console"
#        },
#        {
#            "id": 437,
#            "name": "ey_tianyan",
#            "uuid": "1d008938-e832-3e9b-8059-44777cd4201e",
#            "time": 1773050747236,
#            "continue": 1804586747236,
#            "reason": "volunteer:behaviour, reason:killaura",
#            "operater": "Console"
#        }]}))