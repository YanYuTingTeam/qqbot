import math
import numpy as np
from PIL import Image
from urllib.request import urlopen
from io import BytesIO

# 这是AerMusic的取色方法, 改自 autohue. 
# github: https://github.com/Auto-Plugin/autohue.js
# 在基础上新增了"theme"键. 实际是用来模仿网易云神光播放样式而添加的.
# 内容实际上与bot无关, 在ncm命令用到了. 它来源于AerMusic.
# AerMusic: https://music.aermini.top

def rgb_to_lab(r, g, b):
    R = r / 255.0
    G = g / 255.0
    B = b / 255.0

    R = math.pow((R + 0.055) / 1.055, 2.4) if R > 0.04045 else R / 12.92
    G = math.pow((G + 0.055) / 1.055, 2.4) if G > 0.04045 else G / 12.92
    B = math.pow((B + 0.055) / 1.055, 2.4) if B > 0.04045 else B / 12.92

    X = R * 0.4124 + G * 0.3576 + B * 0.1805
    Y = R * 0.2126 + G * 0.7152 + B * 0.0722
    Z = R * 0.0193 + G * 0.1192 + B * 0.9505

    X /= 0.95047
    Y /= 1.0
    Z /= 1.08883

    def f(t):
        return math.pow(t, 1/3) if t > 0.008856 else 7.787 * t + 0.13793103448275862

    fx = f(X)
    fy = f(Y)
    fz = f(Z)
    L = 116 * fy - 16
    a = 500 * (fx - fy)
    b_val = 200 * (fy - fz)

    return [L, a, b_val]

def lab_distance(lab1, lab2):
    dL = lab1[0] - lab2[0]
    da = lab1[1] - lab2[1]
    db = lab1[2] - lab2[2]
    return math.sqrt(dL*dL + da*da + db*db)

def rgb_to_hex(rgb):
    return "#{:02x}{:02x}{:02x}".format(
        round(rgb[0]),
        round(rgb[1]),
        round(rgb[2])
    )

def hex_to_hsv(hex_color):
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16) / 255.0
    g = int(hex_color[2:4], 16) / 255.0
    b = int(hex_color[4:6], 16) / 255.0
    max_val = max(r, g, b)
    min_val = min(r, g, b)
    v = max_val
    d = max_val - min_val
    s = 0 if max_val == 0 else d / max_val
    h = 0

    if max_val != min_val:
        if max_val == r:
            h = (g - b) / d + (6 if g < b else 0)
        elif max_val == g:
            h = (b - r) / d + 2
        elif max_val == b:
            h = (r - g) / d + 4
        h /= 6

    return {
        'h': h * 360,
        's': s * 100,
        'v': v * 100
    }

def hsv_to_hex(h, s, v):
    h /= 360.0
    s /= 100.0
    v /= 100.0
    i = math.floor(h * 6)
    f = h * 6 - i
    p = v * (1 - s)
    q = v * (1 - f * s)
    t = v * (1 - (1 - f) * s)

    i = i % 6
    if i == 0:
        r, g, b = v, t, p
    elif i == 1:
        r, g, b = q, v, p
    elif i == 2:
        r, g, b = p, v, t
    elif i == 3:
        r, g, b = p, q, v
    elif i == 4:
        r, g, b = t, p, v
    else:
        r, g, b = v, p, q

    def to_hex(x):
        return format(round(x * 255), '02x')
    
    return f"#{to_hex(r)}{to_hex(g)}{to_hex(b)}"

def generate_background_color(primary_hex, secondary_hex):
    p = hex_to_hsv(primary_hex)
    s = hex_to_hsv(secondary_hex)

    is_low_contrast = abs(p['v'] - s['v']) < 30 and p['s'] < 25 and s['s'] < 25
    if is_low_contrast:
        return '#666699'

    is_cool_primary = 200 <= p['h'] <= 320
    is_warm_secondary = (30 <= s['h'] <= 60) or (s['h'] <= 15)
    if is_cool_primary and is_warm_secondary:
        hue = 35 if s['h'] < 15 else s['h']
        saturation = min(90, s['s'] + 20)
        value = min(80, s['v'] + 10)
        return hsv_to_hex(hue, saturation, value)

    is_warm_primary = (30 <= p['h'] <= 60) or (p['h'] <= 15)
    is_cool_secondary = 200 <= s['h'] <= 320
    if is_warm_primary and is_cool_secondary:
        mid_hue = ((p['h'] + s['h']) / 2 + 180) % 360
        saturation = (p['s'] + s['s']) / 2 * 1.2
        value = max(40, (p['v'] + s['v']) / 2)
        return hsv_to_hex(mid_hue, saturation, value)

    hue_diff = min(abs(p['h'] - s['h']), 360 - abs(p['h'] - s['h']))
    if hue_diff < 30:
        saturation = min(80, s['s'] + 10)
        value = max(30, s['v'] - 20) if p['v'] > 70 else min(80, s['v'] + 20)
        return hsv_to_hex(s['h'], saturation, value)

    hue = (p['h'] + 30) % 360
    saturation = min(80, p['s'] * 0.7)
    value = max(30, min(80, p['v'] * 1.2))
    return hsv_to_hex(hue, saturation, value)

def cluster_pixels(pixels, threshold=10):
    clusters = []
    for pixel in pixels:
        r = int(pixel[0])
        g = int(pixel[1])
        b = int(pixel[2])
        lab = rgb_to_lab(r, g, b)
        added = False
        
        for cluster in clusters:
            d = lab_distance(lab, cluster['averageLab'])
            if d < threshold:
                cluster['count'] += 1
                cluster['sumRgb'][0] = cluster['sumRgb'][0] + r
                cluster['sumRgb'][1] = cluster['sumRgb'][1] + g
                cluster['sumRgb'][2] = cluster['sumRgb'][2] + b
                cluster['sumLab'][0] += lab[0]
                cluster['sumLab'][1] += lab[1]
                cluster['sumLab'][2] += lab[2]
                cluster['averageRgb'] = [
                    cluster['sumRgb'][0] / cluster['count'],
                    cluster['sumRgb'][1] / cluster['count'],
                    cluster['sumRgb'][2] / cluster['count']
                ]
                cluster['averageLab'] = [
                    cluster['sumLab'][0] / cluster['count'],
                    cluster['sumLab'][1] / cluster['count'],
                    cluster['sumLab'][2] / cluster['count']
                ]
                added = True
                break
        
        if not added:
            clusters.append({
                'count': 1,
                'sumRgb': [int(r), int(g), int(b)],
                'sumLab': [lab[0], lab[1], lab[2]],
                'averageRgb': [r, g, b],
                'averageLab': lab
            })

    clusters.sort(key=lambda x: x['count'], reverse=True)
    return clusters

def get_color_data(image_url, max_size=100, margin=10):
    try:
        with urlopen(image_url) as response:
            img_data = response.read()
        img = Image.open(BytesIO(img_data)).convert('RGB')
        width, height = img.size
        if width > max_size or height > max_size:
            scale = min(max_size / width, max_size / height)
            new_width = math.floor(width * scale)
            new_height = math.floor(height * scale)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        width, height = img.size
        pixels = np.array(img).reshape(-1, 3)
        
        all_clusters = cluster_pixels(pixels, threshold=10)
        primary_cluster = all_clusters[0] if all_clusters else {'averageRgb': [255,255,255]}
        secondary_cluster = all_clusters[1] if len(all_clusters) > 1 else primary_cluster
        
        primary_color = rgb_to_hex(primary_cluster['averageRgb'])
        secondary_color = rgb_to_hex(secondary_cluster['averageRgb'])
        img_array = np.array(img)
        
        top_pixels = img_array[:margin, :, :].reshape(-1, 3)
        top_clusters = cluster_pixels(top_pixels, threshold=1)
        top_color = rgb_to_hex(top_clusters[0]['averageRgb']) if top_clusters else primary_color
        
        bottom_pixels = img_array[-margin:, :, :].reshape(-1, 3)
        bottom_clusters = cluster_pixels(bottom_pixels, threshold=1)
        bottom_color = rgb_to_hex(bottom_clusters[0]['averageRgb']) if bottom_clusters else primary_color
        
        left_pixels = img_array[:, :margin, :].reshape(-1, 3)
        left_clusters = cluster_pixels(left_pixels, threshold=1)
        left_color = rgb_to_hex(left_clusters[0]['averageRgb']) if left_clusters else primary_color
        
        right_pixels = img_array[:, -margin:, :].reshape(-1, 3)
        right_clusters = cluster_pixels(right_pixels, threshold=1)
        right_color = rgb_to_hex(right_clusters[0]['averageRgb']) if right_clusters else primary_color
        
        theme_color = generate_background_color(primary_color, secondary_color)
        color_data = {
            'main': primary_color,
            'bg': secondary_color,
            'theme': theme_color,
            'left': left_color,
            'right': right_color,
            'top': top_color,
            'bottom': bottom_color
        }
        return color_data
    except Exception as e:
        return {'error': str(e)}