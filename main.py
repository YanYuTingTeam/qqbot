import asyncio
import re
import os
import sys
import importlib
import inspect
import botpy
from botpy.message import GroupMessage
from urllib.parse import quote
from app.sendMessage import sendMessage

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(CURRENT_DIR)
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)


class MyBot(botpy.Client):
    async def on_ready(self):
        print(f"机器人「{self.robot.name}」已上线，开始监听事件...")

    def parse_command(self, raw_content: str) -> dict:
        """
        解析用户命令.
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
            
        api_module_path = f"commands.{command}.{sub_command}"
        loop = asyncio.get_running_loop()
        try:
            def load_module():
                if api_module_path in sys.modules:
                    del sys.modules[api_module_path]
                return importlib.import_module(api_module_path)
            api_module = await loop.run_in_executor(None, load_module)
            if inspect.iscoroutinefunction(api_module.handle_command):
                await api_module.handle_command(sub_args, message)
            else:
                await loop.run_in_executor(None, api_module.handle_command, sub_args, message)

        except ImportError as e:
            if sub_command == "main":
                await sendMessage.text(f"未知命令 /{command}", message)
            else:
                if "No module named" in str(e):
                    await sendMessage.text(f"功能不存在 {sub_command}@{command}", message)
                else:
                    await sendMessage.text(f"引用 {sub_command}@{command} 时，因其内部错误而未能成功\ndetail: {str(e)}", message)
        except AttributeError:
            await sendMessage.text(f"{'main' if sub_command == 'main' else f'{sub_command}'}@{command} 未能处理 handle_command", message)
        except Exception as e:
            await sendMessage.text(f"执行{f' {sub_command}' if sub_command != 'main' else ''}@{command} 出错：{str(e)}", message)


async def main():
    intents = botpy.Intents(public_messages=True)
    bot = MyBot(intents=intents)
    await bot.start(appid="**HIDDEN**", secret="**HIDDEN**")

if __name__ == "__main__":
    print(f"Python 版本: {sys.version}")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n机器人已手动终止，停止监听")
    except Exception as e:
        print(f"运行出错：{e}")