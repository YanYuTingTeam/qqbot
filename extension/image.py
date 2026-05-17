import os
import base64
import requests

def image_to_base64(path, head: bool = False):
    """
    img to base64. path传入本地路径或者url. head决定了结果是否带有 data:image.. 这种
    加这个head是为了qq传base64 img.
    """
    if path.startswith(('http://', 'https://')):
        try:
            response = requests.get(path, timeout=10)
            response.raise_for_status()
            image_data = response.content
            image_ext = path.split('.')[-1].lower()
            if image_ext == 'jpg':
                image_ext = 'jpeg'
        except requests.exceptions.RequestException as e:
            raise Exception(f"fetch error -> {e}")
    else:
        if not os.path.exists(path):
            raise FileNotFoundError(f"文件不存在 -> {path}")
        image_ext = os.path.splitext(path)[1].lstrip('.').lower()
        if image_ext == 'jpg':
            image_ext = 'jpeg'
        with open(path, 'rb') as f:
            image_data = f.read()
    
    base64_encoded = base64.b64encode(image_data).decode('utf-8')
    return base64_encoded if not head else f"data:image/{image_ext};base64,{base64_encoded}"