# 故障排查（Troubleshooting）

## 1. 配置相关

### config.py show 显示 image_ready=false
- 原因：缺少 access_key_id 或 secret_access_key。
- 处理：运行 `python3 config.py set --access-key-id ... --secret-access-key ...`。

### text_ready=false
- 文本辅助为可选项，不影响生图；如需启用，补 `--ark-api-key`。

### 找不到配置文件
- 默认在 `~/.aurora-poster/config.json`；可用 `python3 config.py path` 查看。
- 多环境可用环境变量 `AURORA_POSTER_CONFIG` 指定独立路径。

## 2. 鉴权 / 签名错误（生图）

常见报错关键字：`SignatureDoesNotMatch`、`InvalidAccessKey`、`401`、`403`。

- 确认 AK/SK 复制完整、没有多余空格（set 时会自动 strip）。
- 确认密钥属于**火山引擎账号**，且系统时间准确（签名依赖 UTC 时间）。
- 建议使用 IAM 子账号密钥并已授予视觉服务权限。
- `AccessDenied` / `NoPermission`：账号未授权调用视觉 OpenAPI 或未开通服务。

## 3. 模型未开通 / 不可用

- 报错常含：`model not found`、`req_key invalid`、`未开通`、`not activated`。
- 处理：
  1. 在火山引擎控制台开通「豆包·图像生成 Seedream」对应版本；
  2. 核对 `image_model`（req_key）与控制台一致，默认为 `doubao-seedream-4-5-251128`；
  3. 文本模型同理，在方舟控制台开通并核对 `text_model`。

## 4. 内容审核不通过

- 报错含：`content risk`、`sensitive`、`审核`、`risk control`。
- 处理：弱化/移除敏感词、绝对化承诺、医疗功效等表述；更换画面描述后重试。
- AI 文案模板已尽量规避违禁词，但具体行业仍需人工把关。

## 5. 尺寸 / 出图异常

- 比例取值非法时脚本自动回退到 `2K`；请使用 design-params.md 中列出的比例。
- 出图耗时较长（可能 20~60 秒），默认超时 120 秒；网络差时可重试。
- 返回结构异常：通常是服务临时波动，重试；持续失败请记录完整 message。

## 6. Logo 校验失败

| 报错 | 处理 |
|------|------|
| 超过 500KB | 压缩/精简 Logo 后再传 |
| 仅支持 PNG | 转换为透明 PNG |
| 不包含透明通道 | 导出时勾选透明背景 |
| 尺寸超出 900x360 | 仅警告，可继续；合成时会等比适配 |


## 7. 依赖缺失

- `No module named 'requests'` 或 `PIL`：执行 `pip install requests Pillow`。
- 建议 Python 3.8+。

## 8. 排查顺序建议

1. `python3 config.py show` 看配置完整度；
2. `python3 test_connection.py` 区分是文本还是生图问题；
3. 根据本文件对应类别处理；
4. 用 `--prompt-only`（generate_image.py）先确认 prompt 正常，再排查网络/服务。

## v2 新增：已实测问题

| 报错/现象 | 原因 | 处理 |
|-----------|------|------|
| `Could not find operation CVSync2V3` | 旧版视觉 OpenAPI 已下线 | v2 已切换到方舟 /images/generations，使用 ark_api_key |
| `InvalidEndpointOrModel.NotFound`（文本） | 账号未开通该文本模型 | 去方舟控制台开通任一豆包文本模型，并 config.py set --text-model；不开通则降级为由对话 AI 代写文案 |
| `image size must be at least 3686400 pixels` | 方舟生图有最低像素限制 | 使用脚本 RATIO_SIZE_MAP 内置尺寸，不要传小尺寸 |
| 文字重复/错字/错位 | 文字字段过多或深色高密度排版 | 精简到 ≤5 个文字字段；深色风格进一步减字；底部仅留一行联系信息 |
| 沙箱中配置丢失 | `~/.aurora-poster` 不持久 | 设置 AURORA_POSTER_CONFIG 指向持久挂载目录 |

## v2.8 新增：文字呈现问题

| 现象 | 原因 | 处理 |
|------|------|------|
| 按钮/框体内文字偏一侧、贴顶贴底 | AI 出图文字未居中 | 本地重绘：textbbox 实测文字宽高反算居中坐标（draw_centered），多行按行块居中；交付前局部放大核对 |
| 文字下方出现半透明模糊遮罩，遮挡背景天空/流光 | 早期修复法用整矩形模糊贴片 | 禁用整矩形贴片；改为「文字像素级替换」：亮度阈值定位文字像素（含抗锯齿边缘）+ MaxFilter 膨胀 + 高斯羽化，用周围背景渐变（先强模糊消除竖条纹）替换，背景流光自然穿过 |
| 价格数字不够醒目 | 未执行数字放大规则 | 价格行重绘：小字标签 + 1.5~2 倍大数字 + 画面唯一强调色 |
| 中文斜体变形/裁切 | 错切角度过大或未扩画布 | 倾斜前先扩展图层画布（tan(8°~12°) × 字高），仅主/副标题可用斜体 |
| 竖排文字顺序错 | 误按从左往右排 | 竖排一律从右往左，逐字换行，列间距≈1.3 倍字号 |
