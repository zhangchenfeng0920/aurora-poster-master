#!/usr/bin/env python3
"""海报生成主脚本：真实出图 + Logo 原样合成。

用法：
  python3 generate_image.py --input-json @/tmp/poster_request.json [--out out.png]

poster_request 字段见 references/api-schema.md。
"""

from __future__ import annotations

import argparse
import base64
import datetime as _dt
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (  # noqa: E402
    fail,
    load_as_data_source,
    merged_config,
    ok,
    read_input_json,
    write_temp,
)
from image_client import DEFAULT_REQ_KEY, generate_image  # noqa: E402
from prompt_rules import build_prompt  # noqa: E402


def _reference_data_urls(refs: Optional[List[Any]]) -> List[str]:
    """参考图可以是 {path|url} 对象或字符串。"""
    urls: List[str] = []
    if not refs:
        return urls
    for item in refs:
        if isinstance(item, str):
            source = item
        elif isinstance(item, dict):
            source = item.get("path") or item.get("url") or item.get("data_url")
        else:
            continue
        if not source:
            continue
        if source.startswith("data:"):
            urls.append(source)
        else:
            data = load_as_data_source(source)
            from _common import bytes_to_data_url

            urls.append(bytes_to_data_url(data))
    return urls


def _default_out() -> str:
    stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    return str(Path.cwd() / f"poster-{stamp}.png")


def main() -> None:
    parser = argparse.ArgumentParser(description="生成海报")
    parser.add_argument("--input-json", required=True)
    parser.add_argument("--out", help="输出图片路径，默认当前目录 poster-<时间戳>.png")
    parser.add_argument("--prompt-only", action="store_true", help="只构建 prompt 不出图")
    args = parser.parse_args()

    try:
        data = read_input_json(args.input_json)
        cfg = merged_config(data.get("config"))

        ak = cfg.get("access_key_id")
        sk = cfg.get("secret_access_key")
        if not ak or not sk:
            fail("未配置火山引擎 Access Key，请先运行 config.py set 或在请求中提供 config")
            return

        # 构建 prompt（文字去重由规则模块保证）
        prompt = build_prompt(data)

        if args.prompt_only:
            ok(prompt=prompt)
            return

        image_model = cfg.get("image_model") or DEFAULT_REQ_KEY
        ratio = data.get("aspect_ratio") or data.get("ratio")

        # 注意：用户上传的 Logo 不作为参考图交给 AI；参考图仅来自 reference_images
        ref_urls = _reference_data_urls(data.get("reference_images"))

        result = generate_image(
            access_key_id=ak,
            secret_access_key=sk,
            prompt=prompt,
            ratio=ratio,
            req_key=image_model,
            reference_data_urls=ref_urls,
        )

        # 落盘底图
        if result.get("b64_json"):
            poster_bytes = base64.b64decode(result["b64_json"])
        else:
            poster_bytes = load_as_data_source(result["image_url"])

        poster_tmp = write_temp(poster_bytes, suffix=".jpg")

        out_path = args.out or _default_out()

        # Logo 原样合成
        logo_info: Optional[Dict[str, Any]] = None
        logo = data.get("logo")
        logo_source: Optional[str] = None
        if isinstance(logo, str):
            logo_source = logo
        elif isinstance(logo, dict):
            logo_source = logo.get("path") or logo.get("url") or logo.get("data_url")

        if logo_source:
            from logo import composite, validate_logo

            logo_bytes = (
                base64.b64decode(logo_source.split(",", 1)[1])
                if logo_source.startswith("data:")
                else load_as_data_source(logo_source)
            )
            logo_meta = validate_logo(logo_bytes)
            logo_tmp = write_temp(logo_bytes, suffix=".png")
            position = data.get("logo_position", "左上角")
            logo_info = composite(poster_tmp, logo_tmp, position, out_path)
            logo_info["logo_validation"] = logo_meta
        else:
            # 无 Logo：直接把底图转存为 PNG
            from PIL import Image

            with Image.open(poster_tmp) as img:
                img.convert("RGB").save(out_path, format="PNG")

        ok(
            message="海报生成完成",
            output_path=str(Path(out_path).resolve()),
            size=result.get("size"),
            model=image_model,
            has_logo=bool(logo_source),
            logo=logo_info,
        )
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001
        fail(str(exc))


if __name__ == "__main__":
    main()
