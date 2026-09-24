"""极光海报大师 Skill - 公共工具模块。

仅依赖 Python 标准库。提供：
- 统一 JSON 输出
- 配置文件读写
- 本地/远程文件读取
"""

from __future__ import annotations

import base64
import json
import os
import sys
import tempfile
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional


# ---------------------------------------------------------------------------
# 输出
# ---------------------------------------------------------------------------

def emit(payload: Dict[str, Any]) -> None:
    """向 stdout 输出单行 JSON。"""
    sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def ok(**data: Any) -> None:
    payload = {"status": "ok"}
    payload.update(data)
    emit(payload)


def fail(message: str, **extra: Any) -> None:
    payload: Dict[str, Any] = {"status": "error", "message": str(message)}
    payload.update(extra)
    emit(payload)
    sys.exit(1)


# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------

def config_path() -> Path:
    """返回配置文件路径。"""
    custom = os.environ.get("AURORA_POSTER_CONFIG")
    if custom:
        return Path(custom).expanduser()
    return Path.home() / ".aurora-poster" / "config.json"


def load_config() -> Dict[str, Any]:
    """读取配置；不存在或损坏时返回空字典。"""
    path = config_path()
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def save_config(cfg: Dict[str, Any]) -> Path:
    """写入配置，并尽量收紧文件权限。"""
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    return path


def merged_config(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """配置 = 环境变量 + 配置文件 + 显式覆盖（覆盖优先级最高）。"""
    cfg: Dict[str, Any] = {}
    cfg.update(load_config())

    env_map = {
        "access_key_id": "VOLCENGINE_ACCESS_KEY_ID",
        "secret_access_key": "VOLCENGINE_SECRET_ACCESS_KEY",
        "ark_api_key": "ARK_API_KEY",
        "text_model": "AURORA_TEXT_MODEL",
        "image_model": "AURORA_IMAGE_MODEL",
    }
    for key, env in env_map.items():
        value = os.environ.get(env)
        if value:
            cfg[key] = value

    if overrides:
        for key, value in overrides.items():
            if value is not None:
                cfg[key] = value
    return cfg


# ---------------------------------------------------------------------------
# 输入/文件
# ---------------------------------------------------------------------------

def read_input_json(arg: str) -> Dict[str, Any]:
    """读取 --input-json 参数。

    形式：
    - "@/path/to/file"  从文件读取
    - 其他              视为 JSON 字符串
    """
    if arg.startswith("@"):
        file_path = Path(arg[1:]).expanduser()
        if not file_path.exists():
            raise FileNotFoundError(f"输入文件不存在: {file_path}")
        text = file_path.read_text(encoding="utf-8")
    else:
        text = arg
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("input-json 必须是 JSON 对象")
    return data


def load_as_data_source(source: str, timeout: int = 30) -> bytes:
    """把本地路径或 http(s) URL 读取为字节。"""
    if source.startswith(("http://", "https://")):
        req = urllib.request.Request(source, headers={"User-Agent": "aurora-poster-master/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 (用户主动提供 URL)
            return resp.read()
    path = Path(source).expanduser()
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")
    return path.read_bytes()


def bytes_to_data_url(data: bytes, default_mime: str = "image/png") -> str:
    """字节转 data URL，自动探测常见图片 MIME。"""
    mime = default_mime
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        mime = "image/png"
    elif data[:6] in (b"GIF87a", b"GIF89a"):
        mime = "image/gif"
    elif data[:3] == b"\xff\xd8\xff":
        mime = "image/jpeg"
    elif data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        mime = "image/webp"
    b64 = base64.b64encode(data).decode("ascii")
    return f"data:{mime};base64,{b64}"


def guess_mime(data: bytes, default: str = "image/png") -> str:
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return default


def write_temp(data: bytes, suffix: str = ".img") -> str:
    """把字节写入临时文件，返回路径。"""
    fd, tmp_path = tempfile.mkstemp(suffix=suffix)
    with os.fdopen(fd, "wb") as handle:
        handle.write(data)
    return tmp_path
