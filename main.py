import asyncio
import sys
import os
import traceback
import botpy
from app.api_server import start_api_server
from web_viewer import start_web_viewer
from extension.request import configure
from events.group_message import patch
from listeners.msg_log import handle_msg_log
from listeners.cmd_router import route_command
from listeners.msg_bus import publish as publish_message

configure(
    base_url="",
    salt="**HIDDEN**",
    origin="**HIDDEN**",
    algorithm="HmacSHA256",
)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(CURRENT_DIR)
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)
patch()

class MyBot(botpy.Client):
    async def on_ready(self):
        print(f"机器人「{self.robot.name}」已上线，开始监听事件...")

    async def on_group_message_create(self, message):
        result = route_command(message)
        if not result:
            await publish_message(message)

async def main():
    intents = botpy.Intents(public_messages=True)
    bot = MyBot(intents=intents)
    await start_api_server(port=18080)
    await start_web_viewer(port=18081)
    await bot.start(appid="**HIDDEN**", secret="**HIDDEN**")

if __name__ == "__main__":
    print(f"Python 版本: {sys.version}")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n机器人已手动终止，停止监听")
    except Exception as e:
        traceback.print_exc()
        print(f"运行出错：{e}")