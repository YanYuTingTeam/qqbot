import os
import sys
import json
import sqlite3
import time
import traceback
from datetime import datetime
from aiohttp import web

SCRIPT_ABS = os.path.abspath(__file__)
ROOT_DIR = os.path.dirname(os.path.dirname(SCRIPT_ABS))
DB_PATH = os.path.join(ROOT_DIR, "db.sqlite")

# ============ 请求日志存储（供 web_viewer 读取）============
REQUEST_LOGS = []
MAX_LOGS = 500
_log_counter = 0


def _next_log_id():
    global _log_counter
    _log_counter += 1
    return _log_counter


# ============ 数据库初始化 ============

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def _safe_add_column(cursor, table, column, col_type, default=""):
    """如果列不存在则添加（用于兼容旧表）"""
    cursor.execute(f"PRAGMA table_info({table})")
    existing = [row[1] for row in cursor.fetchall()]
    if column not in existing:
        if default:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type} NOT NULL DEFAULT {default}")
        else:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")

def init_tables():
    conn = get_conn()
    c = conn.cursor()

    # ---- group_binding ----
    # 群号映射: EPL 的 qq_group_id (QQ群号) <-> botpy 的 botpy_group_openid
    c.execute('''CREATE TABLE IF NOT EXISTS group_binding (
        qq_group_id        TEXT PRIMARY KEY,
        botpy_group_openid TEXT NOT NULL UNIQUE,
        created_at         TEXT NOT NULL
    )''')

    # ---- group_members ----
    # 字段对应 Drea SDK 数_成员信息:
    #   群号->group_id, 用户号->qq_number, 昵称->nickname, 头像->avatar_url,
    #   群昵称->group_card, 加群时间->join_time, 角色->role(DR_角色类型_),
    #   性别->gender(DR_性别类型_), 等级->level
    c.execute('''CREATE TABLE IF NOT EXISTS group_members (
        group_id     TEXT NOT NULL,
        qq_number    TEXT NOT NULL,
        nickname     TEXT NOT NULL DEFAULT '',
        avatar_url   TEXT NOT NULL DEFAULT '',
        group_card   TEXT NOT NULL DEFAULT '',
        role         INTEGER NOT NULL DEFAULT 0,
        gender       INTEGER NOT NULL DEFAULT 0,
        level        INTEGER NOT NULL DEFAULT 0,
        join_time    TEXT NOT NULL DEFAULT '',
        member_openid TEXT NOT NULL DEFAULT '',
        updated_at   TEXT NOT NULL,
        PRIMARY KEY (group_id, qq_number)
    )''')
    # 兼容旧表：逐列补齐
    _safe_add_column(c, "group_members", "group_card",    "TEXT",    "''")
    _safe_add_column(c, "group_members", "gender",        "INTEGER", "0")
    _safe_add_column(c, "group_members", "level",         "INTEGER", "0")
    _safe_add_column(c, "group_members", "member_openid", "TEXT",    "''")
    # 旧表的 role 列可能是 TEXT，尝试转换（忽略失败）
    try:
        c.execute("ALTER TABLE group_members RENAME COLUMN role TO role_old")
        c.execute("ALTER TABLE group_members ADD COLUMN role INTEGER NOT NULL DEFAULT 0")
        c.execute("UPDATE group_members SET role = CAST(role_old AS INTEGER)")
        c.execute("ALTER TABLE group_members DROP COLUMN role_old")
    except Exception:
        pass

    # ---- message_log ----
    # EPL 侧写入: message_id, group_id, qq_number, nickname, content, timestamp, raw_data
    # botpy 侧写入: message_id, group_id, member_openid, content, timestamp, raw_data
    # 双方互补，用 INSERT OR IGNORE 避免主键冲突
    c.execute('''CREATE TABLE IF NOT EXISTS message_log (
        message_id     TEXT NOT NULL,
        group_id       TEXT NOT NULL,
        qq_number      TEXT NOT NULL DEFAULT '',
        member_openid  TEXT NOT NULL DEFAULT '',
        nickname       TEXT NOT NULL DEFAULT '',
        content        TEXT NOT NULL DEFAULT '',
        timestamp      TEXT NOT NULL,
        raw_data       TEXT NOT NULL DEFAULT '',
        PRIMARY KEY (message_id, group_id)
    )''')
    _safe_add_column(c, "message_log", "nickname",      "TEXT", "''")
    _safe_add_column(c, "message_log", "raw_data",      "TEXT", "''")
    _safe_add_column(c, "message_log", "member_openid", "TEXT", "''")

    conn.commit()
    conn.close()

# ============ EPL 上报接口 ============

async def post_message(request):
    """EPL 上报群消息（带 qq_number）"""
    try:
        data = await request.json()
    except Exception:
        return web.json_response({"ok": False, "msg": "invalid json"}, status=400)

    group_id = data.get("group_id", "")
    qq_number = str(data.get("qq_number", ""))
    message_id = data.get("message_id", "")
    nickname = data.get("nickname", "")
    content = data.get("content", "")
    timestamp = data.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    raw_data = data.get("raw_data", "")

    conn = get_conn()
    try:
        conn.execute(
            """INSERT OR IGNORE INTO message_log
               (message_id, group_id, qq_number, nickname, content, timestamp, raw_data)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (message_id, group_id, qq_number, nickname, content, timestamp, raw_data)
        )
        # 如果已存在（botpy 先写入了），则补填 qq_number 和 nickname
        conn.execute(
            """UPDATE message_log
               SET qq_number = CASE WHEN qq_number = '' THEN ? ELSE qq_number END,
                   nickname  = CASE WHEN nickname  = '' THEN ? ELSE nickname  END
               WHERE message_id = ? AND group_id = ?""",
            (qq_number, nickname, message_id, group_id)
        )
        conn.commit()
    finally:
        conn.close()

    # 尝试把这条 EPL 消息和 botpy 消息绑定
    try:
        from app.db_helper import try_bind_from_epl
        try_bind_from_epl(group_id, qq_number, content=content, timestamp=timestamp)
    except Exception as e:
        print(f"[API] post_message try_bind_from_epl 错误: {e}")
        traceback.print_exc()

    return web.json_response({"ok": True})

async def post_member_join(request):
    """EPL 上报成员加入"""
    try:
        data = await request.json()
    except Exception:
        return web.json_response({"ok": False, "msg": "invalid json"}, status=400)

    group_id = data.get("group_id", "")
    qq_number = str(data.get("qq_number", ""))
    nickname = data.get("nickname", "")
    avatar_url = data.get("avatar_url", "")
    group_card = data.get("group_card", "")
    role = int(data.get("role", 0))
    gender = int(data.get("gender", 0))
    level = int(data.get("level", 0))
    join_time = data.get("join_time", "")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_conn()
    try:
        conn.execute(
            """INSERT OR REPLACE INTO group_members
               (group_id, qq_number, nickname, avatar_url, group_card, role, gender, level, join_time, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (group_id, qq_number, nickname, avatar_url, group_card, role, gender, level, join_time or now, now)
        )
        conn.commit()
    finally:
        conn.close()

    return web.json_response({"ok": True})

async def post_member_leave(request):
    """EPL 上报成员退出"""
    try:
        data = await request.json()
    except Exception:
        return web.json_response({"ok": False, "msg": "invalid json"}, status=400)

    group_id = data.get("group_id", "")
    qq_number = str(data.get("qq_number", ""))

    conn = get_conn()
    try:
        conn.execute("DELETE FROM group_members WHERE group_id = ? AND qq_number = ?", (group_id, qq_number))
        conn.commit()
    finally:
        conn.close()

    return web.json_response({"ok": True})

async def post_refresh_members(request):
    """EPL 上报全量群成员列表（/refreshlist 触发后调用）"""
    try:
        data = await request.json()
    except Exception:
        return web.json_response({"ok": False, "msg": "invalid json"}, status=400)

    group_id = data.get("group_id", "")
    members = data.get("members", [])
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_conn()
    try:
        # 清除该群旧成员数据
        conn.execute("DELETE FROM group_members WHERE group_id = ?", (group_id,))
        # 批量插入
        rows = []
        for m in members:
            qq = str(m.get("qq_number", ""))
            nick = m.get("nickname", "")
            avatar = m.get("avatar_url", "")
            card = m.get("group_card", "")
            role = int(m.get("role", 0))
            gender = int(m.get("gender", 0))
            level = int(m.get("level", 0))
            join_time = m.get("join_time", "")
            rows.append((group_id, qq, nick, avatar, card, role, gender, level, join_time or now, now))
        conn.executemany(
            """INSERT OR REPLACE INTO group_members
               (group_id, qq_number, nickname, avatar_url, group_card, role, gender, level, join_time, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            rows
        )
        conn.commit()
    finally:
        conn.close()

    return web.json_response({"ok": True, "count": len(members)})

async def post_ping(request):
    """简单 ping 端点，EPL 用来验证 HTTP_POST 能否连通"""
    try:
        raw = await request.text()
    except Exception:
        raw = ""
    print(f"[API] /api/ping 收到请求, body长度={len(raw)}, 内容={raw[:200]}")
    return web.json_response({"ok": True, "pong": True, "body_len": len(raw), "body_preview": raw[:100]})


async def post_refresh_members_txt(request):
    """EPL 上报成员列表（纯文本管道符分隔格式，避免 EPL 循环内拼 JSON 的问题）

    格式: group_id|qq1|nick1|avatar1|card1|role1|gender1|level1|jointime1|qq2|...
    每个成员 8 个字段，第一个字段是 group_id
    """
    try:
        raw = await request.text()
    except Exception as e:
        print(f"[API] refresh_members_txt: 读取body失败: {e}")
        return web.json_response({"ok": False, "msg": "read body failed"}, status=400)

    print(f"[API] refresh_members_txt: 收到数据, 长度={len(raw)}, 前200字符: {raw[:200]}")

    parts = raw.split("|")
    print(f"[API] refresh_members_txt: split后段数={len(parts)}, 第1段(group_id)={parts[0] if parts else 'EMPTY'}")

    if len(parts) < 2:
        print(f"[API] refresh_members_txt: 段数不足2，返回invalid format")
        return web.json_response({"ok": False, "msg": "invalid format", "parts_count": len(parts)}, status=400)

    group_id = parts[0].strip()
    if not group_id:
        print(f"[API] refresh_members_txt: group_id为空！")
        return web.json_response({"ok": False, "msg": "empty group_id"}, status=400)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_conn()
    try:
        conn.execute("DELETE FROM group_members WHERE group_id = ?", (group_id,))
        rows = []
        # 每 8 个字段为一个成员：qq, nick, avatar, card, role, gender, level, jointime
        # i+7 是最后一个字段的索引，需要 i+7 < len(parts)，即 i+8 <= len(parts)
        for i in range(1, len(parts), 8):
            if i + 8 > len(parts):
                print(f"[API] refresh_members_txt: 最后一段不完整，剩余{len(parts) - i}个字段，跳过")
                break
            qq = parts[i].strip()
            if not qq:
                print(f"[API] refresh_members_txt: 跳过空qq号, i={i}")
                continue
            nick = parts[i + 1].strip()
            avatar = parts[i + 2].strip()
            card = parts[i + 3].strip()
            try:
                role = int(parts[i + 4])
            except (ValueError, IndexError):
                role = 0
            try:
                gender = int(parts[i + 5])
            except (ValueError, IndexError):
                gender = 0
            try:
                level = int(parts[i + 6])
            except (ValueError, IndexError):
                level = 0
            join_time = parts[i + 7].strip() or now
            rows.append((group_id, qq, nick, avatar, card, role, gender, level, join_time, now))

        print(f"[API] refresh_members_txt: 解析完成, group_id={group_id}, 有效成员数={len(rows)}")
        conn.executemany(
            """INSERT OR REPLACE INTO group_members
               (group_id, qq_number, nickname, avatar_url, group_card, role, gender, level, join_time, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            rows
        )
        conn.commit()
    except Exception as e:
        print(f"[API] post_refresh_members_txt 错误: {e}")
        traceback.print_exc()
        return web.json_response({"ok": False, "msg": str(e)}, status=500)
    finally:
        conn.close()

    return web.json_response({"ok": True, "count": len(rows)})

# ============ 查询接口（供 botpy 内部使用） ============

def get_member_info(group_id: str, qq_number: str):
    """根据群号+QQ号查成员信息，返回 dict 或 None"""
    try:
        conn = get_conn()
        try:
            row = conn.execute(
                "SELECT * FROM group_members WHERE group_id = ? AND qq_number = ?",
                (group_id, qq_number)
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()
    except Exception as e:
        print(f"[API] get_member_info 错误: {e}")
        traceback.print_exc()
        raise

def get_member_by_openid(group_id: str, member_openid: str):
    """根据群号+member_openid查成员信息（需要先建立映射）"""
    try:
        conn = get_conn()
        try:
            row = conn.execute(
                "SELECT * FROM group_members WHERE group_id = ? AND member_openid = ?",
                (group_id, member_openid)
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()
    except Exception as e:
        print(f"[API] get_member_by_openid 错误: {e}")
        traceback.print_exc()
        raise

def get_member_by_group(group_id: str):
    """获取群全部成员"""
    try:
        conn = get_conn()
        try:
            rows = conn.execute("SELECT * FROM group_members WHERE group_id = ?", (group_id,)).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()
    except Exception as e:
        print(f"[API] get_member_by_group 错误: {e}")
        traceback.print_exc()
        raise

def record_botpy_message(message_id: str, group_id: str, member_openid: str,
                         content: str, timestamp: str, raw_data: str = ""):
    """botpy 侧记录消息（带 member_openid），供 main.py 调用"""
    conn = get_conn()
    try:
        conn.execute(
            """INSERT OR IGNORE INTO message_log
               (message_id, group_id, member_openid, content, timestamp, raw_data)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (message_id, group_id, member_openid, content, timestamp, raw_data)
        )
        conn.commit()
    finally:
        conn.close()

    # 尝试把这条 botpy 消息和 EPL 消息绑定
    try:
        from app.db_helper import try_bind_from_botpy
        try_bind_from_botpy(group_id, member_openid, content=content, timestamp=timestamp)
    except Exception as e:
        print(f"[API] record_botpy_message try_bind_from_botpy 错误: {e}")
        traceback.print_exc()

# ============ 启动服务 ============

@web.middleware
async def access_log_middleware(request, handler):
    """访问日志中间件：记录完整请求/响应信息到 REQUEST_LOGS"""
    start = time.time()

    # 在 handler 读取前先缓存请求体
    req_body = ""
    if request.body_exists:
        try:
            req_body = await request.text()
        except Exception:
            pass

    resp_status = 500
    resp_body = ""
    error_msg = ""

    try:
        resp = await handler(request)
        resp_status = resp.status
        try:
            resp_body = getattr(resp, 'text', '') or ''
        except Exception:
            resp_body = ""
        return resp
    except Exception as e:
        error_msg = str(e)
        raise
    finally:
        cost_ms = (time.time() - start) * 1000
        entry = {
            "id": _next_log_id(),
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "method": request.method,
            "path": request.path,
            "query": request.query_string,
            "client": request.remote or "",
            "req_headers": dict(request.headers),
            "req_body": req_body[:50000],
            "status": resp_status,
            "resp_body": resp_body[:50000],
            "error": error_msg,
            "cost_ms": round(cost_ms, 1),
        }
        REQUEST_LOGS.append(entry)
        if len(REQUEST_LOGS) > MAX_LOGS:
            del REQUEST_LOGS[:-MAX_LOGS]
        # 控制台也打印一行摘要
        if error_msg:
            print(f"[API] {request.method} {request.path} -> 500 ({cost_ms:.1f}ms) ERROR: {error_msg}")
        else:
            print(f"[API] {request.method} {request.path} -> {resp_status} ({cost_ms:.1f}ms)")


def create_app():
    init_tables()
    app = web.Application(middlewares=[access_log_middleware])
    app.router.add_post("/api/message", post_message)
    app.router.add_post("/api/member_join", post_member_join)
    app.router.add_post("/api/member_leave", post_member_leave)
    app.router.add_post("/api/refresh_members", post_refresh_members)
    app.router.add_post("/api/refresh_members_txt", post_refresh_members_txt)
    app.router.add_post("/api/ping", post_ping)
    return app

async def start_api_server(port: int = 18080):
    """在后台启动 API 服务器，与 botpy 共用事件循环"""
    from botpy import logging as botpy_logging
    _log = botpy_logging.get_logger()
    app = create_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    _log.info(f"[API] HTTP 服务已启动，监听端口 {port}")
    return runner