# 输入数据结构（API Schema）

## 1. poster_request —— 海报需求 JSON

由对话收集后组装，建议写入 `/tmp/poster_request.json`，供 `build_prompt.py` / `generate_image.py` 使用。

```json
{
  "industry": "餐饮美食",
  "subcategory": "火锅",
  "theme": "火锅店开业大酬宾",

  "main_title": "盛大开业",
  "subtitle": "地道川味火锅",
  "slogan": "一口入魂 满城飘香",
  "price_offer": "全场菜品6.8折",
  "cta": "立即预订",
  "contact": "电话 010-88888888",
  "notice": "活动限开业前三天",

  "style": "活泼",
  "color_scheme": "暖橙红",
  "aspect_ratio": "9:16",
  "font_style": "现代无衬线",
  "layout_direction": "居中对称",
  "text_effect": "描边字",
  "italic_titles": true,
  "vertical_fields": ["slogan"],
  "number_emphasis": true,
  "bottom_band": "通栏色带",

  "logo": "/path/to/logo.png",
  "logo_position": "左上角",

  "reference_images": [
    "/path/to/dish1.jpg",
    "https://example.com/dish2.jpg"
  ],

  "config": {
    "access_key_id": "可选-临时覆盖",
    "secret_access_key": "可选-临时覆盖",
    "ark_api_key": "可选-临时覆盖",
    "text_model": "doubao-seed-1-6-250615",
    "image_model": "doubao-seedream-4-5-251128"
  }
}
```

### 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| industry | string | 是 | 一级行业，取值见 industry-categories.md |
| subcategory | string | 否 | 子类目，可自定义 |
| theme | string | 否 | 海报主题/活动名，帮助定调 |
| main_title | string | 是* | 主标题 |
| subtitle | string | 否 | 副标题 |
| slogan | string | 否 | 营销金句 |
| price_offer | string | 否 | 价格/优惠 |
| cta | string | 否 | 行动号召 |
| contact | string | 否 | 联系信息 |
| notice | string | 否 | 补充说明 |
| style | string | 否 | 设计风格 |
| color_scheme | string | 否 | 色调 |
| aspect_ratio | string | 否 | 画幅比例，默认 9:16 |
| font_style | string | 否 | 字体气质 |
| layout_direction | string | 否 | 排版走向 |
| text_effect | string | 否 | 文字质感（v2.8）：纯色直排/描边字/渐变金属/霓虹描边/书法/斜体，取值见 design-params.md §5.5 |
| italic_titles | bool | 否 | 主/副标题是否斜体（v2.8，仅标题可用，正文禁斜体），默认 false |
| vertical_fields | array | 否 | 需要竖排的字段名列表（v2.8），如 ["slogan"]，短内容从右往左竖排 |
| number_emphasis | bool | 否 | 价格/优惠中的关键数字是否放大强调（v2.8，默认 true：数字 1.5~2 倍 + 强调色） |
| bottom_band | string | 否 | 底部信息区形式（v2.8）：通栏色带/深色渐变/直接压图 |
| logo | string | 否 | Logo 本地路径/URL/dataURL |
| logo_position | string | 否 | 左上角/顶部居中/右上角，默认左上角 |
| reference_images | array | 否 | 参考图（产品/场景），元素为路径或 URL |
| config | object | 否 | 临时覆盖配置，不落盘 |

> *`main_title` 建议必填；至少应有 main_title 或 theme，否则画面缺少信息焦点。

### 配置优先级

脚本内配置解析顺序（后者覆盖前者）：
1. 配置文件 `~/.aurora-poster/config.json`
2. 环境变量（`VOLCENGINE_ACCESS_KEY_ID` / `VOLCENGINE_SECRET_ACCESS_KEY` / `ARK_API_KEY` / `AURORA_TEXT_MODEL` / `AURORA_IMAGE_MODEL`）
3. poster_request 中的 `config` 对象

---

## 2. config —— 持久配置文件结构

路径：`$AURORA_POSTER_CONFIG` 或 `~/.aurora-poster/config.json`（权限 600）

```json
{
  "access_key_id": "AKLT...",
  "secret_access_key": "...",
  "ark_api_key": "...",
  "text_model": "doubao-seed-1-6-250615",
  "image_model": "doubao-seedream-4-5-251128"
}
```

| 字段 | 用途 | 是否必需 |
|------|------|---------|
| access_key_id | 火山引擎访问密钥 ID（生图签名） | 生图必需 |
| secret_access_key | 火山引擎秘密访问密钥（生图签名） | 生图必需 |
| ark_api_key | 火山方舟 API Key（文本能力） | 文本能力必需 |
| text_model | 方舟文本模型 ID/接入点 | 可空，有默认 |
| image_model | Seedream 模型 req_key | 可空，有默认 |

---

## 3. 统一输出格式

所有脚本 stdout 输出单行 JSON：

成功：
```json
{"status": "ok", "...": "..."}
```

失败：
```json
{"status": "error", "message": "错误原因"}
```

主要脚本成功时的关键字段：

| 脚本 | 关键字段 |
|------|---------|
| config.py show | image_ready / text_ready（及脱敏字段） |
| build_prompt.py | prompt / length |
| generate_image.py | output_path / size / model / has_logo / logo |
| text_ai.py generate-field | field / content |
| text_ai.py polish | original / polished |
| text_ai.py recommend-design | recommendation |
| text_ai.py director | advice |
| test_connection.py | text_ai / image_ai / all_ready |
| logo.py validate | format / width / height / warnings |

---

## 4. v2 扩展字段（poster_request）

| 字段 | 类型 | 说明 |
|------|------|------|
| extra_visual | string | 纯视觉元素自由描述（构图/装饰/细节小窗/光效），禁止包含新文字 |
| extra_rules | string | 附加排版约束（字号层级、底部限制、重复禁令等），追加进【附加要求】段 |

示例：
```json
{
  "extra_visual": "中部左右各一个圆角矩形细节小窗（铰链微距/折痕微距），细线连接主产品",
  "extra_rules": "联系信息用全海报最小字号置于最底部；底部仅一行文字，禁止额外横幅"
}
```

## v2.1 更新

- poster_request 新增 `product_name` 字段（产品名称，海报必显示，位于主标题上方，纳入允许文字清单与去重范围）
- 新增「阶段 1.5 标的物确认」流程：官方页面 URL 抓取校正 / 主动搜图 4 选 1，选中图作为 reference_images

## v2.2 配置扩展

| 字段 | 说明 |
|------|------|
| text_api_key | 可选。文本 AI 专用 Key（如 DeepSeek），优先于 ark_api_key 被 text_ai/test_connection 读取；生图仍用 ark_api_key |
| text_model | 文本模型 ID，如 doubao-seed-1-6-250615 或 deepseek-chat |

## v2.2 实战经验补充

- reference_images 元素支持 {"path"/"url": "...", "desc": "用户对素材的描述"} 对象形式
- Logo 双模式：模式A=logo 字段本地合成；模式B=放入 reference_images 由 AI 融合进场景
- extra_rules 支持 4A 排版约束（文字分区、字号层级、色彩分层、CTA 唯一、二维码占位）

## v2.8 字段扩展

- poster_request 新增：`text_effect`（文字质感）、`italic_titles`（标题斜体）、`vertical_fields`（竖排字段）、`number_emphasis`（数字放大强调，默认 true）、`bottom_band`（底部信息区形式）
- 以上字段在 prompt 的【文字刻画】区体现；AI 出图后本地重绘文字时，按 design-params.md §5.5/§5.6 执行（质感、斜体错切、竖排、数字放大、框体文字双向居中）
- 需求收集必须按 SKILL.md「v2.8 需求收集总清单」逐项确认，全部字段有用户表态后方可进入出图
