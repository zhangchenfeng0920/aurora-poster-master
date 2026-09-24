#!/usr/bin/env python3
"""连接测试：分别验证文本 AI（方舟）与生图 AI（视觉服务）是否可用。

用法：
  python3 test_connection.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import merged_config, ok  # noqa: E402
from ark_client import DEFAULT_MODEL, chat  # noqa: E402
from image_client import DEFAULT_REQ_KEY, generate_image  # noqa: E402


def test_text(cfg: dict) -> dict:
    api_key = cfg.get("text_api_key") or cfg.get("ark_api_key")
    if not api_key:
        return {"available": False, "reason": "未配置 ark_api_key（文本辅助功能不可用，不影响生图）"}
    try:
        model = cfg.get("text_model") or DEFAULT_MODEL
        reply = chat(
            api_key,
            [{"role": "user", "content": "请回复两个字：正常"}],
            model=model,
            temperature=0,
            timeout=30,
        )
        return {"available": True, "model": model, "sample": reply.strip()[:20]}
    except Exception as exc:  # noqa: BLE001
        return {"available": False, "reason": str(exc)}


def test_image(cfg: dict) -> dict:
    ak = cfg.get("access_key_id")
    sk = cfg.get("secret_access_key")
    if not ak or not sk:
        return {"available": False, "reason": "未配置 access_key_id / secret_access_key"}
    try:
        model = cfg.get("image_model") or DEFAULT_REQ_KEY
        result = generate_image(
            access_key_id=ak,
            secret_access_key=sk,
            prompt="一个极简的纯色测试画面，居中一个小圆点，无文字",
            ratio="1:1",
            req_key=model,
            timeout=60,
        )
        return {
            "available": True,
            "model": model,
            "size": result.get("size"),
            "has_image": bool(result.get("b64_json") or result.get("image_url")),
        }
    except Exception as exc:  # noqa: BLE001
        return {"available": False, "reason": str(exc)}


def main() -> None:
    cfg = merged_config()
    text_result = test_text(cfg)
    image_result = test_image(cfg)
    ok(
        text_ai=text_result,
        image_ai=image_result,
        all_ready=image_result.get("available", False),
        message="生图可用即可开始制作；文本 AI 为可选增强",
    )


if __name__ == "__main__":
    main()
