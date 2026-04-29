"""火山引擎 (字节) BigTTS 适配器 — HTTP 一次性合成。

文档：https://www.volcengine.com/docs/6561/79817

使用流程：
1. 火山控制台开通「语音合成大模型」
2. 在 App 中绑定要用的音色（如 zh_male_yunzhou_bigtts 云舟）
3. 拿到 appid 与 access_token

Voice 推荐（电台场景）：
- zh_male_yunzhou_bigtts        云舟    新闻主播腔，最像电台
- zh_female_shuangkuaisisi_moon_bigtts 爽快思思 邻家大姐感
- zh_male_jingqiangkanye_moon_bigtts   京腔侃爷 怀旧栏目味道足
- zh_female_wanqudashu_moon_bigtts     婉曲大叔 温暖叙事
"""
from __future__ import annotations

import base64
import uuid

import httpx
from loguru import logger

from app.speech.tts.base import BaseTTS, TTSResult

_TTS_URL = "https://openspeech.bytedance.com/api/v1/tts"


class VolcanoTTS(BaseTTS):
    """火山引擎 BigTTS 引擎（HTTP /api/v1/tts，operation=query）。"""

    def __init__(
        self,
        app_id: str,
        access_token: str,
        cluster: str = "volcano_tts",
        default_voice: str = "zh_male_yunzhou_bigtts",
        timeout_s: float = 60.0,
    ):
        self.app_id = app_id
        self.access_token = access_token
        self.cluster = cluster
        self.default_voice = default_voice
        self._client = httpx.AsyncClient(timeout=timeout_s)

    async def synthesize(
        self,
        text: str,
        voice_name: str = "",
        speed: float = 1.0,
        volume: float = 1.0,
        audio_format: str = "mp3",
    ) -> TTSResult:
        if not text.strip():
            return TTSResult(audio_data=b"", audio_format=audio_format, sample_rate=24000)

        payload = {
            "app": {
                "appid": self.app_id,
                "token": "access_token",  # 此字段固定占位，真 token 在 header
                "cluster": self.cluster,
            },
            "user": {"uid": "wuwei_radio"},
            "audio": {
                "voice_type": voice_name or self.default_voice,
                "encoding": audio_format,
                "speed_ratio": float(speed),
                "volume_ratio": float(volume),
                "pitch_ratio": 1.0,
            },
            "request": {
                "reqid": str(uuid.uuid4()),
                "text": text,
                "text_type": "plain",
                "operation": "query",
            },
        }
        headers = {"Authorization": f"Bearer;{self.access_token}"}

        logger.debug(
            f"火山 TTS 合成: voice={payload['audio']['voice_type']} "
            f"len={len(text)} cluster={self.cluster} format={audio_format}"
        )

        resp = await self._client.post(_TTS_URL, json=payload, headers=headers)
        if resp.status_code != 200:
            raise RuntimeError(
                f"火山 TTS HTTP 错误: status={resp.status_code} body={resp.text[:300]}"
            )
        data = resp.json()
        code = data.get("code")
        if code != 3000:
            raise RuntimeError(
                f"火山 TTS 错误: code={code} message={data.get('message')!r} "
                f"operation={data.get('operation')}"
            )

        audio_b64 = data.get("data")
        if not audio_b64:
            raise RuntimeError("火山 TTS 返回空音频")

        return TTSResult(
            audio_data=base64.b64decode(audio_b64),
            audio_format=audio_format,
            sample_rate=24000,
            duration_ms=int(data.get("addition", {}).get("duration") or 0) or None,
        )

    async def close(self) -> None:
        await self._client.aclose()
