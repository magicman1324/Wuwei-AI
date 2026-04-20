"""音频格式转换工具：将 mp3/aac/wav 转为后端需要的 PCM16 16kHz 单声道。"""
from __future__ import annotations

import io


def to_pcm16_16k(audio_bytes: bytes, src_format: str) -> bytes:
    """将任意格式音频转换为 PCM16 16kHz 单声道。

    支持 src_format: pcm / mp3 / aac / wav / m4a / ogg
    PCM 直接透传，其他格式用 pydub 解码后重采样。
    """
    fmt = src_format.lower().lstrip(".")
    if fmt == "pcm":
        return audio_bytes

    try:
        from pydub import AudioSegment
    except ImportError as e:
        raise RuntimeError("pydub 未安装，无法转换音频格式") from e

    seg = AudioSegment.from_file(io.BytesIO(audio_bytes), format=fmt)
    seg = seg.set_frame_rate(16000).set_channels(1).set_sample_width(2)
    return seg.raw_data
