import 'dart:typed_data';

/// 录音服务占位 — Windows 桌面调试时不可用，手机端启用 record 插件后替换。
class AudioRecorderService {
  Future<bool> hasPermission() async => false;

  Future<void> startStream({
    required void Function(Uint8List chunk) onData,
    int sampleRate = 16000,
  }) async {
    // Windows 桌面不支持录音
  }

  Future<Uint8List> stop() async => Uint8List(0);

  Future<void> dispose() async {}
}
