import asyncio
import re
import os
import sys
import importlib
import inspect
import botpy
from botpy.message import GroupMessage
from botpy.connection import ConnectionState
from urllib.parse import quote
import json
from datetime import datetime, date
import sqlite3
import traceback
from app.sendMessage import sendMessage
from app.api_server import start_api_server, record_botpy_message
from web_viewer import start_web_viewer

from extension.request import configure

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

LIMIT_CHECK_SECONDS = 1
LIMIT_MAX_MSG = 1
LIMIT_BAN_SECONDS = 10
DB_PATH = os.path.join(CURRENT_DIR, "db.sqlite")
TABLE_RATE_LIMIT = "cmd_rate_limit"

_raw_payloads = {}

def init_rate_limit_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cursor = conn.cursor()
    create_sql = f"""
    CREATE TABLE IF NOT EXISTS {TABLE_RATE_LIMIT} (
        member_openid TEXT PRIMARY KEY,
        cmd_timestamps TEXT NOT NULL,
        ban_until INTEGER NOT NULL DEFAULT 0
    )
    """
    cursor.execute(create_sql)
    conn.commit()
    conn.close()

def get_ts() -> int:
    return int(datetime.now().timestamp())

def check_user_limit(openid: str) -> tuple[bool, int]:
    init_rate_limit_db()
    now_ts = get_ts()
    window_start_ts = now_ts - LIMIT_CHECK_SECONDS
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute(f"SELECT cmd_timestamps, ban_until FROM {TABLE_RATE_LIMIT} WHERE member_openid = ?", (openid,))
    row = cursor.fetchone()
    ban_remain = 0
    ts_list = []
    if row:
        ts_str, ban_until = row
        if ban_until > now_ts:
            ban_remain = ban_until - now_ts
            conn.close()
            return False, ban_remain
        if ts_str.strip():
            ts_list = list(map(int, ts_str.split(",")))
    valid_ts = [t for t in ts_list if t >= window_start_ts]
    if len(valid_ts) < LIMIT_MAX_MSG:
        valid_ts.append(now_ts)
        new_ts_str = ",".join(map(str, valid_ts))
        cursor.execute(
            f"""INSERT OR REPLACE INTO {TABLE_RATE_LIMIT}
                (member_openid, cmd_timestamps, ban_until)
                VALUES (?, ?, ?)""",
            (openid, new_ts_str, 0)
        )
        conn.commit()
        conn.close()
        return True, 0
    ban_end_ts = now_ts + LIMIT_BAN_SECONDS
    cursor.execute(
        f"""INSERT OR REPLACE INTO {TABLE_RATE_LIMIT}
            (member_openid, cmd_timestamps, ban_until)
            VALUES (?, ?, ?)""",
        (openid, ",".join(map(str, valid_ts)), ban_end_ts)
    )
    conn.commit()
    conn.close()
    return False, LIMIT_BAN_SECONDS

def parse_group_message_create(self, payload):
    _message = GroupMessage(self.api, payload.get("id", None), payload.get("d", {}))
    msg_id = payload.get("id", "")
    if msg_id:
        _raw_payloads[msg_id] = payload.get("d", {})
    self._dispatch("group_message_create", _message)
ConnectionState.parse_group_message_create = parse_group_message_create

class MyBot(botpy.Client):
    async def on_ready(self):
        print(f"机器人「{self.robot.name}」已上线，开始监听事件...")
        init_rate_limit_db()

    def parse_group_command(self, raw_content: str) -> dict:
        stripped = (raw_content or "").strip()
        target_at = r"<@457F796388908D56C3BCC5B9C2FE773D>"
        is_at = bool(re.match(rf"^{re.escape(target_at)}", stripped))
        if is_at:
            content = re.sub(rf"^{re.escape(target_at)}\s*", "", stripped).strip()
        else:
            content = stripped

        if not content:
            return {"command": "", "args": [], "is_at": is_at}
        if content.startswith("/"):
            content = content[1:].strip()
        parts = re.split(r"\s+", content)
        command = parts[0] if parts else ""
        args = parts[1:] if len(parts) > 1 else []
        return {
            "command": command.lower(),
            "args": args,
            "is_at": is_at,
        }
    
    async def on_group_message_create(self, message: GroupMessage):
        try:
            raw = _raw_payloads.pop(message.id, {})
            ts = getattr(message, 'timestamp', None) or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            record_botpy_message(
                message_id=message.id,
                group_id=message.group_openid,
                member_openid=message.author.member_openid,
                content=message.content or "",
                timestamp=ts,
                raw_data=json.dumps(raw, ensure_ascii=False) if raw else ""
            )
        except Exception:
            pass

        result = self.parse_group_command(message.content)
        command = result["command"]
        args = result["args"]
        is_at = result["is_at"]
        if not command:
            return

        if is_at:
            await self.MessageHandle(command, args, message)
        else:
            await self.MessageHandleAll(command, args, message)

    async def MessageHandle(self, command, args, message: GroupMessage) -> str:
        openid = message.author.member_openid
        allow_run, ban_sec = check_user_limit(openid)
        if not allow_run:
            await sendMessage.text(f"你调用的太快了! 还需要等待 {ban_sec} 秒才能再次使用命令", message)
            return
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
            handler = getattr(api_module, 'handle_command', None)
            if handler is None:
                await sendMessage.text(f"{'main' if sub_command == 'main' else sub_command}@{command} 未能处理 handle_command", message)
                return
            if inspect.iscoroutinefunction(handler):
                await handler(sub_args, message)
            else:
                await loop.run_in_executor(None, handler, sub_args, message)

        except ImportError as e:
            if sub_command == "main":
                await sendMessage.text(f"未知命令 /{command}", message)
            else:
                if "No module named" in str(e):
                    await sendMessage.text(f"功能不存在 {sub_command}@{command}", message)
                else:
                    await sendMessage.text(f"引用 {sub_command}@{command} 时，因其内部错误而未能成功\ndetail: {str(e)}", message)
        except Exception as e:
            await sendMessage.text(f"执行{f' {sub_command}' if sub_command != 'main' else ''}@{command} 出错：{str(e)}", message)

    async def MessageHandleAll(self, command, args, message: GroupMessage) -> str:
        if not args:
            sub_command = "main"
            sub_args = []
        else:
            sub_command = args[0]
            sub_args = args[1:]
            
        api_module_path = f"commands2.{command}.{sub_command}"
        loop = asyncio.get_running_loop()
        try:
            def load_module():
                if api_module_path in sys.modules:
                    del sys.modules[api_module_path]
                return importlib.import_module(api_module_path)
            api_module = await loop.run_in_executor(None, load_module)
            handler = getattr(api_module, 'handle_command', None)
            openid = message.author.member_openid
            allow_run, ban_sec = check_user_limit(openid)
            if not allow_run:
                await sendMessage.text(f"你调用的太快了! 还需要等待 {ban_sec} 秒才能再次使用命令", message)
                return
            if handler is None:
                await sendMessage.text(f"{'main' if sub_command == 'main' else sub_command}@{command} 未能处理 handle_command", message)
                return
            if inspect.iscoroutinefunction(handler):
                await handler(sub_args, message)
            else:
                await loop.run_in_executor(None, handler, sub_args, message)

        except ImportError as e:
            if sub_command == "main":
                return
            else:
                if "No module named" in str(e):
                    return
                else:
                    await sendMessage.text(f"引用 {sub_command}@{command} 时，因其内部错误而未能成功\ndetail: {str(e)}", message)
        except Exception as e:
            await sendMessage.text(f"执行{f' {sub_command}' if sub_command != 'main' else ''}@{command} 出错：{str(e)}", message)

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