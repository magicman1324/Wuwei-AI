"""音频工具：to_pcm16_16k_mono / write_audio_tempfile 测试。"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np

from app.speech.audio_utils import (
    TARGET_SAMPLE_RATE,
    to_pcm16_16k_mono,
    write_audio_tempfile,
)


# ---- to_pcm16_16k_mono ----

def test_empty_input_returns_empty() -> None:
    assert to_pcm16_16k_mono(16000, np.array([], dtype=np.float32)) == b""


def test_float32_mono_16k_passthrough_length() -> None:
    samples = np.zeros(1600, dtype=np.float32)  # 100ms @ 16k
    pcm = to_pcm16_16k_mono(16000, samples)
    # 1600 samples * 2 bytes/sample
    assert len(pcm) == 3200


def test_int16_passthrough_byte_length() -> None:
    samples = np.zeros(800, dtype=np.int16)
    pcm = to_pcm16_16k_mono(16000, samples)
    assert len(pcm) == 1600


def test_stereo_collapsed_to_mono() -> None:
    # 200 帧 stereo = 200 mono samples after avg
    samples = np.zeros((200, 2), dtype=np.float32)
    pcm = to_pcm16_16k_mono(16000, samples)
    assert len(pcm) == 400  # 200 * 2 bytes


def test_44100_resampled_to_16k() -> None:
    # 1 秒 44.1k 单声道 → 应该约等于 16000 个 PCM16 samples
    samples = np.zeros(44100, dtype=np.float32)
    pcm = to_pcm16_16k_mono(44100, samples)
    n_samples = len(pcm) // 2
    assert abs(n_samples - TARGET_SAMPLE_RATE) <= 2  # 允许四舍五入误差


def test_48000_resampled_to_16k() -> None:
    samples = np.zeros(48000, dtype=np.float32)  # 1 秒
    pcm = to_pcm16_16k_mono(48000, samples)
    n_samples = len(pcm) // 2
    assert abs(n_samples - TARGET_SAMPLE_RATE) <= 2


def test_float_clipping_to_int16_range() -> None:
    # 含有越界值的 float 信号
    samples = np.array([2.0, -2.0, 0.0, 1.0, -1.0], dtype=np.float32)
    pcm = to_pcm16_16k_mono(TARGET_SAMPLE_RATE, samples)
    # 解析回 int16
    arr = np.frombuffer(pcm, dtype="<i2")
    assert arr[0] == 32767   # 2.0 → clamp
    assert arr[1] == -32767  # -2.0 → clamp
    assert arr[2] == 0
    assert arr[3] == 32767
    assert arr[4] == -32767


def test_int8_uint_normalization() -> None:
    # uint8 中点 128 应映射到 ~0
    samples = np.array([128, 0, 255], dtype=np.uint8)
    pcm = to_pcm16_16k_mono(TARGET_SAMPLE_RATE, samples)
    arr = np.frombuffer(pcm, dtype="<i2")
    assert arr[0] == 0
    assert arr[1] < -16000   # 0 → -1.0 → -32767
    assert arr[2] > 16000    # 255 → +0.99...


def test_signal_preserved_after_resample() -> None:
    """正弦波重采样后应该保持低频内容（粗略）。"""
    sr_in = 32000
    t = np.arange(sr_in) / sr_in
    sine = (0.5 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)  # 440Hz, 1s
    pcm = to_pcm16_16k_mono(sr_in, sine)
    out = np.frombuffer(pcm, dtype="<i2").astype(np.float32) / 32767.0
    # 长度近似 16000
    assert abs(len(out) - 16000) <= 2
    # RMS 大致保持 (0.5/sqrt(2) ≈ 0.354)
    rms = float(np.sqrt(np.mean(out**2)))
    assert 0.25 < rms < 0.45


# ---- write_audio_tempfile ----

def test_write_audio_tempfile_creates_file() -> None:
    data = b"\xff\xfb\x90\x44 fake mp3 data"
    path = write_audio_tempfile(data, suffix=".mp3")
    try:
        p = Path(path)
        assert p.exists()
        assert p.suffix == ".mp3"
        assert p.read_bytes() == data
    finally:
        os.unlink(path)


def test_write_audio_tempfile_empty_returns_empty_string() -> None:
    assert write_audio_tempfile(b"") == ""
