"""火山引擎 Signature V4 签名模块（纯标准库实现）。

适用于视觉智能服务（visual，cn-north-1）等 OpenAPI。
参考火山引擎官方「签名方法」文档实现。
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import hmac
from typing import Dict, List, Tuple
from urllib.parse import quote


ALGORITHM = "HMAC-SHA256"


def _sha256_hex(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _hmac_sha256(key: bytes, value: str) -> bytes:
    return hmac.new(key, value.encode("utf-8"), hashlib.sha256).digest()


def _uri_encode(value: str, safe: str = "-_.~") -> str:
    return quote(value, safe=safe)


def _canonical_query(query: Dict[str, str]) -> str:
    if not query:
        return ""
    items: List[Tuple[str, str]] = []
    for key, value in query.items():
        items.append((_uri_encode(str(key)), _uri_encode(str(value))))
    items.sort(key=lambda item: (item[0], item[1]))
    return "&".join(f"{k}={v}" for k, v in items)


def sign_request(
    access_key_id: str,
    secret_access_key: str,
    service: str,
    region: str,
    method: str,
    path: str,
    query: Dict[str, str],
    headers: Dict[str, str],
    body: bytes,
    now: _dt.datetime | None = None,
) -> Dict[str, str]:
    """生成带签名的请求头（含 host / x-date / x-content-sha256 / authorization）。

    headers 中必须至少包含 host；可额外包含 content-type 等。
    返回可直接用于 HTTP 请求的 headers 字典。
    """
    if now is None:
        now = _dt.datetime.now(_dt.timezone.utc)
    x_date = now.strftime("%Y%m%dT%H%M%SZ")
    short_date = x_date[:8]
    payload_hash = _sha256_hex(body)

    result_headers = dict(headers)
    result_headers["x-date"] = x_date
    result_headers["x-content-sha256"] = payload_hash

    # 参与签名的头：全部头（统一小写后按字典序）
    lower_map = {k.lower(): v for k, v in result_headers.items()}
    signed_header_names = sorted(lower_map.keys())

    canonical_headers = "".join(
        f"{name}:{str(lower_map[name]).strip()}\n" for name in signed_header_names
    )
    signed_headers = ";".join(signed_header_names)

    canonical_path = _uri_encode(path, safe="/-_.~")
    canonical_request = "\n".join(
        [
            method.upper(),
            canonical_path,
            _canonical_query(query),
            canonical_headers,
            signed_headers,
            payload_hash,
        ]
    )

    credential_scope = f"{short_date}/{region}/{service}/request"
    string_to_sign = "\n".join(
        [ALGORITHM, x_date, credential_scope, _sha256_hex(canonical_request.encode("utf-8"))]
    )

    k_date = _hmac_sha256(secret_access_key.encode("utf-8"), short_date)
    k_region = _hmac_sha256(k_date, region)
    k_service = _hmac_sha256(k_region, service)
    k_signing = _hmac_sha256(k_service, "request")
    signature = hmac.new(k_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

    authorization = (
        f"{ALGORITHM} Credential={access_key_id}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, Signature={signature}"
    )
    result_headers["Authorization"] = authorization
    return result_headers
