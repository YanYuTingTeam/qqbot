import asyncio
import json
import re
import struct
import time

import dns.asyncresolver


RAKNET_MAGIC = bytes.fromhex("00ffff00fefefefefdfdfdfd12345678")


def pack_varint(value):
    result = bytearray()
    value = int(value)

    if value < 0:
        raise ValueError("VarInt cannot be negative")

    while True:
        current = value & 0x7F
        value >>= 7
        if value:
            current |= 0x80
        result.append(current)
        if not value:
            return bytes(result)


async def read_varint(reader):
    value = 0

    for index in range(5):
        raw = await reader.read(1)
        if not raw:
            raise EOFError("Unexpected end of stream while reading VarInt")

        current = raw[0]
        value |= (current & 0x7F) << (7 * index)

        if not current & 0x80:
            return value

    raise ValueError("Invalid VarInt")


def clean_motd(data):
    parts = []

    if isinstance(data, dict):
        if "text" in data:
            parts.append(str(data["text"]))
        if "extra" in data:
            parts.append(clean_motd(data["extra"]))
    elif isinstance(data, list):
        for item in data:
            parts.append(clean_motd(item))
    elif data is not None:
        parts.append(str(data))

    text = "".join(parts)
    return re.sub(r"§[0-9a-zA-Z]", "", text)


def _hostname_without_port(host):
    if host.startswith("[") and "]" in host:
        return host[1:host.index("]")]

    if host.count(":") == 1:
        name, possible_port = host.rsplit(":", 1)
        if possible_port.isdigit():
            return name

    return host


async def getsrv(host, record="_minecraft._tcp"):
    domain = _hostname_without_port(host)
    query = "%s.%s" % (record, domain)

    try:
        resolver = dns.asyncresolver.Resolver(configure=False)
        resolver.nameservers = ["223.5.5.5"]
        resolver.timeout = 1.5
        resolver.lifetime = 1.5
        answers = await resolver.resolve(query, "SRV")

        # SRV records are ordered by priority. Weight selection is not needed
        # for a status request, so use the first record at the best priority.
        records = sorted(answers, key=lambda item: item.priority)
        if records:
            return str(records[0].target).rstrip("."), int(records[0].port)
    except Exception:
        pass

    return None, None


async def ping_java(host, port, timeout=3):
    writer = None

    async def request():
        nonlocal writer

        reader, writer = await asyncio.open_connection(host, port)
        host_bytes = host.encode("utf-8")

        # Handshake packet. The port is an unsigned big-endian short.
        handshake = (
            pack_varint(0)
            + pack_varint(47)
            + pack_varint(len(host_bytes))
            + host_bytes
            + struct.pack(">H", port)
            + pack_varint(1)
        )
        writer.write(pack_varint(len(handshake)) + handshake)

        status_request = pack_varint(0)
        writer.write(pack_varint(len(status_request)) + status_request)
        await writer.drain()

        await read_varint(reader)  # packet length
        packet_id = await read_varint(reader)
        if packet_id != 0:
            raise ValueError("Unexpected Java status packet id: %s" % packet_id)

        json_length = await read_varint(reader)
        body = bytearray()

        while len(body) < json_length:
            chunk = await reader.read(json_length - len(body))
            if not chunk:
                raise EOFError("Java status response ended early")
            body.extend(chunk)

        return json.loads(bytes(body).decode("utf-8"))

    try:
        return await asyncio.wait_for(request(), timeout=timeout)
    except Exception as exc:
        print("ping_java failed for %s:%s: %s" % (host, port, exc))
        return None
    finally:
        if writer is not None:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass


async def ping_be(host, port, timeout=5):
    """Query a Bedrock server using RakNet Unconnected Ping/Pong."""
    loop = asyncio.get_running_loop()
    response = loop.create_future()
    transport = None
    started = loop.time()

    class UdpProtocol(asyncio.DatagramProtocol):
        def datagram_received(self, data, addr):
            # Unconnected Pong: id, time, server GUID, magic, string length.
            if len(data) < 35:
                return
            if data[0] != 0x1C:
                return
            if data[17:33] != RAKNET_MAGIC:
                return
            if not response.done():
                response.set_result(data)

        def error_received(self, exc):
            if not response.done():
                response.set_exception(exc)

        def connection_lost(self, exc):
            if exc is not None and not response.done():
                response.set_exception(exc)

    def elapsed():
        return loop.time() - started

    try:
        transport, _ = await asyncio.wait_for(
            loop.create_datagram_endpoint(
                UdpProtocol,
                remote_addr=(host, port),
            ),
            timeout=timeout,
        )

        # Unconnected Ping = packet id + time + 16-byte magic + client GUID.
        request = (
            b"\x01"
            + struct.pack(">Q", int(time.time() * 1000))
            + RAKNET_MAGIC
            + struct.pack(">Q", 0)
        )
        transport.sendto(request)

        # Wake up as soon as a valid Pong arrives. Do not sleep for the whole
        # timeout after a response has already been received.
        packet = await asyncio.wait_for(response, timeout=timeout)

        name_length = struct.unpack_from(">H", packet, 33)[0]
        end = 35 + name_length
        if len(packet) < end:
            raise ValueError("Truncated Bedrock Pong server-info string")

        server_info = packet[35:end].decode("utf-8")
        fields = server_info.split(";")
        if len(fields) < 6:
            raise ValueError("Invalid Bedrock server-info field count")

        def field(index):
            return fields[index] if index < len(fields) else ""

        def integer(index, default=0):
            try:
                return int(field(index))
            except (TypeError, ValueError):
                return default

        result = {
            "brand": field(0),
            "motd": field(1),
            "agreement": integer(2),
            "version": field(3),
            "online": integer(4),
            "max": integer(5),
            "server_unique_id": field(6),
            "level_name": field(7),
            "gamemode": field(8),
        }
        return result, elapsed()
    except asyncio.TimeoutError:
        return None, elapsed()
    except Exception as exc:
        print("ping_be failed for %s:%s: %s" % (host, port, exc))
        return None, elapsed()
    finally:
        if transport is not None:
            transport.close()


async def motd(host, port=25565, platform=0):
    """
    Query a Minecraft server.

    platform: 0 for Java Edition, 1 for Bedrock Edition.
    """
    original_host = host
    original_port = port

    if platform == 0:
        # Java uses the conventional _minecraft._tcp SRV record. Honor an
        # explicitly supplied non-default port instead of overriding it.
        srv_host = srv_port = None
        if port == 25565:
            srv_host, srv_port = await getsrv(host, "_minecraft._tcp")

        real_host = srv_host or host
        real_port = srv_port if srv_host else port

        started = asyncio.get_running_loop().time()
        data = await ping_java(real_host, real_port)
        delay = round((asyncio.get_running_loop().time() - started) * 1000, 2)

        if data:
            players = data.get("players") or {}
            version = data.get("version") or {}
            return {
                "status": "online",
                "host": original_host,
                "relhost": real_host,
                "port": original_port if original_port != 25565 else "",
                "relport": real_port,
                "players": {
                    "online": players.get("online", 0),
                    "max": players.get("max", 0),
                },
                "version": {
                    "name": version.get("name", "Unknown"),
                    "protocol": version.get("protocol", 0),
                },
                "motd_clean": clean_motd(data.get("description", "")),
                "motd_html": "",
                "favicon_url": data.get("favicon", ""),
                "delay": delay,
                "raw": data,
            }

        return {
            "status": "offline",
            "host": original_host,
            "relhost": real_host,
            "port": original_port if original_port != 25565 else "",
            "relport": real_port,
            "players": {"online": 0, "max": 0},
            "version": {"name": "Unknown", "protocol": 0},
            "motd_clean": "",
            "motd_html": "",
            "favicon_url": "",
            "delay": delay,
            "raw": {},
        }

    # Bedrock status is UDP. Do not apply the Java _minecraft._tcp record.
    real_host = host
    real_port = 19132 if port == 25565 else port
    display_port = "" if port in (25565, 19132) else port
    data, cost = await ping_be(real_host, real_port)
    delay = round(cost * 1000, 2)

    if data:
        return {
            "status": "online",
            "host": original_host,
            "relhost": real_host,
            "port": display_port,
            "relport": real_port,
            "players": {
                "online": data.get("online", 0),
                "max": data.get("max", 0),
            },
            "version": {
                "name": data.get("version", "Unknown"),
                "protocol": data.get("agreement", 0),
            },
            "motd_clean": clean_motd(data.get("motd", "")),
            "motd_html": "",
            "level_name": data.get("level_name", ""),
            "gamemode": data.get("gamemode", ""),
            "server_unique_id": data.get("server_unique_id", ""),
            "favicon_url": "",
            "delay": delay,
            "raw": data,
        }

    return {
        "status": "offline",
        "host": original_host,
        "relhost": real_host,
        "port": display_port,
        "relport": real_port,
        "players": {"online": 0, "max": 0},
        "version": {"name": "Unknown", "protocol": 0},
        "motd_clean": "",
        "motd_html": "",
        "level_name": "",
        "gamemode": "",
        "server_unique_id": "",
        "favicon_url": "",
        "delay": delay,
        "raw": {},
    }
