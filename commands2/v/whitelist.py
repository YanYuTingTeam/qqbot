from typing import List
from botpy.message import GroupMessage  
import sys
import os
import importlib
import ast  # 用于安全解析配置文件

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.sendMessage import sendMessage

# 超管配置（只有超管能执行白名单管理命令）
SUPER_ADMIN_OPENID = "290967913F063AF2E8FB3FDE3B012DBC"  # 超管OI
# 配置文件实际路径（需和v.config模块对应）
current_dir = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE_PATH = os.path.join(current_dir, "config.py")

# 读取配置文件内容
def read_config_file():
    """读取config.py文件内容，返回字符串"""
    if not os.path.exists(CONFIG_FILE_PATH):
        raise FileNotFoundError(f"配置文件不存在：{CONFIG_FILE_PATH}")
    with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
        return f.read()

# 写入配置文件内容
def write_config_file(content: str):
    """将修改后的内容写入config.py"""
    with open(CONFIG_FILE_PATH, "w", encoding="utf-8") as f:
        f.write(content)

# 解析whitelist变量
def parse_whitelist(config_content: str):
    """从配置文件内容中解析出whitelist列表"""
    # 查找whitelist定义行
    lines = config_content.split("\n")
    whitelist_line = ""
    line_num = -1
    for i, line in enumerate(lines):
        if line.strip().startswith("whitelist ="):
            whitelist_line = line
            line_num = i
            break
    if not whitelist_line:
        raise ValueError("配置文件中未找到whitelist变量定义")
    
    # 安全解析列表（避免eval风险）
    whitelist_str = whitelist_line.split("=", 1)[1].strip()
    try:
        whitelist = ast.literal_eval(whitelist_str)
        if not isinstance(whitelist, list):
            raise TypeError("whitelist必须是列表类型")
        return whitelist, line_num
    except Exception as e:
        raise ValueError(f"解析whitelist失败：{e}")

# 白名单管理核心逻辑（适配 args = [add/del, openid]）
async def handle_command(args: List[str], message: GroupMessage) -> str:
    # ========== 1. 动态加载配置（复用鉴权基础） ==========
    run_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # 项目根目录
    sys.path.insert(0, run_path)
    config_path = "commands2.v.config"  # 对应commands/v/config.py模块
    if config_path in sys.modules:
        del sys.modules[config_path]
    config = importlib.import_module(config_path)

    # ========== 2. 超管鉴权（只有超管能执行） ==========
    current_openid = message.author.member_openid
    if current_openid != SUPER_ADMIN_OPENID:
        await sendMessage.text("你没有权限使用这个命令", message)
        return

    # ========== 3. 解析参数（适配 args = [add/del, openid]） ==========
    # 命令格式：/v whitelist add <oi> → args = [add, oi]
    #          /v whitelist del <oi> → args = [del, oi]
    #          /v whitelist → args = []
    if len(args) < 1 or args[0] not in ["add", "del"]:
        await sendMessage.text("""WHITELIST HELP\n\n/v whitelist add <oi> - 添加白名单\n/v whitelist del <oi> - 删除白名单""", message)
        return

    action = args[0]  # add/del（第一个参数是操作类型）
    target_openid = args[1] if len(args) >=2 else ""

    # 参数校验（oi不能为空且长度≥8）
    if not target_openid or len(target_openid) < 8:
        await sendMessage.text("oi非法", message)
        return

    # ========== 4. 读取并修改白名单 ==========
    try:
        # 读取配置文件
        config_content = read_config_file()
        # 解析当前白名单
        whitelist, line_num = parse_whitelist(config_content)
        lines = config_content.split("\n")

        # 执行添加/删除操作
        if action == "add":
            if target_openid in whitelist:
                await sendMessage.text(f"oi {target_openid[:4]}* 已在白名单中", message)
                return
            whitelist.append(target_openid)
            tip = "添加成功"
        else:  # del
            if target_openid not in whitelist:
                await sendMessage.text(f"oi {target_openid[:4]}* 不在白名单", message)
                return
            whitelist.remove(target_openid)
            tip = "删除成功"

        # ========== 5. 持久化修改（写入配置文件） ==========
        # 重新生成whitelist行（保持格式整洁）
        new_whitelist_line = f"whitelist = {whitelist}"
        lines[line_num] = new_whitelist_line
        new_config_content = "\n".join(lines)
        write_config_file(new_config_content)

        # ========== 6. 刷新配置模块 + 反馈结果 ==========
        # 强制刷新config模块，确保后续命令立即生效
        if config_path in sys.modules:
            del sys.modules[config_path]
        importlib.import_module(config_path)

        # 发送成功提示（隐藏完整OI，只显示前4位）
        await sendMessage.text(f"白名单{tip}\noi {target_openid[:4]}*\n白名单总数：{len(whitelist)}", message)

    except FileNotFoundError as e:
        await sendMessage.text(f"配置文件不存在：{e}", message)
    except ValueError as e:
        await sendMessage.text(f"配置文件解析失败：{e}", message)
    except Exception as e:
        await sendMessage.text(f"操作失败：{str(e)}", message)