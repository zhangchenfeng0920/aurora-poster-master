"""火山方舟（Ark）文本模型客户端。

使用 API Key（Bearer）鉴权：
  POST https://ark.cn-beijing.volces.com/api/v3/chat/completions
"""

from __future__ import annotations

import json
from typing import Any, Dict, Iterable, List, Optional

import requests


BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
DEFAULT_MODEL = "doubao-seed-1-6-250615"


class ArkError(RuntimeError):
    pass


def _post_chat(
    api_key: str,
    messages: List[Dict[str, str]],
    model: str = DEFAULT_MODEL,
    temperature: float = 0.8,
    response_format_json: bool = False,
    timeout: int = 120,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "stream": False,
    }
    if response_format_json:
        payload["response_format"] = {"type": "json_object"}

    resp = requests.post(
        f"{BASE_URL}/chat/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        timeout=timeout,
    )
    if resp.status_code != 200:
        raise ArkError(f"方舟接口 HTTP {resp.status_code}: {resp.text[:500]}")
    try:
        return resp.json()
    except ValueError as exc:
        raise ArkError(f"方舟接口返回非 JSON: {resp.text[:500]}") from exc


def chat(
    api_key: str,
    messages: List[Dict[str, str]],
    model: str = DEFAULT_MODEL,
    temperature: float = 0.8,
    timeout: int = 120,
) -> str:
    """单轮/多轮对话，返回助手文本。"""
    result = _post_chat(
        api_key, messages, model=model, temperature=temperature, timeout=timeout
    )
    try:
        return result["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as exc:
        raise ArkError(f"方舟响应结构异常: {json.dumps(result, ensure_ascii=False)[:500]}") from exc


def chat_json(
    api_key: str,
    messages: List[Dict[str, str]],
    model: str = DEFAULT_MODEL,
    temperature: float = 0.7,
    timeout: int = 120,
) -> Dict[str, Any]:
    """要求模型返回 JSON 对象。"""
    result = _post_chat(
        api_key,
        messages,
        model=model,
        temperature=temperature,
        response_format_json=True,
        timeout=timeout,
    )
    content = result["choices"][0]["message"]["content"]
    try:
        return json.loads(content)
    except ValueError as exc:
        raise ArkError(f"模型未返回合法 JSON: {content[:500]}") from exc


def stream_chat(
    api_key: str,
    messages: List[Dict[str, str]],
    model: str = DEFAULT_MODEL,
    temperature: float = 0.8,
    timeout: int = 120,
) -> Iterable[str]:
    """流式对话，逐块产出文本增量（SSE）。"""
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "stream": True,
    }
    with requests.post(
        f"{BASE_URL}/chat/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        json=payload,
        timeout=timeout,
        stream=True,
    ) as resp:
        if resp.status_code != 200:
            raise ArkError(f"方舟流式接口 HTTP {resp.status_code}: {resp.text[:500]}")
        for raw_line in resp.iter_lines():
            if not raw_line:
                continue
            line = raw_line.decode("utf-8")
            if not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if data == "[DONE]":
                break
            try:
                chunk = json.loads(data)
                delta = chunk["choices"][0].get("delta", {})
                piece = delta.get("content")
                if piece:
                    yield piece
            except (ValueError, KeyError, IndexError):
                continue
