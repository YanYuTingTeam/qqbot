import asyncio
import struct
import json
import re
import dns.asyncresolver
import time

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
        if not b_raw:
            return 0
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
            if not chunk:
                break
            body += chunk

        writer.close()
        await writer.wait_closed()
        return json.loads(body.decode('utf-8'))
    except Exception as e:
        print(e)
        return None


async def ping_be(host: str, port: int, timeout=5):
    try:
        loop = asyncio.get_running_loop()
        recv_data = None

        class UdpProtocol(asyncio.DatagramProtocol):
            def __init__(self):
                self.transport = None

            def connection_made(self, trans):
                self.transport = trans

            def datagram_received(self, data, addr):
                nonlocal recv_data
                recv_data = data
                self.transport.close()

            def error_received(self, exc):
                pass

        transport, protocol = await asyncio.wait_for(
            loop.create_datagram_endpoint(UdpProtocol, remote_addr=(host, port)),
            timeout=timeout
        )

        packet_id = b'\x01'
        client_send_time = struct.pack(">Q", int(time.time() * 1000))
        magic = bytes([0x00, 0xFF, 0xFF, 0x00, 0xFE, 0xFE, 0xFE, 0xFE, 0xFD, 0xFD, 0xFD, 0xFD])
        client_id = b'\x12\x34\x56\x78\x00'
        client_guid = struct.pack(">Q", 0)

        send_data = packet_id + client_send_time + magic + client_id + client_guid
        start_time = asyncio.get_event_loop().time()
        transport.sendto(send_data)

        await asyncio.sleep(timeout)
        end_time = asyncio.get_event_loop().time()
        transport.close()

        if recv_data is None or len(recv_data) < 33:
            return None, end_time - start_time

        server_info_raw = recv_data[33:]
        server_info_str = server_info_raw.decode('utf‑8')
        motd_data = server_info_str.split(";")

        result = {
            "motd": motd_data[1],
            "agreement": int(motd_data[2]),
            "version": motd_data[3],
            "online": int(motd_data[4]),
            "max": int(motd_data[5]),
            "server_unique_id": motd_data[6],
            "level_name": motd_data[7],
            "gamemode": motd_data[8]
        }
        return result, end_time - start_time
    except Exception as e:
        print(e)
        return None, 0


async def motd(host: str, port: int = 25565, platform: int = 0):
    """
    :param host: 服务器域名/IP
    :param port: 端口
    :param platform: 0=Java版, 1=Bedrock(基岩)版
    :return: 统一结构字典
    """
    orig_host = host
    orig_port = port
    srv_host, srv_port = await getsrv(host)
    real_host = srv_host if srv_host else host
    real_port = srv_port if srv_host else port

    if platform == 0:
        # Java
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
    else:
        # Bedrock 基岩版
        if orig_port == 25565:
            orig_port = 19132
        if real_port == 25565 and srv_host is None:
            real_port = 19132
        data, cost = await ping_be(real_host, real_port)
        delay = round(cost * 1000, 2)
        if data:
            return {
                "status": "online",
                "host": orig_host,
                "relhost": real_host,
                "port": orig_port if orig_port != 19132 else "",
                "relport": real_port,
                "players": {
                    "online": data.get("online", 0),
                    "max": data.get("max", 0)
                },
                "version": {
                    "name": data.get("version", "Unknown"),
                    "protocol": data.get("agreement", 0)
                },
                "motd_clean": clean_motd(data.get("motd", "")),
                "motd_html": "",
                "level_name": data.get("level_name", ""),
                "gamemode": data.get("gamemode", ""),
                "server_unique_id": data.get("server_unique_id", ""),
                "favicon_url": "",
                "delay": delay,
                "raw": data
            }
        return {
            "status": "offline",
            "host": orig_host,
            "relhost": real_host,
            "port": orig_port if orig_port != 19132 else "",
            "relport": real_port,
            "players": {"online": 0, "max": 0},
            "version": {"name": "Unknown", "protocol": 0},
            "motd_clean": "",
            "motd_html": "",
            "level_name": "",
            "gamemode": "",
            "server_unique_id": "",
            "favicon_url": "",
            "raw": {}
        }
