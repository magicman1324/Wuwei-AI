import 'dart:typed_data';

/// 音频播放占位 — Windows 桌面调试时不可用，手机端启用 just_audio 插件后替换。
class AudioPlayerService {
  bool get isPlaying => false;

  Future<void> playBytes(Uint8List audioBytes, {String format = 'mp3'}) async {
    // Windows 桌面不支持音频播放
  }

  Future<void> stop() async {}

  Future<void> dispose() async {}
}
