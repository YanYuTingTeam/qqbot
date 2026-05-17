import asyncio
import re
import os
import botpy
import importlib
from botpy.message import GroupMessage
import sys
from urllib.parse import quote
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from app.sendMessage import sendMessage

class MyBot(botpy.Client):
    async def on_ready(self):
        print(f"机器人「{self.robot.name}」已上线，开始监听事件...")

    def parse_command(self, raw_content: str) -> dict:
        """
        解析用户命令.\n
        例如: \n
        /abw bw => command: abw, args:["bw"]\n
        yyt top bw 2 => command: yyt, args:["top","bw","2"]\n
        返回格式: \n
        {"command":command,"args":[args]}
        """
        content = re.sub(r"^@.*?\s", "", raw_content).strip()
        
        if not content:
            return {"command": "help", "args": []}
        
        if content.startswith("/"):
            content = content[1:].strip()
        
        parts = re.split(r"\s+", content)
        command = parts[0] if parts else ""
        args = parts[1:] if len(parts) > 1 else []
        
        return {
            "command": command.lower(),
            "args": args
        }

    async def on_group_at_message_create(self, message: GroupMessage):
        """
        
        """   
        parse_result = self.parse_command(message.content)
        command = parse_result["command"]
        args = parse_result["args"]

        if not command:
            return
        await self.MessageHandle(command, args, message)

    async def MessageHandle(self, command, args, message: GroupMessage) -> str:
        if not args:
            sub_command = "main"
            sub_args = []
        else:
            sub_command = args[0]
            sub_args = args[1:]
        try:
            run_path = os.getcwd()
            #module_path = f"commands.{command}.{sub_command}"
            #module = importlib.import_module(module_path)
            sys.path.insert(0, run_path)
            api_module_path = f"commands.{command}.{sub_command}"
            if api_module_path in sys.modules:
                del sys.modules[api_module_path]
            api_module = importlib.import_module(api_module_path)
            await api_module.handle_command(sub_args, message)

        except ImportError as e:
            if sub_command == "main":
                await sendMessage.text(f"未知命令 /{command}",message)
            else:
                if "No module named" in str(e):
                    await sendMessage.text(f"功能不存在 {sub_command}@{command}",message)
                else:
                    await sendMessage.text(f"引用 {sub_command}@{command} 时，因其内部错误而未能成功\ndetail: {str(e)}",message)
        except AttributeError:
            await sendMessage.text(f"{'main' if sub_command == 'main' else f'{sub_command}'}@{command} 未能处理 handle_command",message)
        except Exception as e:
            await sendMessage.text(f"执行{f' {sub_command}' if sub_command != 'main' else ''}@{command} 出错：{str(e)}",message)

async def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    loop = asyncio.get_event_loop()
    asyncio.set_event_loop(loop)
    intents = botpy.Intents(public_messages=True)
    bot = MyBot(intents=intents)
    await bot.start(appid="**HIDDEN**", secret="**HIDDEN**")

if __name__ == "__main__":
    import asyncio
    print(sys.version)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n机器人已手动终止，停止监听")
    except Exception as e:
        print(f"运行出错：{e}")