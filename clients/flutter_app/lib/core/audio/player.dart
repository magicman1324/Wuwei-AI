import 'dart:typed_data';

import 'package:just_audio/just_audio.dart';

class AudioPlayerService {
  final AudioPlayer _player = AudioPlayer();

  bool get isPlaying => _player.playing;

  Future<void> playBytes(Uint8List audioBytes, {String format = 'mp3'}) async {
    final source = _BytesAudioSource(audioBytes, format);
    await _player.setAudioSource(source);
    await _player.play();
  }

  Future<void> stop() async {
    await _player.stop();
  }

  Future<void> dispose() async {
    await _player.dispose();
  }
}

class _BytesAudioSource extends StreamAudioSource {
  final Uint8List _bytes;
  final String _format;

  _BytesAudioSource(this._bytes, this._format);

  @override
  Future<StreamAudioResponse> request([int? start, int? end]) async {
    start ??= 0;
    end ??= _bytes.length;
    return StreamAudioResponse(
      sourceLength: _bytes.length,
      contentLength: end - start,
      offset: start,
      stream: Stream.value(_bytes.sublist(start, end)),
      contentType: 'audio/$_format',
    );
  }
}
