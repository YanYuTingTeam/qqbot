import sqlite3
import os
import traceback
from datetime import datetime

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT_DIR, "db.sqlite")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ============ 时间解析 ============

def _parse_ts(ts_str: str) -> datetime:
    if not ts_str:
        return datetime.now()
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"):
        try:
            clean = ts_str.split("+")[0].split("Z")[0]
            return datetime.strptime(clean, fmt)
        except (ValueError, IndexError):
            continue
    return datetime.now()


# ============ 群号绑定 ============

def get_group_mapping(qq_group_id: str = "", botpy_group_openid: str = ""):
    """
    查询群号映射。
    传入任一侧的 ID，返回 {"qq_group_id": ..., "botpy_group_openid": ...} 或 None。
    """
    try:
        conn = get_conn()
        try:
            if qq_group_id:
                row = conn.execute(
                    "SELECT * FROM group_binding WHERE qq_group_id = ?", (qq_group_id,)
                ).fetchone()
            elif botpy_group_openid:
                row = conn.execute(
                    "SELECT * FROM group_binding WHERE botpy_group_openid = ?", (botpy_group_openid,)
                ).fetchone()
            else:
                return None
            return dict(row) if row else None
        finally:
            conn.close()
    except Exception as e:
        print(f"[DB] get_group_mapping 错误 (qq_group_id={qq_group_id}, botpy_group_openid={botpy_group_openid}): {e}")
        traceback.print_exc()
        raise


def _save_group_binding(qq_group_id: str, botpy_group_openid: str, conn=None):
    """写入群号映射（如果 conn 已传入则复用，否则自己创建）"""
    own_conn = conn is None
    if own_conn:
        conn = get_conn()
    try:
        conn.execute(
            """INSERT OR REPLACE INTO group_binding (qq_group_id, botpy_group_openid, created_at)
               VALUES (?, ?, datetime('now','localtime'))""",
            (qq_group_id, botpy_group_openid),
        )
        if own_conn:
            conn.commit()
    except Exception as e:
        print(f"[DB] _save_group_binding 错误 (qq_group_id={qq_group_id}, botpy_group_openid={botpy_group_openid}): {e}")
        traceback.print_exc()
        raise
    finally:
        if own_conn:
            conn.close()


# ============ 用户绑定 ============

def try_bind_from_botpy(botpy_group: str, member_openid: str,
                        content: str = "", timestamp: str = ""):
    """
    botpy 侧调用：已知 botpy_group_openid + member_openid，
    找 EPL 消息（有 qq_number）做匹配并绑定。
    返回绑定的 qq_number 或 None。
    """
    if not botpy_group or not member_openid:
        return None

    msg_dt = _parse_ts(timestamp)
    try:
        conn = get_conn()
        try:
            # 第一步：查已有的群号映射
            mapping = get_group_mapping(botpy_group_openid=botpy_group)
            epl_group = mapping["qq_group_id"] if mapping else None

            # 第二步：找 EPL 消息
            if epl_group:
                # 已知群号映射，直接在对应 EPL 群里找
                rows = conn.execute("""
                    SELECT message_id, qq_number, timestamp, content, group_id
                    FROM message_log
                    WHERE group_id = ? AND qq_number != '' AND member_openid = ''
                    ORDER BY timestamp DESC LIMIT 20
                """, (epl_group,)).fetchall()
            else:
                # 没有群号映射，跨群搜索：同内容 + 最近时间
                if not content:
                    return None
                rows = conn.execute("""
                    SELECT message_id, qq_number, timestamp, content, group_id
                    FROM message_log
                    WHERE qq_number != '' AND member_openid = '' AND content = ?
                    ORDER BY timestamp DESC LIMIT 10
                """, (content,)).fetchall()

            for row in rows:
                row_dt = _parse_ts(row["timestamp"])
                diff = abs((msg_dt - row_dt).total_seconds())

                # 5秒内不需内容匹配；30秒内需内容匹配
                content_match = bool(content and row["content"] and content == row["content"])
                if diff > 5 and not (diff <= 30 and content_match):
                    continue

                qq = row["qq_number"]
                found_epl_group = row["group_id"]

                # 建立/确认群号绑定
                if not epl_group:
                    _save_group_binding(found_epl_group, botpy_group, conn=conn)
                    epl_group = found_epl_group

                # 更新 EPL 消息：补上 member_openid
                conn.execute(
                    "UPDATE message_log SET member_openid = ? WHERE message_id = ? AND group_id = ?",
                    (member_openid, row["message_id"], epl_group),
                )
                # 更新 botpy 消息：补上 qq_number（该用户的所有未绑定消息）
                conn.execute(
                    "UPDATE message_log SET qq_number = ? WHERE group_id = ? AND member_openid = ? AND qq_number = ''",
                    (qq, botpy_group, member_openid),
                )
                # 写入 group_members 用户绑定
                _upsert_user_binding(conn, epl_group, qq, member_openid)
                conn.commit()
                return qq

            return None
        finally:
            conn.close()
    except Exception as e:
        print(f"[DB] try_bind_from_botpy 错误 (botpy_group={botpy_group}, member_openid={member_openid}): {e}")
        traceback.print_exc()
        raise


def try_bind_from_epl(epl_group: str, qq_number: str,
                      content: str = "", timestamp: str = ""):
    """
    EPL 侧调用（API handler 里用）：已知 epl_group_id + qq_number，
    找 botpy 消息（有 member_openid）做匹配并绑定。
    返回绑定的 member_openid 或 None。
    """
    if not epl_group or not qq_number:
        return None

    msg_dt = _parse_ts(timestamp)
    try:
        conn = get_conn()
        try:
            # 查群号映射
            mapping = get_group_mapping(qq_group_id=epl_group)
            botpy_group = mapping["botpy_group_openid"] if mapping else None

            # 找 botpy 消息
            if botpy_group:
                rows = conn.execute("""
                    SELECT message_id, member_openid, timestamp, content, group_id
                    FROM message_log
                    WHERE group_id = ? AND member_openid != '' AND qq_number = ''
                    ORDER BY timestamp DESC LIMIT 20
                """, (botpy_group,)).fetchall()
            else:
                if not content:
                    return None
                rows = conn.execute("""
                    SELECT message_id, member_openid, timestamp, content, group_id
                    FROM message_log
                    WHERE member_openid != '' AND qq_number = '' AND content = ?
                    ORDER BY timestamp DESC LIMIT 10
                """, (content,)).fetchall()

            for row in rows:
                row_dt = _parse_ts(row["timestamp"])
                diff = abs((msg_dt - row_dt).total_seconds())

                content_match = bool(content and row["content"] and content == row["content"])
                if diff > 5 and not (diff <= 30 and content_match):
                    continue

                openid = row["member_openid"]
                found_botpy_group = row["group_id"]

                # 建立群号绑定
                if not botpy_group:
                    _save_group_binding(epl_group, found_botpy_group, conn=conn)
                    botpy_group = found_botpy_group

                # 更新 botpy 消息：补上 qq_number
                conn.execute(
                    "UPDATE message_log SET qq_number = ? WHERE message_id = ? AND group_id = ?",
                    (qq_number, row["message_id"], botpy_group),
                )
                # 更新 EPL 消息：补上 member_openid
                conn.execute(
                    "UPDATE message_log SET member_openid = ? WHERE group_id = ? AND qq_number = ? AND member_openid = ''",
                    (openid, epl_group, qq_number),
                )
                _upsert_user_binding(conn, epl_group, qq_number, openid)
                conn.commit()
                return openid

            return None
        finally:
            conn.close()
    except Exception as e:
        print(f"[DB] try_bind_from_epl 错误 (epl_group={epl_group}, qq_number={qq_number}): {e}")
        traceback.print_exc()
        raise


def _upsert_user_binding(conn, epl_group: str, qq_number: str, member_openid: str):
    """在 group_members 中写入/更新 member_openid 绑定"""
    try:
        conn.execute(
            "UPDATE group_members SET member_openid = ? WHERE group_id = ? AND qq_number = ?",
            (member_openid, epl_group, qq_number),
        )
        conn.execute(
            """INSERT OR IGNORE INTO group_members
               (group_id, qq_number, member_openid, updated_at)
               VALUES (?, ?, ?, datetime('now','localtime'))""",
            (epl_group, qq_number, member_openid),
        )
    except Exception as e:
        print(f"[DB] _upsert_user_binding 错误 (epl_group={epl_group}, qq_number={qq_number}, member_openid={member_openid}): {e}")
        traceback.print_exc()
        raise


# ============ 查询接口 ============

def get_user_info(botpy_group_openid: str, member_openid: str) -> dict:
    """
    根据 botpy_group_openid + member_openid 查询用户信息。
    内部自动转换到 EPL 群号查询 group_members。
    如果尚未绑定会先尝试自动绑定。
    返回 dict {"qq_number", "nickname", "avatar_url", "group_card", ...} 或 None。
    """
    try:
        # 查群号映射
        mapping = get_group_mapping(botpy_group_openid=botpy_group_openid)
        epl_group = mapping["qq_group_id"] if mapping else None

        if epl_group:
            conn = get_conn()
            try:
                row = conn.execute(
                    "SELECT * FROM group_members WHERE group_id = ? AND member_openid = ?",
                    (epl_group, member_openid),
                ).fetchone()
                if row and row["qq_number"]:
                    return dict(row)
            finally:
                conn.close()

        # 没找到绑定，尝试自动绑定
        try_bind_from_botpy(botpy_group_openid, member_openid)

        # 再查一次
        mapping = get_group_mapping(botpy_group_openid=botpy_group_openid)
        if not mapping:
            return None
        epl_group = mapping["qq_group_id"]

        conn = get_conn()
        try:
            row = conn.execute(
                "SELECT * FROM group_members WHERE group_id = ? AND member_openid = ?",
                (epl_group, member_openid),
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()
    except Exception as e:
        print(f"[DB] get_user_info 错误 (botpy_group_openid={botpy_group_openid}, member_openid={member_openid}): {e}")
        traceback.print_exc()
        raise


def get_all_members(botpy_group_openid: str) -> list:
    """获取群全部成员列表（自动转换群号）"""
    try:
        mapping = get_group_mapping(botpy_group_openid=botpy_group_openid)
        if not mapping:
            return []
        epl_group = mapping["qq_group_id"]
        conn = get_conn()
        try:
            rows = conn.execute(
                "SELECT * FROM group_members WHERE group_id = ? ORDER BY qq_number",
                (epl_group,),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()
    except Exception as e:
        print(f"[DB] get_all_members 错误 (botpy_group_openid={botpy_group_openid}): {e}")
        traceback.print_exc()
        raise