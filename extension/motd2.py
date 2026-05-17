import aiohttp

async def motd(host: str, port: int = 25565, timeout=10):
    # 这个API貌似也被限同时3请求了 而且还出现了获取不到多行motd的问题
    url = f"https://mcapi.us/server/status?ip={host}{'&port='+str(port) if port != 25565 else ''}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=timeout) as resp:
                data = await resp.json()
        if data.get("online", False):
            return {
                "status": "online",
                "host": host,
                "port": port,
                "players": {
                    "online": data.get("players", {}).get("now", 0),
                    "max": data.get("players", {}).get("max", 0)
                },
                "version": {
                    "name": data.get("server", {}).get("name") or "Unknown",
                    "protocol": data.get("server", {}).get("protocol", 0)
                },
                "motd_clean": data.get("motd") or "",
                "motd_html": data.get("motd_html") or "",
                "favicon_url": data.get("favicon") or "",
                "raw": data
            }
        return {
            "status": "offline",
            "host": host,
            "port": port,
            "players": {"online": 0, "max": 0},
            "version": {"name": "Unknown", "protocol": 0},
            "motd_clean": "",
            "motd_html": "",
            "favicon_url": "",
            "raw": data
        }
    except Exception as e:
        print(f"motd {host}:{port} 失败 -> {str(e)}")
        return {
            "status": "offline",
            "host": host,
            "port": port,
            "players": {"online": 0, "max": 0},
            "version": {"name": "Unknown", "protocol": 0},
            "motd_clean": "",
            "motd_html": "",
            "favicon_url": "",
            "raw": {}
        }