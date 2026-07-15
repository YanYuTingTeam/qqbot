import asyncio
import hashlib
import hmac
import json
import time
from typing import Optional, Any, Dict

try:
    import aiohttp
except ImportError:
    raise ImportError("pip install aiohttp first")


class JsonResp(dict):

    def __str__(self):
        return json.dumps(self, ensure_ascii=False, indent=2)


def _parse(text: str):
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        return text
    if isinstance(obj, dict):
        return JsonResp(obj)
    return obj


def _parse_with_status(text: str, status: int):
    parsed = _parse(text)
    if isinstance(parsed, (dict, list)):
        return parsed
    return {"_status": status, "_raw": text}


_ALGO_MAP = {
    "HmacMD5": "md5",
    "HmacSHA256": "sha256",
    "HmacSHA1": "sha1",
    "HmacSHA512": "sha512",
}


class AerMonitorClient:

    def __init__(
        self,
        base_url: str,
        salt: str = "**HIDDEN**",
        origin: str = "**HIDDEN**",
        algorithm: str = "HmacMD5",
        timeout: float = 10.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.salt = salt
        self.origin = origin
        self.algorithm = algorithm
        py_algo = _ALGO_MAP.get(algorithm)
        if py_algo is None:
            raise ValueError(f"unsupported algorithm: {algorithm}")
        self._py_algo = py_algo
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self._session = aiohttp.ClientSession(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self._session:
            await self._session.close()
            self._session = None

    def _sign(self, data: str) -> str:
        return hmac.new(
            self.salt.encode("utf-8"),
            data.encode("utf-8"),
            self._py_algo,
        ).hexdigest()

    def _build_headers(self, method: str, body: Optional[str]) -> Dict[str, str]:
        a = str(int(time.time() * 1000))
        if method.upper() in ("GET", "HEAD"):
            data = self.origin
        else:
            data = body if body is not None else ""
        b = self._sign(data)
        return {
            "a": a,
            "b": b,
            "Content-Type": "application/json; charset=utf-8",
        }

    def _full_url(self, url: str) -> str:
        if url.startswith("http://") or url.startswith("https://"):
            return url
        if not url.startswith("/"):
            url = "/" + url
        return self.base_url + url

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None:
            self._session = aiohttp.ClientSession(timeout=self.timeout)
        return self._session

    async def get(self, url: str) -> Dict[str, Any]:
        full = self._full_url(url)
        headers = self._build_headers("GET", None)
        session = await self._get_session()
        print(f"GET {full} with headers: {headers}")
        try:
            async with session.get(full, headers=headers) as resp:
                text = await resp.text()
                return _parse_with_status(text, resp.status)
        except Exception as e:
            return {"_status": 0, "_error": f"{type(e).__name__}: {e}"}

    async def post(self, url: str, body: Any) -> Dict[str, Any]:
        full = self._full_url(url)
        if isinstance(body, (dict, list)):
            body_str = json.dumps(body, ensure_ascii=False)
        else:
            body_str = str(body)
        headers = self._build_headers("POST", body_str)
        session = await self._get_session()
        print(f"POST {full} with headers: {headers} and body: {body_str}")
        try:
            async with session.post(full, headers=headers, data=body_str.encode("utf-8")) as resp:
                text = await resp.text()
                return _parse_with_status(text, resp.status)
        except Exception as e:
            return {"_status": 0, "_error": f"{type(e).__name__}: {e}"}

    async def put(self, url: str, body: Any) -> Dict[str, Any]:
        full = self._full_url(url)
        if isinstance(body, (dict, list)):
            body_str = json.dumps(body, ensure_ascii=False)
        else:
            body_str = str(body)
        headers = self._build_headers("PUT", body_str)
        session = await self._get_session()
        try:
            async with session.put(full, headers=headers, data=body_str.encode("utf-8")) as resp:
                text = await resp.text()
                return _parse_with_status(text, resp.status)
        except Exception as e:
            return {"_status": 0, "_error": f"{type(e).__name__}: {e}"}

    async def delete(self, url: str, body: Any = None) -> Dict[str, Any]:
        full = self._full_url(url)
        if isinstance(body, (dict, list)):
            body_str = json.dumps(body, ensure_ascii=False)
        elif body is None:
            body_str = ""
        else:
            body_str = str(body)
        headers = self._build_headers("DELETE", body_str)
        session = await self._get_session()
        try:
            async with session.delete(full, headers=headers, data=body_str.encode("utf-8")) as resp:
                text = await resp.text()
                return _parse_with_status(text, resp.status)
        except Exception as e:
            return {"_status": 0, "_error": f"{type(e).__name__}: {e}"}

    async def close(self):
        if self._session:
            await self._session.close()
            self._session = None


_default: Optional[AerMonitorClient] = None


def configure(
    base_url: str,
    salt: str = "**HIDDEN**",
    origin: str = "**HIDDEN**",
    algorithm: str = "HmacMD5",
    timeout: float = 10.0,
) -> AerMonitorClient:
    global _default
    _default = AerMonitorClient(base_url, salt, origin, algorithm, timeout)
    return _default


_DEFAULTS = dict(
    base_url="",
    salt="**HIDDEN**",
    origin="**HIDDEN**",
    algorithm="HmacMD5",
    timeout=10.0,
)


def get_default() -> AerMonitorClient:
    global _default
    if _default is None:
        _default = AerMonitorClient(**_DEFAULTS)
    return _default


async def get(url: str) -> Dict[str, Any]:
    return await get_default().get(url)


async def post(url: str, body: Any) -> Dict[str, Any]:
    return await get_default().post(url, body)


async def put(url: str, body: Any) -> Dict[str, Any]:
    return await get_default().put(url, body)


async def delete(url: str, body: Any = None) -> Dict[str, Any]:
    return await get_default().delete(url, body)


async def close():
    if _default is not None:
        await _default.close()


def sync_get(url: str) -> Dict[str, Any]:
    return _run_sync(lambda c: c.get(url))


def sync_post(url: str, body: Any) -> Dict[str, Any]:
    return _run_sync(lambda c: c.post(url, body))


def sync_put(url: str, body: Any) -> Dict[str, Any]:
    return _run_sync(lambda c: c.put(url, body))


def sync_delete(url: str, body: Any = None) -> Dict[str, Any]:
    return _run_sync(lambda c: c.delete(url, body))


def _run_sync(coro_factory):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            raise RuntimeError(
                "sync_*() cannot be called from a running event loop; "
                "use the async get/post/put/delete with await instead"
            )
    except RuntimeError as e:
        if "There is no current event loop" in str(e) or "no running event loop" in str(e):
            pass
        else:
            raise

    async def _runner():
        client = get_default()
        try:
            return await coro_factory(client)
        finally:
            await client.close()

    return asyncio.run(_runner())


def _cli():
    import argparse
    parser = argparse.ArgumentParser(description="AerServerMonitor API client")
    parser.add_argument("--base", default="http://127.0.0.1:8765", help="api base url")
    parser.add_argument("--salt", default="**HIDDEN**", help="hmac salt")
    parser.add_argument("--origin", default="**HIDDEN**", help="hmac origin (used as data for GET)")
    parser.add_argument("--algo", default="HmacMD5", help="hmac algorithm")
    parser.add_argument("method", choices=["get", "post", "put", "delete"])
    parser.add_argument("url", help="path or full url, e.g. /api/player")
    parser.add_argument("--body", default=None, help="request body (json string)")
    args = parser.parse_args()

    configure(args.base, salt=args.salt, origin=args.origin, algorithm=args.algo)

    async def run():
        try:
            if args.method == "get":
                resp = await get(args.url)
            elif args.method == "post":
                body = json.loads(args.body) if args.body else {}
                resp = await post(args.url, body)
            elif args.method == "put":
                body = json.loads(args.body) if args.body else {}
                resp = await put(args.url, body)
            else:
                body = json.loads(args.body) if args.body else None
                resp = await delete(args.url, body)
            print(json.dumps(resp, ensure_ascii=False, indent=2))
        finally:
            await close()

    asyncio.run(run())


if __name__ == "__main__":
    _cli()