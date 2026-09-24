#!/usr/bin/env python3
"""根据海报需求 JSON 构建最终绘图提示词。

用法：
  python3 build_prompt.py --input-json @/tmp/poster_request.json
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import fail, ok, read_input_json  # noqa: E402
from prompt_rules import build_prompt  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="构建海报绘图提示词")
    parser.add_argument("--input-json", required=True, help="@文件 或 JSON 字符串")
    args = parser.parse_args()

    try:
        data = read_input_json(args.input_json)
        prompt = build_prompt(data)
        ok(prompt=prompt, length=len(prompt))
    except Exception as exc:  # noqa: BLE001
        fail(str(exc))


if __name__ == "__main__":
    main()
