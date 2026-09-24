#!/usr/bin/env python3
"""配置管理脚本。

用法：
  python3 config.py show
  python3 config.py set [--access-key-id X] [--secret-access-key X]
                        [--ark-api-key X] [--text-model X] [--image-model X]
  python3 config.py clear
  python3 config.py path
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (  # noqa: E402
    config_path,
    fail,
    load_config,
    ok,
    save_config,
)

SETTABLE_FIELDS = [
    "access_key_id",
    "secret_access_key",
    "ark_api_key",
    "text_model",
    "image_model",
]

DEFAULTS = {
    "text_model": "doubao-seed-1-6-250615",
    "image_model": "doubao-seedream-4-5-251128",
}


def _mask(value: str, keep: int = 4) -> str:
    if not value:
        return ""
    if len(value) <= keep:
        return "*" * len(value)
    return "*" * (len(value) - keep) + value[-keep:]


def _public_view(cfg: dict) -> dict:
    view = {}
    for key in SETTABLE_FIELDS:
        value = cfg.get(key, "")
        if key in ("access_key_id", "secret_access_key", "ark_api_key"):
            view[key] = _mask(value) if value else ""
        else:
            view[key] = value
    # 便捷的完整度判断
    view["image_ready"] = bool(cfg.get("access_key_id") and cfg.get("secret_access_key"))
    view["text_ready"] = bool(cfg.get("ark_api_key"))
    view["config_path"] = str(config_path())
    return view


def cmd_show(_args: argparse.Namespace) -> None:
    cfg = load_config()
    view = _public_view(cfg)
    view["status"] = "ok"
    # 调整字段顺序，把 status 放最前
    ordered = {"status": "ok"}
    ordered.update(view)
    from _common import emit

    emit(ordered)


def cmd_set(args: argparse.Namespace) -> None:
    cfg = load_config()
    changed = []
    for field in SETTABLE_FIELDS:
        value = getattr(args, field)
        if value is not None:
            cfg[field] = value.strip()
            changed.append(field)

    # 首次配置时补默认模型
    for key, default in DEFAULTS.items():
        if not cfg.get(key):
            cfg[key] = default

    path = save_config(cfg)
    ok(message="配置已保存", changed=changed, path=str(path), config=_public_view(cfg))


def cmd_clear(_args: argparse.Namespace) -> None:
    path = config_path()
    if path.exists():
        path.unlink()
    ok(message="配置已清除", path=str(path))


def cmd_path(_args: argparse.Namespace) -> None:
    ok(path=str(config_path()), exists=config_path().exists())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="极光海报大师配置管理")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("show", help="查看当前配置（密钥脱敏）").set_defaults(func=cmd_show)

    p_set = sub.add_parser("set", help="写入/更新配置项")
    p_set.add_argument("--access-key-id")
    p_set.add_argument("--secret-access-key")
    p_set.add_argument("--ark-api-key")
    p_set.add_argument("--text-model")
    p_set.add_argument("--image-model")
    p_set.set_defaults(func=cmd_set)

    sub.add_parser("clear", help="清除全部配置").set_defaults(func=cmd_clear)
    sub.add_parser("path", help="输出配置文件路径").set_defaults(func=cmd_path)
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
