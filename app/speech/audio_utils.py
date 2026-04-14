"""音频格式转换工具：把 Gradio 麦克风/上传的音频转成讯飞 IAT 要求的格式。

讯飞 IAT 要求 PCM16, 16kHz, 单声道, little-endian。
Gradio Audio(type="numpy") 返回 (sample_rate, np.ndarray)，可能是 stereo / 任意采样率 /
float32 或 int16 dtype。
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np

TARGET_SAMPLE_RATE = 16000


def to_pcm16_16k_mono(sample_rate: int, samples: np.ndarray) -> bytes:
    """把任意采样率/声道/dtype 的 numpy 音频转为 16k 单声道 PCM16 字节流。

    重采样使用线性插值（np.interp），对语音 ASR 的精度足够；
    若需要更高音质可换用 scipy.signal.resample_poly，但额外引入依赖。
    """
    if samples.size == 0:
        return b""

    # 1. 立体声 → 单声道（取均值）
    if samples.ndim == 2:
        samples = samples.mean(axis=1)

    # 2. dtype → float32 (-1.0, 1.0)，便于统一处理
    if np.issubdtype(samples.dtype, np.integer):
        info = np.iinfo(samples.dtype)
        # int16: 32768; int32: 2147483648; uint8: 128
        if samples.dtype == np.uint8:
            samples = (samples.astype(np.float32) - 128) / 128.0
        else:
            scale = float(max(abs(info.min), info.max))
            samples = samples.astype(np.float32) / scale
    else:
        samples = samples.astype(np.float32)

    # 3. 重采样到 16kHz
    if sample_rate != TARGET_SAMPLE_RATE:
        n_target = int(round(len(samples) * TARGET_SAMPLE_RATE / sample_rate))
        if n_target <= 0:
            return b""
        old_idx = np.arange(len(samples), dtype=np.float64)
        new_idx = np.linspace(0, len(samples) - 1, n_target, dtype=np.float64)
        samples = np.interp(new_idx, old_idx, samples).astype(np.float32)

    # 4. float32 → int16, clamp to avoid overflow on edge values
    samples = np.clip(samples, -1.0, 1.0)
    pcm16 = (samples * 32767.0).astype("<i2")  # little-endian int16
    return pcm16.tobytes()


def write_audio_tempfile(audio_bytes: bytes, suffix: str = ".mp3") -> str:
    """把 TTS 返回的音频字节写到临时文件，返回路径供 Gradio Audio 输出播放。

    Gradio 会自己负责清理 outputs 目录里的临时文件。
    """
    if not audio_bytes:
        return ""
    tmp = tempfile.NamedTemporaryFile(prefix="wuwei_tts_", suffix=suffix, delete=False)
    try:
        tmp.write(audio_bytes)
    finally:
        tmp.close()
    return str(Path(tmp.name))
