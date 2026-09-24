#!/usr/bin/env python3
"""Logo 校验与原样合成脚本。

校验规则：
- 格式仅 PNG / GIF（透明背景）
- 大小 ≤ 500KB
- 建议尺寸 ≤ 900×360（超出给警告但不阻断）

合成规则：
- Logo 保持原样（不改色、不重绘、保持透明度与动画首帧）
- 可放置：左上角 / 顶部居中 / 右上角
- 约束：Logo 最大宽度 ≤ 海报宽 25%，最大高度 ≤ 海报高 15%
  （等比缩放仅在超限时发生，普通尺寸完全不缩放）

用法：
  python3 logo.py validate --path logo.png
  python3 logo.py composite --poster p.png --logo logo.png --position 左上角 --out out.png
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import fail, load_as_data_source, ok, write_temp  # noqa: E402

MAX_BYTES = 500 * 1024
SUGGEST_MAX_W = 900
SUGGEST_MAX_H = 360
ALLOWED_MIME = {"image/png": ".png", "image/gif": ".gif"}
POSITIONS = ("左上角", "顶部居中", "右上角")
MARGIN_RATIO = 0.03   # 边距 = 海报短边的 3%


def _check_transparency(img) -> Tuple[bool, str]:
    """判断图像是否带透明通道。GIF 需检查透明色或至少可能透明。"""
    mode = getattr(img, "mode", "")
    if mode in ("RGBA", "LA"):
        # 只要存在 alpha 通道即认为可透明（不强制要求某像素必须透明）
        return True, "RGBA"
    if mode == "P":
        transparency = img.info.get("transparency")
        if transparency is not None:
            return True, "P+transparency"
        return False, "P(无透明信息)"
    if mode == "GIF":
        transparency = img.info.get("transparency")
        if transparency is not None:
            return True, "GIF+transparency"
        return False, "GIF(无透明信息)"
    return False, mode


def validate_logo(data: bytes):
    from PIL import Image  # 延迟导入，缺依赖时报错更友好

    if len(data) > MAX_BYTES:
        raise ValueError(f"Logo 大小 {len(data)} 字节，超过 500KB 限制")

    import io

    img = Image.open(io.BytesIO(data))
    img.load()
    fmt = (img.format or "").upper()

    if fmt not in ("PNG", "GIF"):
        raise ValueError(f"仅支持 PNG / GIF 透明背景格式，当前为 {fmt}")

    transparent, mode_desc = _check_transparency(img)
    if not transparent:
        raise ValueError("Logo 不包含透明通道，请使用透明背景的 PNG/GIF")

    warnings = []
    width, height = img.size
    if width > SUGGEST_MAX_W or height > SUGGEST_MAX_H:
        warnings.append(
            f"尺寸 {width}x{height} 超出建议的 {SUGGEST_MAX_W}x{SUGGEST_MAX_H}，将按比例适配"
        )

    return {
        "format": fmt,
        "width": width,
        "height": height,
        "size_bytes": len(data),
        "mode": mode_desc,
        "warnings": warnings,
    }


def cmd_validate(args: argparse.Namespace) -> None:
    data = load_as_data_source(args.path)
    info = validate_logo(data)
    ok(message="Logo 校验通过", **info)


def composite(poster_path: str, logo_path: str, position: str, out_path: str) -> dict:
    from PIL import Image

    poster = Image.open(poster_path).convert("RGBA")
    logo = Image.open(logo_path)
    # GIF 动图取第一帧
    if getattr(logo, "is_animated", False):
        logo.seek(0)
    logo = logo.convert("RGBA")

    pw, ph = poster.size
    max_w = int(pw * 0.25)
    max_h = int(ph * 0.15)

    lw, lh = logo.size
    scale = min(max_w / lw, max_h / lh, 1.0)
    if scale < 1.0:
        new_size = (max(1, int(lw * scale)), max(1, int(lh * scale)))
        logo = logo.resize(new_size, Image.LANCZOS)
        lw, lh = logo.size

    margin = int(min(pw, ph) * MARGIN_RATIO)
    if position == "左上角":
        x, y = margin, margin
    elif position == "右上角":
        x, y = pw - lw - margin, margin
    elif position == "顶部居中":
        x, y = (pw - lw) // 2, margin
    else:
        raise ValueError(f"不支持的位置: {position}")

    layer = Image.new("RGBA", poster.size, (0, 0, 0, 0))
    layer.paste(logo, (x, y), logo)
    result = Image.alpha_composite(poster, layer)

    # 输出统一 PNG，保证透明合成结果正确显示
    final = result.convert("RGB")
    final.save(out_path, format="PNG")
    return {
        "poster_size": [pw, ph],
        "logo_size": [lw, lh],
        "position": position,
        "xy": [x, y],
        "output_path": str(Path(out_path).resolve()),
    }


def cmd_composite(args: argparse.Namespace) -> None:
    if args.position not in POSITIONS:
        raise ValueError(f"位置必须是 {POSITIONS} 之一")
    info = composite(args.poster, args.logo, args.position, args.out)
    ok(message="Logo 合成完成", **info)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Logo 校验与合成")
    sub = parser.add_subparsers(dest="command", required=True)

    p_val = sub.add_parser("validate")
    p_val.add_argument("--path", required=True)
    p_val.set_defaults(func=cmd_validate)

    p_comp = sub.add_parser("composite")
    p_comp.add_argument("--poster", required=True)
    p_comp.add_argument("--logo", required=True)
    p_comp.add_argument("--position", default="左上角")
    p_comp.add_argument("--out", required=True)
    p_comp.set_defaults(func=cmd_composite)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except Exception as exc:  # noqa: BLE001
        fail(str(exc))


if __name__ == "__main__":
    main()
