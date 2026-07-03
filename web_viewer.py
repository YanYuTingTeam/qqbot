import os
import sys
import json
import asyncio
from aiohttp import web

SCRIPT_ABS = os.path.abspath(__file__)
ROOT_DIR = os.path.dirname(SCRIPT_ABS)
sys.path.insert(0, ROOT_DIR)

from app.api_server import REQUEST_LOGS


HTML_PAGE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>API 请求查看</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0d1117;color:#c9d1d9;font-family:Consolas,Monaco,'Courier New',monospace;font-size:13px}
.hdr{background:#161b22;border-bottom:1px solid #30363d;padding:10px 20px;display:flex;justify-content:space-between;align-items:center;position:sticky;top:0;z-index:100}
.hdr h1{font-size:15px;color:#58a6ff;font-weight:600;letter-spacing:.3px}
.hdr-left{display:flex;align-items:center;gap:10px}
.badge-new{background:#f85149;color:#fff;font-size:10px;padding:0 8px;border-radius:10px;cursor:pointer;display:none}
.badge-new.show{display:inline-block;animation:pulse 1s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
.ctrls{display:flex;gap:10px;align-items:center}
.ctrls button{background:#21262d;color:#c9d1d9;border:1px solid #30363d;padding:5px 14px;border-radius:6px;cursor:pointer;font-size:12px;font-family:inherit;transition:background .15s}
.ctrls button:hover{background:#30363d}
.ctrls button.on{background:#238636;border-color:#238636;color:#fff}
.stats{display:flex;gap:14px;font-size:12px;color:#8b949e}
.stats b{color:#c9d1d9;font-weight:500}
.s-ok{color:#3fb950!important}
.s-err{color:#f85149!important}
.flt{background:#0d1117;border:1px solid #30363d;color:#c9d1d9;padding:4px 10px;border-radius:6px;font-size:12px;width:180px;font-family:inherit}
.flt:focus{outline:none;border-color:#58a6ff}
.chk{display:flex;align-items:center;gap:4px;font-size:12px;color:#8b949e;user-select:none}
.chk input{accent-color:#58a6ff;cursor:pointer}
table{width:100%;border-collapse:collapse}
thead th{background:#161b22;color:#8b949e;text-transform:uppercase;font-size:10.5px;letter-spacing:.6px;padding:7px 12px;text-align:left;border-bottom:1px solid #30363d;position:sticky;top:42px;z-index:50}
td{padding:5px 12px;border-bottom:1px solid #21262d;vertical-align:middle;cursor:default}
tbody tr{transition:background .1s}
tbody tr:hover{background:#161b22}
tbody tr.expanded{background:#161b22}
tbody tr.row-error{background:#f8514910}
tbody tr.row-error:hover{background:#f8514918}
.mtd{font-weight:700;padding:2px 8px;border-radius:4px;font-size:11px;letter-spacing:.3px}
.mtd.POST{background:#1f6feb33;color:#58a6ff}
.mtd.GET{background:#23863633;color:#3fb950}
.st{font-weight:700}
.st.c2{color:#3fb950}.st.c4{color:#d29922}.st.c5{color:#f85149}
.pth{max-width:320px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.tm{color:#8b949e;white-space:nowrap;font-size:12px}
.cs{color:#8b949e;font-size:12px}
.dp{display:none}
tbody tr.expanded+tr .dp{display:block}
.dpn{background:#0d1117;border:1px solid #30363d;border-radius:8px;margin:2px 12px 6px;overflow:hidden}
.tabs{display:flex;border-bottom:1px solid #30363d;background:#161b22}
.tab{padding:7px 18px;cursor:pointer;color:#8b949e;font-size:12px;border-bottom:2px solid transparent;transition:color .15s}
.tab:hover{color:#c9d1d9}
.tab.on{color:#58a6ff;border-bottom-color:#58a6ff}
.tbc{padding:12px;max-height:420px;overflow:auto}
.tbc pre{white-space:pre-wrap;word-break:break-all;font-size:12px;line-height:1.6;margin:0}
.jk{color:#79c0ff}.js{color:#a5d6ff}.jn{color:#f2cc60}.jb{color:#ff7b72}.jnull{color:#8b949e}
.empty{text-align:center;padding:80px 20px;color:#484f58;font-size:14px}
.cpn{display:inline-block;padding:1px 7px;border-radius:10px;font-size:10px;background:#21262d;color:#8b949e;margin-left:6px}
.hl{color:#7ee787;font-weight:600}
.hdr-info{font-size:11px;color:#484f58;margin-top:2px}
.copy-btn{background:#21262d;color:#8b949e;border:1px solid #30363d;padding:2px 10px;border-radius:4px;cursor:pointer;font-size:11px;font-family:inherit;float:right;transition:color .15s}
.copy-btn:hover{color:#c9d1d9}
</style>
</head>
<body>
<div class="hdr">
  <div class="hdr-left">
    <h1>API 请求查看</h1>
    <span class="badge-new" id="nb" onclick="scrollBot()">新请求</span>
  </div>
  <div class="ctrls">
    <input class="flt" id="fi" placeholder="过滤路径..." />
    <label class="chk"><input type="checkbox" id="as" checked />自动滚动</label>
    <div class="stats">
      总计 <b id="st">0</b>
      &nbsp;成功 <b class="s-ok" id="sk">0</b>
      &nbsp;错误 <b class="s-err" id="se">0</b>
    </div>
    <button onclick="doClear()">清空</button>
    <button id="pb" onclick="doPause()">暂停</button>
  </div>
</div>
<div style="overflow-x:auto">
<table>
<thead><tr>
  <th style="width:48px">#</th>
  <th style="width:138px">时间</th>
  <th style="width:65px">方法</th>
  <th>路径</th>
  <th style="width:60px">状态</th>
  <th style="width:72px">耗时</th>
</tr></thead>
<tbody id="tb"></tbody>
</table>
<div class="empty" id="em">等待请求...</div>
</div>
<script>
var allLogs=[],lastId=0,paused=false,filter='';
function esc(s){if(!s)return'';return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;')}
function fmtJson(s){
  if(!s)return'<span class="jnull">(empty)</span>';
  try{var o=JSON.parse(s);s=JSON.stringify(o,null,2)}catch(e){}
  return hlJson(esc(s));
}
function hlJson(s){
  s=s.replace(/(&quot;(\\u[\da-fA-F]{4}|\\[^u]|[^\\&])*?&quot;)(\s*:)?/g,function(m){
    var c=m.indexOf(':')>-1?'jk':'js';
    return'<span class="'+c+'">'+m+'</span>';
  });
  s=s.replace(/\b(true|false)\b/g,'<span class="jb">$1</span>');
  s=s.replace(/\bnull\b/g,'<span class="jnull">null</span>');
  s=s.replace(/\b(\d+\.?\d*)\b/g,'<span class="jn">$1</span>');
  return s;
}
function fmtInfo(l){
  var h='';
  var hdrs=l.req_headers||{};
  for(var k in hdrs){h+='  '+esc(k)+': '+esc(hdrs[k])+'\n'}
  return '客户端: '+esc(l.client||'-')+
    '\n查询参数: '+(l.query?esc(l.query):'(none)')+
    '\n请求体大小: '+(l.req_body?l.req_body.length:0)+' bytes'+
    '\n响应体大小: '+(l.resp_body?l.resp_body.length:0)+' bytes'+
    (l.error?'\n错误: '+esc(l.error):'')+
    '\n\n请求头:\n'+h;
}
function render(){
  var tb=document.getElementById('tb'),em=document.getElementById('em');
  var fl=filter.toLowerCase();
  var arr=allLogs.filter(function(l){return !fl||l.path.toLowerCase().indexOf(fl)>-1});
  if(!arr.length){tb.innerHTML='';em.style.display='block';return}
  em.style.display='none';
  var s='';
  for(var i=0;i<arr.length;i++){
    var l=arr[i];
    var sc=l.status>=500?'c5':l.status>=400?'c4':'c2';
    var ec=l.error?' row-error':'';
    var qs=l.query?'?'+esc(l.query):'';
    s+='<tr class="'+ec+'" data-id="'+l.id+'" onclick="tog('+l.id+')">'+
      '<td>'+l.id+'</td>'+
      '<td class="tm">'+esc(l.time)+'</td>'+
      '<td><span class="mtd '+l.method+'">'+l.method+'</span></td>'+
      '<td class="pth" title="'+esc(l.path)+qs+'">'+esc(l.path)+(qs?'<span class="cpn">'+esc(l.query)+'</span>':'')+'</td>'+
      '<td class="st '+sc+'">'+l.status+'</td>'+
      '<td class="cs">'+l.cost_ms+'ms</td></tr>'+
      '<tr id="d-'+l.id+'" style="display:none"><td colspan="6" style="padding:0"><div class="dpn">'+
      '<div class="tabs">'+
        '<div class="tab on" onclick="stab(this,\''+l.id+'\',\'rb\')">请求体</div>'+
        '<div class="tab" onclick="stab(this,\''+l.id+'\',\'rsb\')">响应体</div>'+
        '<div class="tab" onclick="stab(this,\''+l.id+'\',\'inf\')">详情</div>'+
      '</div>'+
      '<div class="tbc" id="c-rb-'+l.id+'"><button class="copy-btn" onclick="event.stopPropagation();copyTxt(\''+l.id+'\',\'rb\')">复制</button><pre>'+fmtJson(l.req_body)+'</pre></div>'+
      '<div class="tbc" id="c-rsb-'+l.id+'" style="display:none"><button class="copy-btn" onclick="event.stopPropagation();copyTxt(\''+l.id+'\',\'rsb\')">复制</button><pre>'+fmtJson(l.resp_body)+'</pre></div>'+
      '<div class="tbc" id="c-inf-'+l.id+'" style="display:none"><pre>'+fmtInfo(l)+'</pre></div>'+
      '</div></td></tr>';
  }
  tb.innerHTML=s;
}
function tog(id){
  var r=document.querySelector('tr[data-id="'+id+'"]');
  var d=document.getElementById('d-'+id);
  if(d.style.display==='none'){
    document.querySelectorAll('[id^="d-"]').forEach(function(el){if(el.id!=='d-'+id)el.style.display='none'});
    document.querySelectorAll('tr.expanded').forEach(function(el){el.classList.remove('expanded')});
    d.style.display='';r.classList.add('expanded');
  }else{
    d.style.display='none';r.classList.remove('expanded');
  }
}
function stab(tab,id,panel){
  var p=tab.parentElement;
  p.querySelectorAll('.tab').forEach(function(t){t.classList.remove('on')});
  tab.classList.add('on');
  ['rb','rsb','inf'].forEach(function(p2){
    document.getElementById('c-'+p2+'-'+id).style.display=p2===panel?'':'none';
  });
}
function copyTxt(id,src){
  var el=document.getElementById('c-'+src+'-'+id).querySelector('pre');
  var txt=el.textContent||el.innerText;
  navigator.clipboard.writeText(txt).then(function(){
    var btn=el.parentElement.querySelector('.copy-btn');
    btn.textContent='已复制';setTimeout(function(){btn.textContent='复制'},1200);
  });
}
function updStats(){
  document.getElementById('st').textContent=allLogs.length;
  document.getElementById('sk').textContent=allLogs.filter(function(l){return l.status<400}).length;
  document.getElementById('se').textContent=allLogs.filter(function(l){return l.status>=400}).length;
}
function scrollBot(){window.scrollTo(0,document.body.scrollHeight);document.getElementById('nb').classList.remove('show')}
function doClear(){
  fetch('/api/logs/clear',{method:'POST'}).then(function(){allLogs=[];lastId=0;render();updStats()});
}
function doPause(){
  paused=!paused;
  var b=document.getElementById('pb');
  b.textContent=paused?'继续':'暂停';
  b.classList.toggle('on',paused);
}
async function poll(){
  if(paused)return;
  try{
    var r=await fetch('/api/logs?since='+lastId);
    var nl=await r.json();
    if(nl.length>0){
      allLogs=allLogs.concat(nl);
      lastId=nl[nl.length-1].id;
      render();updStats();
      if(document.getElementById('as').checked){
        var atBot=(window.innerHeight+window.scrollY)>=document.body.offsetHeight-60;
        if(atBot){scrollBot()}else{document.getElementById('nb').classList.add('show')}
      }
    }
  }catch(e){console.error('poll err',e)}
}
document.getElementById('fi').addEventListener('input',function(e){filter=e.target.value;render()});
poll();setInterval(poll,1500);
</script>
</body>
</html>"""


async def handle_index(request):
    return web.Response(text=HTML_PAGE, content_type="text/html", charset="utf-8")


async def handle_logs(request):
    """增量拉取日志：?since=<id> 返回 id 之后的日志"""
    try:
        since = int(request.query.get("since", "0"))
    except ValueError:
        since = 0
    logs = [l for l in REQUEST_LOGS if l["id"] > since]
    return web.json_response(logs)


async def handle_logs_clear(request):
    """清空日志"""
    REQUEST_LOGS.clear()
    return web.json_response({"ok": True})


async def start_web_viewer(port: int = 18081):
    """启动 Web 查看平台（与 botpy 共用事件循环）"""
    app = web.Application()
    app.router.add_get("/", handle_index)
    app.router.add_get("/api/logs", handle_logs)
    app.router.add_post("/api/logs/clear", handle_logs_clear)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"[Viewer] 请求查看平台已启动: http://127.0.0.1:{port}")
    return runner


if __name__ == "__main__":
    async def _standalone():
        print("[Viewer] 独立模式启动（无 botpy，日志将为空）")
        await start_web_viewer(18081)
        print("[Viewer] 按 Ctrl+C 停止")
        await asyncio.Event().wait()

    try:
        asyncio.run(_standalone())
    except KeyboardInterrupt:
        print("\n[Viewer] 已停止")