"""科大讯飞 WebSocket API 公共工具（鉴权 URL 构造、PCM 帧切分）。

讯飞 IAT / TTS 均使用同一套 HMAC-SHA256 鉴权：
https://www.xfyun.cn/doc/asr/voicedictation/API.html
https://www.xfyun.cn/doc/tts/online_tts/API.html
"""
from __future__ import annotations

import base64
import hashlib
import hmac
from datetime import datetime, timezone
from email.utils import format_datetime
from typing import Iterable
from urllib.parse import urlencode, urlparse


def _rfc1123_now() -> str:
    """RFC1123 格式的 GMT 时间，讯飞签名要求。"""
    return format_datetime(datetime.now(timezone.utc), usegmt=True)


def build_auth_url(
    base_url: str,
    api_key: str,
    api_secret: str,
    *,
    date: str | None = None,
) -> str:
    """生成讯飞 WebSocket 鉴权 URL。

    Args:
        base_url: 讯飞接口 wss URL，如 ``wss://iat-api.xfyun.cn/v2/iat``
            或 ``wss://tts-api.xfyun.cn/v2/tts``。
        api_key: 控制台的 APIKey。
        api_secret: 控制台的 APISecret。
        date: 可选，测试时可注入固定时间，生产环境请传 None（自动取当前 GMT）。

    Returns:
        拼好 query 参数的完整 wss URL。
    """
    parsed = urlparse(base_url)
    host = parsed.hostname or ""
    path = parsed.path or "/"

    date = date or _rfc1123_now()
    signature_origin = (
        f"host: {host}\n"
        f"date: {date}\n"
        f"GET {path} HTTP/1.1"
    )
    signature_sha = hmac.new(
        api_secret.encode("utf-8"),
        signature_origin.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()
    signature = base64.b64encode(signature_sha).decode("utf-8")

    authorization_origin = (
        f'api_key="{api_key}", '
        f'algorithm="hmac-sha256", '
        f'headers="host date request-line", '
        f'signature="{signature}"'
    )
    authorization = base64.b64encode(
        authorization_origin.encode("utf-8")
    ).decode("utf-8")

    query = urlencode(
        {
            "authorization": authorization,
            "date": date,
            "host": host,
        }
    )
    return f"{base_url}?{query}"


# 讯飞 IAT 推荐帧大小：40ms @ 16kHz 16bit mono = 1280 bytes
DEFAULT_FRAME_SIZE = 1280


def chunk_pcm(audio_data: bytes, frame_size: int = DEFAULT_FRAME_SIZE) -> Iterable[bytes]:
    """把整段 PCM 切成固定大小的帧（最后一帧可能不满）。"""
    if not audio_data:
        return
    for i in range(0, len(audio_data), frame_size):
        yield audio_data[i : i + frame_size]
