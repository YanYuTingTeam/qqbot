# =============== 调试脚本 ===============
# 保存为 debug_mcsm.py, 改底下 3 个配置项然后 python debug_mcsm.py 运行
import hmac, hashlib, time, requests, json

#  ↓↓↓  ↓↓↓
APIKEY   = "7ed0b2b4-efda-4c3d-ae8e-d4b290e5fac8"   # 比如 aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee
SALT     = "**HIDDEN**"
PROXY    = "https://**HIDDEN**.mcsm.mcyyt.cn"   # 你的 专属面板域名
PATH     = "/api/service/remote_service_instances"
PARAMS   = {"daemonId":"762cf478f80f463cbb2024281f346307","page":1,"page_size":200}
#  ↑↑↑  ↑↑↑

a = str(int(time.time() * 1000))
msg = APIKEY + a + PATH
b   = hmac.new(SALT.encode("utf-8"), msg.encode("utf-8"), hashlib.md5).hexdigest()

headers = {"X-API-Key": APIKEY, "a": a, "b": b}
print("===== 客户端请求信息 =====")
print(f"URL      = {PROXY}{PATH}?{'&'.join(f'{k}={v}' for k,v in PARAMS.items())}")
print(f"apikey   = {APIKEY[:8]}...(len={len(APIKEY)})")
print(f"salt     = {SALT!r}")
print(f"a (ms)   = {a}  (本地当前时间)")
print(f"sign_msg = {msg!r}")
print(f"b (sign) = {b}")
print(f"headers  = {headers}")
try:
    r = requests.get(PROXY + PATH, headers=headers, params=PARAMS, timeout=15, verify=False)
except Exception as e:
    print(f"\n===== requests 层异常 =====")
    print(repr(e))
    raise
print(f"\n===== HTTP 响应 =====")
print(f"status  = {r.status_code}")
print(f"headers = {dict(r.headers)}")
print(f"body    = {r.text[:800]}")
try:
    j = r.json()
    print(f"\n===== JSON 解析结果 =====")
    print(json.dumps(j, ensure_ascii=False, indent=2))
except Exception:
    pass