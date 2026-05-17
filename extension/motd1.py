import aiohttp

async def motd(host: str, port: int = 25565, timeout=10):
    # 这个API貌似被限同时3请求了
    url = f"https://uapis.cn/api/v1/game/minecraft/serverstatus?server={host}{":"+str(port) if port != 25565 else ""}"
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
                    "online": data.get("players", 0),
                    "max": data.get("max_players", 0)
                },
                "version": {
                    "name": data.get("version", "Unknown"),
                    "protocol": 0
                },
                "motd_clean": data.get("motd_clean", ""),
                "motd_html": data.get("motd_html", ""),
                "favicon_url": data.get("favicon_url", ""),
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