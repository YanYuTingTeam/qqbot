import os
import asyncio
import importlib
import inspect
import re
import sqlite3
from datetime import datetime
from botpy.message import GroupMessage
import sys
from app.sendMessage import sendMessage

LIMIT_CHECK_SECONDS = 2
LIMIT_MAX_MSG = 3
LIMIT_BAN_SECONDS = 15
_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db.sqlite")
TABLE_RATE_LIMIT = "cmd_rate_limit"
TARGET_AT = "<@457F796388908D56C3BCC5B9C2FE773D>"

def init_rate_limit_db():
    conn = sqlite3.connect(_DB_PATH, check_same_thread=False)
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
    conn = sqlite3.connect(_DB_PATH, check_same_thread=False)
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

def parse_group_command(raw_content: str) -> dict:
    stripped = (raw_content or "").strip()
    is_at = bool(re.match(rf"^{re.escape(TARGET_AT)}", stripped))
    if is_at:
        content = re.sub(rf"^{re.escape(TARGET_AT)}\s*", "", stripped).strip()
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

async def _run_command(api_module_path: str, sub_command: str, sub_args: list, message: GroupMessage, is_at: bool):
    loop = asyncio.get_running_loop()
    def load_module():
        if api_module_path in sys.modules:
            del sys.modules[api_module_path]
        return importlib.import_module(api_module_path)

    try:
        api_module = await loop.run_in_executor(None, load_module)
    except ImportError as e:
        cmd_name = api_module_path.split('.')[1]
        if is_at:
            if sub_command == "main":
                await sendMessage.text(f"未知命令 /{cmd_name}", message)
            else:
                if "No module named" in str(e):
                    await sendMessage.text(f"功能不存在 {sub_command}@{cmd_name}", message)
                else:
                    await sendMessage.text(f"引用 {sub_command}@{cmd_name} 时，因其内部错误而未能成功\ndetail: {str(e)}", message)
        else:
            if sub_command != "main" and "No module named" not in str(e):
                await sendMessage.text(f"引用 {sub_command}@{cmd_name} 时，因其内部错误而未能成功\ndetail: {str(e)}", message)
        return

    handler = getattr(api_module, 'handle_command', None)
    if handler is None:
        await sendMessage.text(f"{'main' if sub_command == 'main' else sub_command}@{api_module_path.split('.')[1]} 未能处理 handle_command", message)
        return

    try:
        if inspect.iscoroutinefunction(handler):
            await handler(sub_args, message)
        else:
            await loop.run_in_executor(None, handler, sub_args, message)
    except Exception as e:
        await sendMessage.text(f"执行{f' {sub_command}' if sub_command != 'main' else ''}@{api_module_path.split('.')[1]} 出错：{str(e)}", message)

async def MessageHandle(command: str, args: list, message: GroupMessage) -> str:
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
    await _run_command(api_module_path, sub_command, sub_args, message, is_at=True)

async def MessageHandleAll(command: str, args: list, message: GroupMessage) -> str:
    if not args:
        sub_command = "main"
        sub_args = []
    else:
        sub_command = args[0]
        sub_args = args[1:]
    api_module_path = f"commands2.{command}.{sub_command}"
    openid = message.author.member_openid
    allow_run, ban_sec = check_user_limit(openid)
    if not allow_run:
        await sendMessage.text(f"你调用的太快了! 还需要等待 {ban_sec} 秒才能再次使用命令", message)
        return
    await _run_command(api_module_path, sub_command, sub_args, message, is_at=False)

def route_command(message: GroupMessage):
    result = parse_group_command(message.content)
    command = result["command"]
    args = result["args"]
    is_at = result["is_at"]
    if not command:
        return False
    if is_at:
        asyncio.create_task(MessageHandle(command, args, message))
    else:
        asyncio.create_task(MessageHandleAll(command, args, message))
    return True