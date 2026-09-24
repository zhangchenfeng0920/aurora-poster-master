"""火山方舟 - 豆包 Seedream 文生图客户端（新版接口）。

旧版视觉智能 OpenAPI（CVSync2V3 / 2022-08-31）已下线，
现统一走方舟 API Key 鉴权：
  POST https://ark.cn-beijing.volces.com/api/v3/images/generations
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import requests


ENDPOINT = "https://ark.cn-beijing.volces.com/api/v3/images/generations"

DEFAULT_REQ_KEY = "doubao-seedream-4-5-251128"

# 画幅比例 -> 自定义像素尺寸（满足 Seedream 高分辨率区间）
RATIO_SIZE_MAP: Dict[str, str] = {
    "9:16": "2560x4568",
    "16:9": "4568x2560",
    "1:1": "3072x3072",
    "3:4": "3072x4096",
    "4:3": "4096x3072",
    "2:3": "2560x3840",
    "3:2": "3840x2560",
    "21:9": "4568x1960",
    "9:21": "1960x4568",
    "A4": "3508x4960",
    "5:7": "2800x3920",
}


class VolcImageError(RuntimeError):
    pass


def resolve_size(ratio: Optional[str]) -> str:
    if ratio and ratio in RATIO_SIZE_MAP:
        return RATIO_SIZE_MAP[ratio]
    return "2K"


def generate_image(
    access_key_id: str,
    secret_access_key: str,
    prompt: str,
    ratio: Optional[str] = None,
    req_key: str = DEFAULT_REQ_KEY,
    reference_data_urls: Optional[List[str]] = None,
    timeout: int = 120,
) -> Dict[str, Any]:
    """生成一张图片。

    返回字典：
      { "b64_json": ..., "image_url": ..., "size": ..., "raw": <完整响应> }
    """
    size = resolve_size(ratio)

    request_body: Dict[str, Any] = {
        "model": req_key,
        "prompt": prompt,
        "size": size,
        "watermark": False,
        "response_format": "b64_json",
    }
    if reference_data_urls:
        request_body["image"] = reference_data_urls

    response = requests.post(
        ENDPOINT,
        json=request_body,
        headers={
            "Content-Type": "application/json",
            # 方舟生图使用 API Key；兼容传入 AK/SK 的旧签名调用方式
            "Authorization": f"Bearer {_resolve_bearer(access_key_id, secret_access_key)}",
        },
        timeout=timeout,
    )

    # HTTP 层失败
    if response.status_code != 200:
        raise VolcImageError(
            f"生图接口 HTTP {response.status_code}: {response.text[:500]}"
        )

    try:
        result = response.json()
    except ValueError as exc:
        raise VolcImageError(f"生图接口返回非 JSON: {response.text[:500]}") from exc

    err = result.get("error")
    if err:
        raise VolcImageError(
            f"{err.get('code', 'Error')}: {err.get('message', '')}".strip()
        )

    data_list = result.get("data") or []
    first = data_list[0] if data_list else {}
    b64 = first.get("b64_json")
    image_url = first.get("url")

    if not b64 and not image_url:
        raise VolcImageError(f"生图成功但未返回图片数据: {json.dumps(result, ensure_ascii=False)[:500]}")

    return {
        "b64_json": b64,
        "image_url": image_url,
        "size": size,
        "raw": result,
    }


def _resolve_bearer(access_key_id: str, secret_access_key: str) -> str:
    """生图已切换到方舟 Bearer 鉴权：优先使用配置中的 ark_api_key。"""
    try:
        from _common import merged_config

        cfg = merged_config(None)
        ark_key = cfg.get("ark_api_key")
        if ark_key:
            return ark_key
    except Exception:
        pass
    return access_key_id
