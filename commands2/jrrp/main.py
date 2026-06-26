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

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    create_sql = f'''
        CREATE TABLE IF NOT EXISTS {TABLE_LUCK} (
            member_openid TEXT PRIMARY KEY,
            luck_num INTEGER NOT NULL,
            first_query TEXT NOT NULL,
            last_query TEXT NOT NULL
        )
    '''
    cursor.execute(create_sql)
    conn.commit()
    conn.close()

def get_today_str() -> str:
    day_str = date.today().strftime("%Y-%m-%d")
    return day_str

def get_luck_desc(luck_val: int) -> tuple[str, str]:
    if luck_val >= 90:
        return "🥳", "今日欧皇附体！出门有好运，抽奖必中，万事顺遂"
    elif luck_val >= 70:
        return "😊", "运气超棒，办事顺风顺水，适合出门游玩、收惊喜"
    elif luck_val >= 50:
        return "😌", "人品尚可，平平淡淡才是真，今天适合在家追剧吃零食"
    elif luck_val >= 30:
        return "😔", "今日运势一般，做事多留心，避免冲动决策"
    else:
        return "🥀", "今日非酋buff拉满，谨慎投资，少做高风险尝试"

async def handle_command(args: List[str], message: GroupMessage) -> str:
    try:
        user_id = message.author.member_openid
        init_db()
        today = get_today_str()
        now_full = datetime.now().strftime("%Y年%m月%d日 %H:%M")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        query_sql = f"SELECT luck_num, first_query, last_query FROM {TABLE_LUCK} WHERE member_openid = ?"
        cursor.execute(query_sql, (user_id,))
        row = cursor.fetchone()

        if row is None:
            luck = random.randint(0, 100)
            insert_sql = f'''
                INSERT INTO {TABLE_LUCK} (member_openid, luck_num, first_query, last_query)
                VALUES (?, ?, ?, ?)
            '''
            cursor.execute(insert_sql, (user_id, luck, now_full, now_full))
            first_time = now_full
        else:
            old_luck, first_date, last_date = row
            last_day = last_date.split(" ")[0].replace("年", "-").replace("月", "-").replace("日", "")
            if last_day != today:
                luck = random.randint(0, 100)
                update_sql = f'''
                    UPDATE {TABLE_LUCK} SET luck_num = ?, last_query = ? WHERE member_openid = ?
                '''
                cursor.execute(update_sql, (luck, now_full, user_id))
            else:
                luck = old_luck
                update_sql = f'''
                    UPDATE {TABLE_LUCK} SET last_query = ? WHERE member_openid = ?
                '''
                cursor.execute(update_sql, (now_full, user_id))
            first_time = first_date

        conn.commit()
        conn.close()

        face, desc = get_luck_desc(luck)
        msg_text = f"""你的今日人品值是：{luck} 🎲

{face} {desc}

📅 首次查询：{first_time}
⏰ 查询时间：{now_full}"""
        await sendMessage.text(msg_text, message)

    except Exception as e:
        traceback.print_exc()
        raise e
    return