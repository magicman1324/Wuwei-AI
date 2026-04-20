import 'dart:async';
import 'dart:typed_data';

import 'package:record/record.dart';

class AudioRecorderService {
  final AudioRecorder _recorder = AudioRecorder();
  StreamSubscription? _streamSub;

  Future<bool> hasPermission() => _recorder.hasPermission();

  Future<void> startStream({
    required void Function(Uint8List chunk) onData,
    int sampleRate = 16000,
  }) async {
    final stream = await _recorder.startStream(RecordConfig(
      encoder: AudioEncoder.pcm16bits,
      sampleRate: sampleRate,
      numChannels: 1,
      bitRate: 256000,
    ));
    _streamSub = stream.listen(onData);
  }

  Future<Uint8List?> startAndCollect({int sampleRate = 16000}) async {
    final chunks = <Uint8List>[];
    await startStream(
      onData: (chunk) => chunks.add(chunk),
      sampleRate: sampleRate,
    );
    return null; // call stopAndCollect() later
  }

  Future<Uint8List> stop() async {
    await _streamSub?.cancel();
    _streamSub = null;
    final path = await _recorder.stop();
    return Uint8List(0);
  }

  Future<void> dispose() async {
    await _streamSub?.cancel();
    await _recorder.dispose();
  }
}
