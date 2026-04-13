"""讯飞 WebSocket 鉴权与帧切分工具测试。"""
from __future__ import annotations

from urllib.parse import parse_qs, urlparse

from app.speech.iflytek_common import build_auth_url, chunk_pcm


def test_build_auth_url_contains_required_params() -> None:
    url = build_auth_url(
        "wss://iat-api.xfyun.cn/v2/iat",
        api_key="ak",
        api_secret="as",
        date="Sun, 13 Apr 2026 00:00:00 GMT",
    )
    parsed = urlparse(url)
    q = parse_qs(parsed.query)
    assert parsed.hostname == "iat-api.xfyun.cn"
    assert parsed.path == "/v2/iat"
    assert q["host"] == ["iat-api.xfyun.cn"]
    assert q["date"] == ["Sun, 13 Apr 2026 00:00:00 GMT"]
    assert "authorization" in q and q["authorization"][0]


def test_build_auth_url_is_deterministic_when_date_fixed() -> None:
    url1 = build_auth_url(
        "wss://tts-api.xfyun.cn/v2/tts",
        api_key="k",
        api_secret="s",
        date="Mon, 14 Apr 2026 12:00:00 GMT",
    )
    url2 = build_auth_url(
        "wss://tts-api.xfyun.cn/v2/tts",
        api_key="k",
        api_secret="s",
        date="Mon, 14 Apr 2026 12:00:00 GMT",
    )
    assert url1 == url2


def test_build_auth_url_different_secret_yields_different_sig() -> None:
    url1 = build_auth_url(
        "wss://iat-api.xfyun.cn/v2/iat",
        api_key="k",
        api_secret="s1",
        date="Mon, 14 Apr 2026 12:00:00 GMT",
    )
    url2 = build_auth_url(
        "wss://iat-api.xfyun.cn/v2/iat",
        api_key="k",
        api_secret="s2",
        date="Mon, 14 Apr 2026 12:00:00 GMT",
    )
    assert url1 != url2


def test_chunk_pcm_exact_division() -> None:
    data = b"\x00" * 1280 * 3
    chunks = list(chunk_pcm(data, frame_size=1280))
    assert len(chunks) == 3
    assert all(len(c) == 1280 for c in chunks)


def test_chunk_pcm_with_tail() -> None:
    data = b"\x00" * (1280 * 2 + 100)
    chunks = list(chunk_pcm(data, frame_size=1280))
    assert len(chunks) == 3
    assert len(chunks[-1]) == 100


def test_chunk_pcm_empty() -> None:
    assert list(chunk_pcm(b"")) == []
