import os
import base64
import requests
import subprocess

def audio_to_base64(path):
    """音频转base64. 依旧要么本地路径要么url
    结果不带 data:.. 这种"""
    temp_dir = os.path.join(os.getcwd(), 'temp')
    os.makedirs(temp_dir, exist_ok=True)
    audio_file_path = ""
    if path.startswith(('http://', 'https://')):
        try:
            response = requests.get(path, timeout=10, stream=True)
            response.raise_for_status()
            file_name = f"temp_mp3_{hash(path)}.mp3"
            audio_file_path = os.path.join(temp_dir, file_name)
            with open(audio_file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        except requests.exceptions.RequestException as e:
            if os.path.exists(audio_file_path):
                os.remove(audio_file_path)
            raise Exception(f"fetch error -> {e}")
    else:
        if not os.path.exists(path):
            raise FileNotFoundError(f"文件不存在 -> {path}")
        audio_file_path = path
    try:
        with open(audio_file_path, 'rb') as f:
            audio_data = f.read()
        base64_encoded = base64.b64encode(audio_data).decode('utf-8')
    except Exception as e:
        raise Exception(f"转base64失败 -> {e}")
    
    return base64_encoded

def audio_to_silk(path):
    """音频转slk 也就是转qq语音. 依旧传入本地路径或url"""
    # 用到了 tool/a2slk.exe
    # 程序来源 https://github.com/kn007/silk-v3-decoder
    silk_encoder_exe = os.path.join(os.getcwd(), "tool", "a2slk.exe")
    if not os.path.exists(silk_encoder_exe):
        raise Exception(f"未在 {silk_encoder_exe} 找到工具")
    temp_dir = os.path.join(os.getcwd(), 'temp')
    os.makedirs(temp_dir, exist_ok=True)
    original_path = ""
    if path.startswith(('http://', 'https://')):
        file_name = f"net_mp3_{hash(path)}.mp3"
        original_path = os.path.join(temp_dir, file_name)
        try:
            response = requests.get(path, timeout=10, stream=True)
            response.raise_for_status()
            with open(original_path, 'wb') as f:
                for chunk in response.iter_content(8192):
                    f.write(chunk)
        except Exception as e:
            raise Exception(f"fetch error -> {e}")
    else:
        original_path = path
    pcm_file = os.path.join(temp_dir, f"temp_{hash(original_path)}.pcm")
    ffmpeg_cmd = [
        "ffmpeg", "-y", "-i", original_path,
        "-ar", "24000", "-ac", "1", "-f", "s16le", "-acodec", "pcm_s16le",
        pcm_file
    ]
    try:
        subprocess.run(ffmpeg_cmd, capture_output=True, check=True)
        if not os.path.exists(pcm_file):
            raise Exception("pcm生成失败")
    except subprocess.CalledProcessError as e:
        raise Exception(f"转换pcm出现问题 -> {e.stderr.decode('utf-8')}")
    slk_file = os.path.join(temp_dir, os.path.splitext(os.path.basename(original_path))[0] + ".slk")
    silk_cmd = [
        silk_encoder_exe,
        pcm_file, slk_file,
        "-Fs_API", "24000",
        "-rate", "25000",
        "-tencent"
    ]
    try:
        result = subprocess.run(silk_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"slk编码失败 -> {result.stderr}")
        if not os.path.exists(slk_file):
            raise Exception("slk生成失败")
    except Exception as e:
        raise Exception(f"调用转换失败 -> {e}")
    for temp_file in [pcm_file, original_path] if path.startswith(('http://', 'https://')) else [pcm_file]:
        if os.path.exists(temp_file):
            os.remove(temp_file)
    slk_base64 = audio_to_base64(slk_file)
    return slk_base64