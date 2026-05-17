import aiohttp
import dns.asyncresolver

# 涉及的服务来自 https://github.com/BlackBEDevelopment/MCBE-Server-Motd
# 这里直接启动 tool/MCBE-Server-Motd.exe 来开启服务

async def getsrv(host: str):
    domain = host.split(':')[0]
    srv_query = f"_minecraft._tcp.{domain}"
    try:
        resolver = dns.asyncresolver.Resolver()
        answers = await resolver.resolve(srv_query, 'SRV')
        records = sorted(answers, key=lambda r: (r.priority, -r.weight))
        if records:
            target = str(records[0].target).rstrip('.')
            port = records[0].port
            return f"{target}:{port}"
    except Exception:
        return host
    return host

async def motd(host: str, port: int, timeout=10):
    api_url = f"http://localhost:8080/api/java?host={await getsrv(f"{host}{':'+str(port) if port != 25565 else ''}")}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, timeout=timeout) as resp:
                data = await resp.json()
        is_online = data.get("status") == "online" or data.get("online", 0) > 0
        
        if is_online:
            return {
                "status": "online",
                "host": host,
                "relhost":data.get("host", host),
                "port": port if port != 25565 else "",
                "relport": int(data.get("host", " :25565").split(":")[-1]) if ":" in data.get("host", "") else "",
                "players": {
                    "online": data.get("online", 0),
                    "max": data.get("max", 0)
                },
                "version": {
                    "name": data.get("version", "Unknown"),
                    "protocol": data.get("agreement", 0)
                },
                "motd_clean": data.get("motd", ""),
                "motd_html": data.get("motd", ""),
                "favicon_url": data.get("favicon", ""),
                "raw": data
            }

    except Exception as e:
        print(str(e))

    return {
        "status": "offline",
        "host": host,
        "port": 25565,
        "players": {"online": 0, "max": 0},
        "version": {"name": "Unknown", "protocol": 0},
        "motd_clean": "",
        "motd_html": "",
        "favicon_url": "",
        "raw": {}
    }