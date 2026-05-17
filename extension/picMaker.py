from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageEnhance
import os
import requests
import re
from io import BytesIO
import datetime
from collections import deque
from typing import List, Tuple, Union

def get_current_time(format_str: str = "%Y年%m月%d日 %H:%M") -> str:
    """
    获取当前时间并格式化, 可以传入格式化格式.
    """
    current_time = datetime.datetime.now()
    formatted_time = current_time.strftime(format_str)
    return formatted_time

def format_time(timestamp: int = 0) -> str:
    """
    for yyt. 传入的应当是毫秒级, 返回 YYYY/mm/dd HH/MM/SS
    """
    if timestamp<1:
        return "永久不予解封"
    else:
        sec_timestamp = int(timestamp) / 1000
        dt_object = datetime.datetime.fromtimestamp(sec_timestamp)
        formatted_time = dt_object.strftime("%Y/%#m/%#d %H:%M:%S")
        return formatted_time

class ImageMaker:
    """
    绘图
    抄css. %和pw/ph的区别在于, %是根据当前传入的属性来判断父级是width或height
    """
    def __init__(self, bg_img_path: str):
        if not os.path.exists(bg_img_path):
            raise FileNotFoundError(f"文件不存在 -> {bg_img_path}")
        self.bg_img = Image.open(bg_img_path).convert("RGBA")
        self.img_width, self.img_height = self.bg_img.size
        self.draw = ImageDraw.Draw(self.bg_img, "RGBA")

    def _parse_unit(self, value: Union[str, int, float], unit_type: str) -> int:
        value_str = str(value).strip().lower()
        if re.match(r"^\d+(\.\d+)?$", value_str):
            return int(float(value_str))
        elif "%" in value_str:
            num = float(value_str.replace("%", "")) / 100
            return int(num * self.img_width) if unit_type in ["x", "width"] else int(num * self.img_height)
        elif "pw" in value_str:
            return int(float(value_str.replace("pw", "")) / 100 * self.img_width)
        elif "ph" in value_str:
            return int(float(value_str.replace("ph", "")) / 100 * self.img_height)
        elif "px" in value_str:
            return int(float(value_str.replace("px", "")))
        else:
            raise ValueError(f"单位错误 -> {value_str}")

    def _parse_color(self, color: Union[str, Tuple[int, int, int]], opacity: float = 1.0) -> Tuple[int, int, int, int]:
        opacity = max(0.0, min(1.0, opacity))
        alpha = int(opacity * 255)
        if isinstance(color, str) and color.startswith("#"):
            color = color.lstrip("#")
            color = ''.join([c*2 for c in color]) if len(color) == 3 else color
            return (int(color[0:2],16), int(color[2:4],16), int(color[4:6],16), alpha)
        elif isinstance(color, str) and color.startswith("rgb"):
            nums = re.findall(r"\d+", color)
            return (int(nums[0]), int(nums[1]), int(nums[2]), alpha)
        elif isinstance(color, (tuple, list)) and len(color) == 3:
            return (int(color[0]), int(color[1]), int(color[2]), alpha)
        else:
            raise ValueError(f"颜色格式错误 -> {color}")

    def _parse_anchor(self, x: Union[str, int, float], y: Union[str, int, float], 
                      width: int, height: int, align: str = "center") -> Tuple[int, int]:
        """
        对齐方式.
        left, right, top, bottom, center
        """
        x_px = self._parse_unit(x, "x")
        y_px = self._parse_unit(y, "y")
        if align == "left":
            return (x_px, y_px - height//2)
        elif align == "right":
            return (x_px - width, y_px - height//2)
        elif align == "top":
            return (x_px - width//2, y_px)
        elif align == "bottom":
            return (x_px - width//2, y_px - height)
        else:
            return (x_px - width//2, y_px - height//2)

    def text(self,
             x: Union[str, int, float],
             y: Union[str, int, float],
             size: Union[str, int],
             font_path: str,
             color: Union[str, Tuple[int, int, int]],
             opacity: float = 1.0,
             align: str = "center",
             content: str = "") -> None:
        """
        绘字.
        对齐方式-> left, right, top, bottom, center
        位置相关单位-> px, %, pw, ph
        懒得写了, 依旧抄袭css. color不能rgba, 想用就写rgb再来个opacity属性
        """
        font_size = self._parse_unit(size, "x")
        try:
            font = ImageFont.truetype(font_path, font_size)
        except Exception as e:
            print(f"字体 {font_path} 加载失败 -> {e}")
            fallback_fonts = ["C:/Windows/Fonts/simhei.ttf", "C:/Windows/Fonts/msyh.ttc"]
            font = None
            for fallback in fallback_fonts:
                try:
                    font = ImageFont.truetype(fallback, font_size)
                    break
                except:
                    continue
            font = font if font else ImageFont.load_default()
        text_bbox = self.draw.textbbox((0, 0), str(content), font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        left, top = self._parse_anchor(x, y, text_width, text_height, align)
        rgba_color = self._parse_color(color, opacity)
        self.draw.text(
            (left, top),
            str(content),
            font=font,
            fill=rgba_color,
            align=align
        )

    def color_block(self,
                    x: Union[str, int, float],
                    y: Union[str, int, float],
                    width: Union[str, int, float],
                    height: Union[str, int, float],
                    color: Union[str, Tuple[int, int, int]],
                    radius: List[int] = [0, 0, 0, 0],
                    opacity: float = 1.0) -> None:
        """
        绘色块.
        """
        w_px = self._parse_unit(width, "width")
        h_px = self._parse_unit(height, "height")
        left, top = self._parse_anchor(x, y, w_px, h_px, "center")
        right = left + w_px
        bottom = top + h_px
        block_layer = Image.new("RGBA", (self.img_width, self.img_height), (0, 0, 0, 0))
        block_draw = ImageDraw.Draw(block_layer, "RGBA")
        rgba_color = self._parse_color(color, opacity)
        radius_val = max(radius) if isinstance(radius, (list, tuple)) and radius else 0
        block_draw.rounded_rectangle(
            [left, top, right, bottom],
            radius=int(radius_val),
            fill=rgba_color
        )
        self.bg_img = Image.alpha_composite(self.bg_img, block_layer)
        self.draw = ImageDraw.Draw(self.bg_img, "RGBA")

    def image(self,
              x: Union[str, int, float],
              y: Union[str, int, float],
              width: Union[str, int, float],
              height: Union[str, int, float],
              radius: List[int] = [0, 0, 0, 0],
              opacity: float = 1.0,
              img_path: str = "") -> None:
        """
        绘图.
        radius是圆角-> 传入列表(元素都是int) [左上, 右上, 右下, 左下]
        img_path-> path或url
        """
        def is_url(path: str) -> bool:
            url_pattern = re.compile(r'^https?://.*\.(png|jpg|jpeg|gif|webp|bmp)', re.IGNORECASE)
            return bool(url_pattern.match(path))
        try:
            if is_url(img_path):
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }
                response = requests.get(img_path, headers=headers, timeout=10)
                response.raise_for_status()
                sub_img = Image.open(BytesIO(response.content)).convert("RGBA")
            else:
                if not os.path.exists(img_path):
                    raise FileNotFoundError(f"图片不存在 路径：{img_path}")
                sub_img = Image.open(img_path).convert("RGBA")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"图片下载失败 {e}")
        except Exception as e:
            raise RuntimeError(f"图片加载失败 {e}")
        w_px = self._parse_unit(width, "width")
        h_px = self._parse_unit(height, "height")
        sub_img = sub_img.resize((w_px, h_px), Image.Resampling.LANCZOS)
        if opacity < 1.0:
            alpha = sub_img.split()[3]
            alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
            sub_img.putalpha(alpha)
        left, top = self._parse_anchor(x, y, w_px, h_px, "center")
        radius_val = max(radius) if isinstance(radius, (list, tuple)) and radius else 0
        if radius_val > 0:
            mask = Image.new("L", (w_px, h_px), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.rounded_rectangle([0,0,w_px,h_px], radius=int(radius_val), fill=255)
            sub_img = ImageOps.fit(sub_img, mask.size, centering=(0.5,0.5))
            sub_img.putalpha(mask)
        temp_layer = Image.new("RGBA", self.bg_img.size, (0, 0, 0, 0))
        temp_layer.paste(sub_img, (left, top), sub_img)
        self.bg_img = Image.alpha_composite(self.bg_img, temp_layer)
        self.draw = ImageDraw.Draw(self.bg_img, "RGBA")

    def save(self, save_path: str = "result.png", quality: int = 95) -> str:
        abs_save_path = os.path.abspath(save_path)
        if save_path.lower().endswith((".jpg", ".jpeg")):
            rgb_img = self.bg_img.convert("RGB")
            rgb_img.save(abs_save_path, quality=quality)
            print(f"JPG不支持opacity 所以自动转为了RGB")
        else:
            self.bg_img.save(abs_save_path, quality=quality)
        return abs_save_path
    
    def get_text_size(self,
                      size: Union[str, int],
                      font_path: str,
                      content: str = "") -> Tuple[int, int]:
        """
        计算文字实际渲染的宽高
        返回 (text_width, text_height) 单位px
        """
        font_size = self._parse_unit(size, "x")
        try:
            font = ImageFont.truetype(font_path, font_size)
        except Exception as e:
            print(f"字体 {font_path} 加载失败-> {e}")
            fallback_fonts = ["C:/Windows/Fonts/simhei.ttf", "C:/Windows/Fonts/msyh.ttc"]
            font = None
            for fallback in fallback_fonts:
                try:
                    font = ImageFont.truetype(fallback, font_size)
                    break
                except:
                    continue
            font = font if font else ImageFont.load_default()
        text_bbox = self.draw.textbbox((0, 0), str(content), font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        return text_width, text_height

    def truncate_text_by_width(self,
                              content: str,
                              max_width: int,
                              size: Union[str, int],
                              font_path: str,
                              ellipsis: str = "...") -> str:
        """
        按渲染宽高截断文本. 比如把 'ALazyPikaXD是男娘这是毋庸置疑的' 截成 'ALazyPikaXD是男娘..'
        用作截断的文本传入至ellipsis
        max_width-> 最大允许的渲染width 单位px
        """
        ellipsis_width, _ = self.get_text_size(size, font_path, ellipsis)
        available_width = max_width - ellipsis_width
        original_width, _ = self.get_text_size(size, font_path, content)
        if original_width <= max_width:
            return content
        truncated_text = ""
        current_width = 0
        for char in content:
            char_width, _ = self.get_text_size(size, font_path, char)
            if current_width + char_width > available_width:
                break
            truncated_text += char
            current_width += char_width
        return f"{truncated_text}{ellipsis}"
    
    def draw_html(self,
              x: Union[str, int, float],
              y: Union[str, int, float],
              size: Union[str, int],
              font_path: str,
              html_content: str,
              line_spacing: int = 4,
              default_color: Union[str, Tuple[int, int, int]] = "#ffffff") -> None:
        # 这个功能是AI写的, 我就不展开说了. 忘了什么效果了 反正我肯定后来不用它了
        """
        绘制带HTML样式的文字（专门适配MC MOTD：<span style="color:#xxx">文字</span>、<br>换行）
        :param x: 起始X（左上锚点）
        :param y: 起始Y（左上锚点）
        :param size: 字体大小
        :param font_path: 字体路径
        :param html_content: 带html的内容
        :param line_spacing: 行间距
        :param default_color: 默认颜色
        """
        font_size = self._parse_unit(size, "x")

        try:
            font = ImageFont.truetype(font_path, font_size)
        except:
            font = ImageFont.load_default()

        base_x = self._parse_unit(x, "x")
        base_y = self._parse_unit(y, "y")

        html = html_content.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
        color_pattern = re.compile(r'<span style="color:\s*(#[0-9a-fA-F]+);?.*?">(.*?)</span>', re.I | re.S)

        def split_segments(s):
            segs = []
            while True:
                match = color_pattern.search(s)
                if not match:
                    if s:
                        segs.append((None, s))
                    break
                start, end = match.span()
                if start > 0:
                    segs.append((None, s[:start]))
                color = match.group(1)
                text = match.group(2)
                segs.append((color, text))
                s = s[end:]
            return segs

        lines = []
        raw_lines = html.split("\n")
        for line in raw_lines:
            lines.append(split_segments(line))

        current_y = base_y
        for line in lines:
            current_x = base_x
            max_h = 0
            for color_str, text in line:
                if not text:
                    continue
                bbox = self.draw.textbbox((0, 0), text, font=font)
                w = bbox[2] - bbox[0]
                h = bbox[3] - bbox[1]
                max_h = max(max_h, h)

                color = self._parse_color(color_str) if color_str else self._parse_color(default_color)
                self.draw.text((current_x, current_y), text, font=font, fill=color)
                current_x += w
            current_y += max_h + line_spacing