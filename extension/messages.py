import re
from typing import Optional

AT_PATTERN = re.compile(r"<@([^>]+)>")
def getAt(raw_text: str) -> Optional[str]:
    """
    解析单条艾特格式: <@{OPENID}>
    返回大写openid；没有匹配返回 None
    """
    match = AT_PATTERN.search(raw_text)
    if not match:
        return None
    openid = match.group(1)
    return openid.upper()


def getAtall(raw_text: str) -> list[str]:
    """
    提取文本中全部艾特 <@{xxx}>，返回全部大写openid列表
    """
    matches = AT_PATTERN.findall(raw_text)
    return [s.upper() for s in matches]