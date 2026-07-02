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

DESC_RULES = [
    {"s": 0,  "o": 0, "c": [
        "⛔ 人品归零！今天请务必宅在家里！宇宙都在针对你！",
        "🛡️ 运气全无！今天什么都不宜做！连呼吸都要小心！",
        "💀 人品清零！今天请远离一切活动！床是你最好的朋友！"
    ]},
    {"s": 1,  "o": 14, "c": [
        "😱 人品惨淡！今天最好宅在家里！出门可能会踩到狗屎！",
        "💀 运气糟糕！今天万事要小心！喝水都可能被呛到！",
        "🚫 运势崩坏！今天不宜出门！在家躺着最安全！"
    ]},
    {"s": 15, "o": 29, "c": [
        "😰 人品较差，今天不宜做重要决定，投资理财请谨慎",
        "⚡ 运气不佳，今天要小心行事，走路不要看手机",
        "🏠 运势低迷，今天适合宅在家里，追番打游戏最安全"
    ]},
    {"s": 30, "o": 49, "c": [
        "🤔 人品一般，凡事多加小心，今天过马路要看红绿灯",
        "☔ 运气偏低，今天出门记得带伞，可能会遇到小麻烦",
        "🌙 运势不佳，今天适合低调行事，不要做重大决定"
    ]},
    {"s": 50, "o": 69, "c": [
        "😌 人品尚可，平平淡淡才是真，今天适合在家追剧吃零食",
        "🍃 运气一般，保持平常心就好，今天适合喝杯奶茶放松一下",
        "🌿 运势平稳，今天适合早睡早起，养生模式开启"
    ]},
    {"s": 70, "o": 84, "c": [
        "🍀 人品不错！今天点外卖超时商家会主动退款加送！",
        "🎈 运气良好！今天挤地铁一定有座位！上班不迟到！",
        "🌸 吉星高照！今天网购的快递都会提前到达！"
    ]},
    {"s": 85, "o": 94, "c": [
        "🎯 人品极佳！今天打游戏连胜！队友都夸你是大神！",
        "💎 运气超棒！今天吃火锅不会溅到衣服！干啥都顺心！",
        "🌈 福星降临！今天出门遇贵人！走路都能捡到宝贝！"
    ]},
    {"s": 95, "o": 99, "c": [
        "✨ 人品值爆表！今天你就是天选之子！出门捡钱不是梦！",
        "🌟 运气值MAX！今天买彩票可能中大奖！快去试试手气！",
        "🎊 福星高照！今天表白成功率100%！喜欢的人也会喜欢你！"
    ]},
    {"s": 100, "o": 100, "c": [
        "🏆 人品满分！今天就是你的幸运日！许什么愿都灵！",
        "👑 运气满值！今天做什么都会成功！买彩票必中！",
        "🌟 人品爆表！今天就是你的主场！全世界都在为你让路！"
    ]},
]

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

def get_today_str() -> str:
    return date.today().strftime("%Y-%m-%d")

def pick_desc(luck_val: int) -> str:
    for rule in DESC_RULES:
        if rule["s"] <= luck_val <= rule["o"]:
            return random.choice(rule["c"])
    return "未知运势"

async def handle_command(args: List[str], message: GroupMessage) -> str:
    try:
        user_id = message.author.member_openid
        init_db()
        today = get_today_str()
        now_full = datetime.now().strftime("%Y年%m月%d日 %H:%M")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        has_desc_col = False
        cursor.execute(f"PRAGMA table_info({TABLE_LUCK})")
        for col in cursor.fetchall():
            if col[1] == "desc_text":
                has_desc_col = True
                break

        query_sql = f"SELECT luck_num, first_query, last_query FROM {TABLE_LUCK} WHERE member_openid = ?"
        if has_desc_col:
            query_sql = f"SELECT luck_num, desc_text, first_query, last_query FROM {TABLE_LUCK} WHERE member_openid = ?"
        cursor.execute(query_sql, (user_id,))
        row = cursor.fetchone()

        if row is None:
            luck = random.randint(0, 100)
            desc = pick_desc(luck)
            if has_desc_col:
                cursor.execute(
                    f"INSERT INTO {TABLE_LUCK} (member_openid, luck_num, desc_text, first_query, last_query) VALUES (?, ?, ?, ?, ?)",
                    (user_id, luck, desc, now_full, now_full)
                )
            else:
                cursor.execute(
                    f"INSERT INTO {TABLE_LUCK} (member_openid, luck_num, first_query, last_query) VALUES (?, ?, ?, ?)",
                    (user_id, luck, now_full, now_full)
                )
            first_time = now_full
        else:
            if has_desc_col:
                old_luck, old_desc, first_date, last_date = row
            else:
                old_luck, first_date, last_date = row
                old_desc = ""

            last_day = last_date.split(" ")[0].replace("年", "-").replace("月", "-").replace("日", "")
            if last_day != today:
                luck = random.randint(0, 100)
                desc = pick_desc(luck)
                if has_desc_col:
                    cursor.execute(
                        f"UPDATE {TABLE_LUCK} SET luck_num = ?, desc_text = ?, last_query = ? WHERE member_openid = ?",
                        (luck, desc, now_full, user_id)
                    )
                else:
                    cursor.execute(
                        f"UPDATE {TABLE_LUCK} SET luck_num = ?, last_query = ? WHERE member_openid = ?",
                        (luck, now_full, user_id)
                    )
            else:
                luck = old_luck
                desc = pick_desc(old_luck) if not old_desc else old_desc
                if has_desc_col and not old_desc:
                    cursor.execute(
                        f"UPDATE {TABLE_LUCK} SET desc_text = ?, last_query = ? WHERE member_openid = ?",
                        (desc, now_full, user_id)
                    )
                else:
                    cursor.execute(
                        f"UPDATE {TABLE_LUCK} SET last_query = ? WHERE member_openid = ?",
                        (now_full, user_id)
                    )
            first_time = first_date

        conn.commit()
        conn.close()
        n = "\u200b\n"
        msg_text = f"{sendMessage.at(message.author.member_openid)} 的今日人品值是：{luck} 🎲{n}{n}{desc}{n}{n}📅 首次查询：{first_time}{n}⏰ 查询时间：{now_full}"
        await sendMessage.markdown(msg_text, message)

    except Exception as e:
        traceback.print_exc()
        raise e