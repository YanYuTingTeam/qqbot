import asyncio
import struct
import json
import re
import dns.asyncresolver
from fastapi import FastAPI, Query

# 与motd4的不同是, 这个是自己开api在11452端口
# 源自 https://github.com/xdingya/Motd_For_Minecraft
# 从php转至python

app = FastAPI()
def pack_varint(d):
    o = b""
    while True:
        b = d & 0x7F
        d >>= 7
        o += struct.pack("B", b | (0x80 if d > 0 else 0))
        if d == 0:
            break
    return o

async def read_varint(reader):
    d = 0
    for i in range(5):
        b_raw = await reader.read(1)
        if not b_raw: return 0
        b = ord(b_raw)
        d |= (b & 0x7F) << (7 * i)
        if not (b & 0x80):
            break
    return d

def clean_motd(data):
    full_text = ""
    if isinstance(data, dict):
        full_text += data.get("text", "")
        if "extra" in data:
            if isinstance(data["extra"], list):
                for part in data["extra"]:
                    full_text += clean_motd(part)
            else:
                full_text += clean_motd(data["extra"])
    elif isinstance(data, list):
        for part in data:
            full_text += clean_motd(part)
    else:
        full_text += str(data)
    return re.sub(r'§[0-9a-zA-Z]', '', full_text)

async def getsrv(host: str):
    domain = host.split(':')[0]
    srv_query = f"_minecraft._tcp.{domain}"
    try:
        resolver = dns.asyncresolver.Resolver()
        resolver.timeout = 1.5
        resolver.lifetime = 1.5
        answers = await resolver.resolve(srv_query, 'SRV')
        records = sorted(answers, key=lambda r: (r.priority, -r.weight))
        if records:
            return str(records[0].target).rstrip('.'), records[0].port
    except:
        pass
    return None, None

async def ping_java(host: str, port: int, timeout=3):
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port), timeout=timeout
        )
        host_b = host.encode('utf-8')
        data = pack_varint(0) + pack_varint(47) + pack_varint(len(host_b)) + host_b + struct.pack("H", port) + pack_varint(1)
        writer.write(pack_varint(len(data)) + data)
        req = pack_varint(0)
        writer.write(pack_varint(len(req)) + req)
        await writer.drain()
        await read_varint(reader)
        await read_varint(reader)
        json_len = await read_varint(reader)
        body = b""
        while len(body) < json_len:
            chunk = await reader.read(json_len - len(body))
            if not chunk: break
            body += chunk
        writer.close()
        await writer.wait_closed()
        return json.loads(body.decode('utf-8'))
    except:
        return None

@app.get("/motd")
async def motd_api(host: str = Query(...), port: int = 25565):
    orig_host = host
    orig_port = port
    srv_host, srv_port = await getsrv(host)
    real_host = srv_host if srv_host else host
    real_port = srv_port if srv_host else port
    start_time = asyncio.get_event_loop().time()
    data = await ping_java(real_host, real_port)
    end_time = asyncio.get_event_loop().time()
    if data:
        return {
            "status": "online",
            "host": orig_host,
            "relhost": real_host,
            "port": orig_port if orig_port != 25565 else "",
            "relport": real_port,
            "players": {
                "online": data.get("players", {}).get("online", 0),
                "max": data.get("players", {}).get("max", 0)
            },
            "version": {
                "name": data.get("version", {}).get("name", "Unknown"),
                "protocol": data.get("version", {}).get("protocol", 0)
            },
            "motd_clean": clean_motd(data.get("description", "")),
            "motd_html": "",
            "favicon_url": data.get("favicon", ""),
            "delay": round((end_time - start_time) * 1000, 2),
            "raw": data
        }
    return {
        "status": "offline",
        "host": orig_host,
        "relhost": real_host,
        "port": orig_port if orig_port != 25565 else "",
        "relport": real_port,
        "players": {"online": 0, "max": 0},
        "version": {"name": "Unknown", "protocol": 0},
        "motd_clean": "",
        "motd_html": "",
        "favicon_url": "",
        "raw": {}
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=11452)