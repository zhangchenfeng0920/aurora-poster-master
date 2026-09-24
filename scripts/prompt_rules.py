"""绘图提示词（Prompt）构建规则。

设计目标：
- 文字内容只出现一次，集中在「允许显示的文字」区
- 明确禁止重复、禁止额外文字
- 行业/风格/色调等映射为可绘制的视觉关键词
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# 参数 -> 视觉关键词映射
# ---------------------------------------------------------------------------

STYLE_MAP: Dict[str, str] = {
    "简约": "极简主义，大量留白，克制的元素与单一视觉焦点",
    "极简": "极简主义构图，纯净背景，去装饰化",
    "奢华": "高级奢华质感，金色点缀，精致材质，影棚级布光",
    "活泼": "明快活泼，跳跃的色彩，动感构图",
    "国潮": "新国潮风格，东方美学，传统纹样现代表达",
    "科技": "未来科技感，光影粒子，冷色金属质感",
    "自然": "自然清新，柔和日光，真实材质，环保氛围",
    "复古": "复古怀旧调性，胶片颗粒，年代配色",
    "商务": "专业商务风格，稳重布局，利落几何",
    "可爱": "可爱治愈，圆润造型，柔和糖果色",
    "梦幻": "梦幻浪漫，柔焦光晕，轻盈层次",
    "高端": "高端杂志感，精致排版，高级灰调",
}

COLOR_MAP: Dict[str, str] = {
    "极光青绿": "极光青绿渐变（青绿到蓝紫），通透流光",
    "暖橙红": "暖橙到正红渐变，热情有食欲",
    "高对比黑白": "高对比黑白配色，强烈光影",
    "莫兰迪": "莫兰迪低饱和色系，柔和高级",
    "霓虹紫": "霓虹紫色调，赛博夜光",
    "金色奢华": "金色与深色搭配，奢华质感",
    "清新蓝白": "清新蓝白色调，干净通透",
    "粉系甜美": "柔和粉色系，甜美温柔",
    "大地色系": "大地色系，沉稳自然",
}

FONT_MAP: Dict[str, str] = {
    "现代无衬线": "现代无衬线字体，清晰利落",
    "经典衬线": "经典衬线字体，优雅有品质",
    "圆润可爱": "圆润可爱字体，亲和友好",
    "书法国风": "书法/国风字体，遒劲有力",
    "等宽科技": "等宽/科技感字体，理性未来",
    "纤细时尚": "纤细时尚字体，轻盈高级",
}

LAYOUT_MAP: Dict[str, str] = {
    "居中对称": "居中对称构图，视觉重心稳定庄重",
    "左对齐": "左对齐排版，右侧留主视觉空间",
    "右对齐": "右对齐排版，左侧留主视觉空间",
    "上下分割": "上下分割构图，图文分区清晰",
    "对角线": "对角线动态构图，富有张力",
}


# ---------------------------------------------------------------------------
# 行业特定视觉提示词
# ---------------------------------------------------------------------------

INDUSTRY_VISUAL: Dict[str, str] = {
    "餐饮美食": "诱人的美食特写，热气腾腾，食欲感强，温暖灯光，浅景深虚化",
    "零售电商": "产品居中精致陈列，干净背景，影棚柔光，突出商品质感与促销氛围",
    "生活服务": "真实服务场景，专业可信的人物与环境，温馨亲和的光线",
    "休闲娱乐": "欢乐热闹的氛围，人群互动，绚丽灯光，高饱和度",
    "旅游出行": "壮丽风景或舒适住宿空间，开阔视野，黄金时刻光线，向往感",
    "金融保险": "稳重可信赖的视觉，城市天际线/抽象几何，蓝金色调，简洁专业",
    "教育培训": "积极向上的学习场景，明亮教室，专注的人物，希望感",
    "医疗健康": "洁净专业的环境，白衣形象，柔和光线，安心可靠",
    "汽车交通": "车辆动感姿态，金属反光，公路/城市背景，速度感",
    "房产家居": "温馨室内空间或品质建筑外观，自然采光，家居质感",
    "文化传媒": "富有创意的视觉拼贴，艺术化光影，潮流文化符号",
    "科技互联网": "未来感界面，数据光效，深蓝/青色调，极简科技空间",
    "农业林业": "绿色田野与自然生态，阳光雨露，新鲜天然的农产品",
    "工业制造": "精密机械与工厂场景，金属质感，秩序感，冷色调",
    "能源环保": "清洁能源意象（阳光/风力/绿叶），蓝天绿地，可持续氛围",
}


# ---------------------------------------------------------------------------
# 字段定义（与前端 PosterData 对齐）
# ---------------------------------------------------------------------------

TEXT_FIELDS: List[Dict[str, str]] = [
    {"key": "product_name", "label": "产品名称"},
    {"key": "main_title", "label": "主标题"},
    {"key": "subtitle", "label": "副标题"},
    {"key": "slogan", "label": "营销金句"},
    {"key": "price_offer", "label": "价格/优惠"},
    {"key": "cta", "label": "行动号召"},
    {"key": "contact", "label": "联系信息"},
    {"key": "notice", "label": "补充说明"},
]

# 允许出现在海报上的字符白名单（用于过滤潜在非法字符）
ALLOWED_CHARS = set(
    "abcdefghijklmnopqrstuvwxyz"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789"
    " !\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"
    "，。！？、；：“”‘’（）《》【】…—·～￥%&＋＝／"
)


def sanitize_text(value: str) -> str:
    """轻度清洗：去除首尾空白与换行，统一不允许多行（避免文字错位）。"""
    if not value:
        return ""
    cleaned = " ".join(str(value).split())
    return cleaned.strip()


def _join_keywords(*parts: Optional[str]) -> str:
    return "，".join([p for p in parts if p])


def build_prompt(data: Dict[str, Any]) -> str:
    """根据 poster_request 构造最终绘图提示词。

    data 字段见 references/api-schema.md。
    """
    industry = sanitize_text(data.get("industry", ""))
    subcategory = sanitize_text(data.get("subcategory", ""))
    theme = sanitize_text(data.get("theme", ""))

    style = data.get("style", "")
    color_scheme = data.get("color_scheme", "")
    font_style = data.get("font_style", "")
    layout_direction = data.get("layout_direction", "")

    # ---- 文字区（唯一来源，去重）----
    text_lines: List[str] = []
    seen: set[str] = set()
    for field in TEXT_FIELDS:
        raw = data.get(field["key"], "")
        text = sanitize_text(raw if isinstance(raw, str) else "")
        if not text:
            continue
        # 同一字符串去重（避免用户在多个字段填了相同内容）
        if text in seen:
            continue
        seen.add(text)
        text_lines.append(f"- {field['label']}：{text}")

    has_logo = bool(data.get("logo"))
    logo_position = data.get("logo_position", "左上角")

    # ---- 组装 ----
    sections: List[str] = []

    subject = theme or subcategory or industry
    sections.append(f"【主题】一张关于「{subject}」的专业商业宣传海报")

    visual_parts: List[str] = []
    if industry and industry in INDUSTRY_VISUAL:
        visual_parts.append(INDUSTRY_VISUAL[industry])
    if style and style in STYLE_MAP:
        visual_parts.append(STYLE_MAP[style])
    if color_scheme and color_scheme in COLOR_MAP:
        visual_parts.append(COLOR_MAP[color_scheme])
    if layout_direction and layout_direction in LAYOUT_MAP:
        visual_parts.append(LAYOUT_MAP[layout_direction])
    extra_visual = sanitize_text(data.get("extra_visual", ""))
    if extra_visual:
        visual_parts.append(extra_visual)
    if visual_parts:
        sections.append("【视觉风格】" + _join_keywords(*visual_parts))

    if font_style and font_style in FONT_MAP:
        sections.append("【文字气质】" + FONT_MAP[font_style])

    if has_logo:
        sections.append(
            "【Logo区域】画面"
            + logo_position
            + "预留一块干净的空白安全区域用于后期放置品牌Logo，此区域保持简洁、不要绘制任何标志或文字"
        )

    if text_lines:
        sections.append("【海报上允许显示的全部文字（且仅允许这些文字）】\n" + "\n".join(text_lines))

    # 严格的文字约束
    sections.append(
        "【严格要求】"
        "1）上面列出的每段文字在整张海报中只出现一次，严禁以任何形式重复——尤其主标题、行动号召、联系信息三大高危字段，绝不允许多次出现；"
        "2）文字必须准确、清晰、完整、无错别字、不变形、不乱码；"
        "3）除上面列出的文字外，禁止出现任何其他文字、字母、网址、二维码、标签或符号；不同字段的文字禁止拼接、混搭或拆分重组；"
        "4）文字排版层级清晰、对齐规整、与背景有足够对比度、不被画面元素遮挡；"
        "5）不要生成或绘制任何Logo、品牌标志、水印。"
    )
    extra_rules = sanitize_text(data.get("extra_rules", ""))
    if extra_rules:
        sections.append("【附加要求】" + extra_rules)
    sections.append("高质量商业海报，细节丰富，专业平面设计，4K级精细度")

    return "\n".join(sections)
