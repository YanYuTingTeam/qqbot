import json
from datetime import datetime
from app.api_server import record_botpy_message
from events.group_message import get_raw_payload

def handle_msg_log(message):
    try:
        raw = get_raw_payload(message.id)
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