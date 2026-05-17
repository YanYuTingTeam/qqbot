import re
from typing import Union

def check_allowed_chars(s: str) -> bool:
    pattern = r'^[\u4e00-\u9fa5a-zA-Z0-9_]+$'
    return bool(re.match(pattern, s))

def songTime(value: Union[int, float], keep_ms: bool = False) -> str:
    # 格式化歌曲时间 ncm的duration是毫秒级的
    total_seconds = value / 1000
    minutes = int(total_seconds // 60)
    seconds = total_seconds % 60
    r = f"{minutes:02d}:{seconds:06.3f}"
    return r.replace(".", ":").replace(":", ".", 1) if keep_ms else r
    
def get_text_bbox(font_path, font_size, text):
    # 尝试解决制图时中英同行对齐的问题
    from PIL import ImageFont, ImageDraw, Image
    font_size_num = int(font_size.replace("px", "")) if "px" in font_size else int(font_size)
    font = ImageFont.truetype(font_path, font_size_num)
    img = Image.new('RGBA', (1, 1), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    bbox = draw.textbbox((0, 0), text, font=font)
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    offset_y = -bbox[1]
    return width, height, offset_y