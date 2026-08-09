from typing import List
from botpy.message import GroupMessage
import sys
import os
import random
import sqlite3
from datetime import datetime, date
import traceback

SCRIPT_ABS = os.path.abspath(__file__)
JRRP_DIR = os.path.dirname(SCRIPT_ABS)
COMMANDS_DIR = os.path.dirname(JRRP_DIR)
ROOT_DIR = os.path.dirname(COMMANDS_DIR)
DB_PATH = os.path.join(ROOT_DIR, "db.sqlite")
TABLE_LUCK = "jrrp"

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.sendMessage import sendMessage
from extension.messages import getAt

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    create_sql = f'''
        CREATE TABLE IF NOT EXISTS {TABLE_LUCK} (
            member_openid TEXT PRIMARY KEY,
            luck_num INTEGER NOT NULL,
            desc_text TEXT NOT NULL,
            first_query TEXT NOT NULL,
            last_query TEXT NOT NULL
        )
    '''
    cursor.execute(create_sql)
    try:
        cursor.execute(f"ALTER TABLE {TABLE_LUCK} ADD COLUMN desc_text TEXT NOT NULL DEFAULT ''")
    except sqlite3.OperationalError:
        pass
    conn.commit()
    conn.close()

async def handle_command(args: List[str], message: GroupMessage) -> str:
    import importlib
    run_path = os.getcwd()
    sys.path.insert(0, run_path)
    config_path = f"commands2.v.config"
    if config_path in sys.modules:
        del sys.modules[config_path]
    config = importlib.import_module(config_path)
    if message.author.member_openid not in config.whitelist:
        await sendMessage.text("你没有权限使用这个命令!",message)
        return
    try:
        user_id = getAt(message.content) or message.author.member_openid
        init_db()
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(f"DELETE FROM {TABLE_LUCK} WHERE member_openid = ?", (user_id,))
        conn.commit()
        conn.close()

        n = "\u200b\n"
        msg_text = f"{sendMessage.at(user_id)} 的人品数据已清除{n}再次发送/jrrp即可重新抽取今日人品"
        await sendMessage.markdown(msg_text, message)

    except Exception as e:
        traceback.print_exc()
        raise e