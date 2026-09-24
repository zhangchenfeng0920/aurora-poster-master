#!/usr/bin/env python3
"""文本 AI 能力 CLI：字段文案生成 / 润色 / 设计参数推荐 / AI 总监建议。

用法：
  python3 text_ai.py generate-field --field main_title --theme 开业大酬宾 \
      --industry 餐饮美食 --subcategory 火锅
  python3 text_ai.py polish --text "火锅店开业优惠大"
  python3 text_ai.py recommend-design --industry 餐饮美食 --subcategory 火锅 --theme 开业大酬宾
  python3 text_ai.py director --industry 餐饮美食 --subcategory 火锅 --theme 开业大酬宾
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import fail, merged_config, ok  # noqa: E402
from ark_client import DEFAULT_MODEL, chat, chat_json  # noqa: E402


# ---------------------------------------------------------------------------
# Prompt 模板
# ---------------------------------------------------------------------------

FIELD_META: Dict[str, Dict[str, str]] = {
    "main_title": {"label": "主标题", "limit": "12字以内", "tone": "醒目、有冲击力"},
    "subtitle": {"label": "副标题", "limit": "18字以内", "tone": "补充说明、承上启下"},
    "slogan": {"label": "营销金句", "limit": "16字以内", "tone": "直击利益点、易传播"},
    "selling_points": {"label": "核心卖点", "limit": "每条14字以内", "tone": "具体、可信"},
    "price_offer": {"label": "价格/优惠", "limit": "14字以内", "tone": "有紧迫感、让利明确"},
    "cta": {"label": "行动号召", "limit": "8字以内", "tone": "动作明确、催促行动"},
    "contact": {"label": "联系信息", "limit": "30字以内", "tone": "清晰、可信"},
    "notice": {"label": "补充说明", "limit": "40字以内", "tone": "简洁、严谨"},
}


def _context_line(industry: str, subcategory: str) -> str:
    parts = [p for p in (industry, subcategory) if p]
    return f"行业：{' / '.join(parts)}" if parts else "行业：未指定"


def build_field_prompt(field: str, theme: str, industry: str, subcategory: str) -> List[Dict[str, str]]:
    meta = FIELD_META[field]
    system = (
        "你是一名世界级广告公司的资深文案，擅长为商业海报撰写高转化中文文案。"
        "只输出文案本身，不要解释、不要引号、不要序号。"
    )
    user = (
        f"{_context_line(industry, subcategory)}\n"
        f"海报主题：{theme or '未指定'}\n"
        f"请为海报写1条「{meta['label']}」。要求：{meta['tone']}，{meta['limit']}，"
        "符合该行业受众心理，口语自然，不使用夸张违禁用语。"
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


# ---------------------------------------------------------------------------
# 命令实现
# ---------------------------------------------------------------------------

def cmd_generate_field(args: argparse.Namespace) -> None:
    cfg = merged_config()
    api_key = cfg.get("text_api_key") or cfg.get("ark_api_key")
    if not api_key:
        fail("未配置方舟 API Key（ark_api_key），AI 文案不可用；可先运行 config.py set --ark-api-key")
        return
    if args.field not in FIELD_META:
        fail(f"field 必须是 {list(FIELD_META)} 之一")
        return

    messages = build_field_prompt(args.field, args.theme, args.industry, args.subcategory)
    model = cfg.get("text_model") or DEFAULT_MODEL
    content = chat(api_key, messages, model=model, temperature=0.9)
    content = content.strip().strip("「」\"'“”‘’").splitlines()[0].strip()
    ok(field=args.field, content=content)


def cmd_polish(args: argparse.Namespace) -> None:
    cfg = merged_config()
    api_key = cfg.get("text_api_key") or cfg.get("ark_api_key")
    if not api_key:
        fail("未配置方舟 API Key，润色不可用")
        return
    messages = [
        {
            "role": "system",
            "content": "你是资深文案编辑，擅长把平淡的句子改得更有吸引力且保留原意。只输出改写后的句子。",
        },
        {
            "role": "user",
            "content": (
                f"{_context_line(args.industry, args.subcategory)}\n"
                f"请把下面这句话改写得更精练、更有营销感（不改变事实、不添加虚假承诺）：\n{args.text}"
            ),
        },
    ]
    model = cfg.get("text_model") or DEFAULT_MODEL
    content = chat(api_key, messages, model=model, temperature=0.8)
    ok(original=args.text, polished=content.strip().splitlines()[0].strip())


def cmd_recommend_design(args: argparse.Namespace) -> None:
    cfg = merged_config()
    api_key = cfg.get("text_api_key") or cfg.get("ark_api_key")
    if not api_key:
        fail("未配置方舟 API Key，设计推荐不可用")
        return

    allowed = {
        "style": ["简约", "极简", "奢华", "活泼", "国潮", "科技", "自然", "复古", "商务", "可爱", "梦幻", "高端"],
        "color_scheme": ["极光青绿", "暖橙红", "高对比黑白", "莫兰迪", "霓虹紫", "金色奢华", "清新蓝白", "粉系甜美", "大地色系"],
        "aspect_ratio": ["9:16", "1:1", "3:4", "16:9", "4:3", "2:3", "3:2", "21:9", "9:21", "A4", "5:7"],
        "font_style": ["现代无衬线", "经典衬线", "圆润可爱", "书法国风", "等宽科技", "纤细时尚"],
        "layout_direction": ["居中对称", "左对齐", "右对齐", "上下分割", "对角线"],
    }

    system = "你是世界级广告公司的美术指导，根据行业与主题给出海报设计参数。只输出 JSON。"
    user = (
        f"{_context_line(args.industry, args.subcategory)}\n海报主题：{args.theme or '未指定'}\n"
        "请从下列候选中为每个字段选择一个最合适的值，并给出一句理由 reason：\n"
        + json.dumps(allowed, ensure_ascii=False)
        + '\n返回格式：{"style":...,"color_scheme":...,"aspect_ratio":...,"font_style":...,'
        '"layout_direction":...,"reason":"..."}'
    )
    model = cfg.get("text_model") or DEFAULT_MODEL
    data = chat_json(api_key, [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ], model=model, temperature=0.6)
    ok(recommendation=data)


def cmd_director(args: argparse.Namespace) -> None:
    cfg = merged_config()
    api_key = cfg.get("text_api_key") or cfg.get("ark_api_key")
    if not api_key:
        fail("未配置方舟 API Key，AI 总监建议不可用")
        return
    messages = [
        {
            "role": "system",
            "content": (
                "你是一位融合奥美、电通、Wieden+Kennedy 标准的世界级广告创意总监，"
                "依据文图比例、视觉动线、人体工程学与 WCAG 无障碍标准给出可执行的海报建议。"
            ),
        },
        {
            "role": "user",
            "content": (
                f"{_context_line(args.industry, args.subcategory)}\n海报主题：{args.theme or '未指定'}\n"
                "请给出：1）核心创意概念（一句话）；2）画面主体与构图建议；3）文字层级与文图比例；"
                "4）配色与光影；5）需要规避的常见问题。用中文分条简洁输出。"
            ),
        },
    ]
    model = cfg.get("text_model") or DEFAULT_MODEL
    content = chat(api_key, messages, model=model, temperature=0.8)
    ok(advice=content.strip())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="极光海报大师文本 AI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_field = sub.add_parser("generate-field")
    p_field.add_argument("--field", required=True)
    p_field.add_argument("--theme", default="")
    p_field.add_argument("--industry", default="")
    p_field.add_argument("--subcategory", default="")
    p_field.set_defaults(func=cmd_generate_field)

    p_polish = sub.add_parser("polish")
    p_polish.add_argument("--text", required=True)
    p_polish.add_argument("--industry", default="")
    p_polish.add_argument("--subcategory", default="")
    p_polish.set_defaults(func=cmd_polish)

    p_rec = sub.add_parser("recommend-design")
    p_rec.add_argument("--industry", default="")
    p_rec.add_argument("--subcategory", default="")
    p_rec.add_argument("--theme", default="")
    p_rec.set_defaults(func=cmd_recommend_design)

    p_dir = sub.add_parser("director")
    p_dir.add_argument("--industry", default="")
    p_dir.add_argument("--subcategory", default="")
    p_dir.add_argument("--theme", default="")
    p_dir.set_defaults(func=cmd_director)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001
        fail(str(exc))


if __name__ == "__main__":
    main()
