import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';

import 'package:web_socket_channel/web_socket_channel.dart';

import '../constants.dart';

sealed class WsMessage {}

class WsAsrPartial extends WsMessage {
  final String text;
  WsAsrPartial(this.text);
}

class WsAsrFinal extends WsMessage {
  final String text;
  final String dialectDetected;
  WsAsrFinal(this.text, this.dialectDetected);
}

class WsLlmChunk extends WsMessage {
  final String text;
  WsLlmChunk(this.text);
}

class WsTtsAudio extends WsMessage {
  final Uint8List audioBytes;
  final String format;
  WsTtsAudio(this.audioBytes, this.format);
}

class WsDone extends WsMessage {
  final String fullResponse;
  WsDone(this.fullResponse);
}

class WsError extends WsMessage {
  final String reason;
  WsError(this.reason);
}

class VoiceStreamClient {
  WebSocketChannel? _channel;
  final String userId;
  final DialectCode dialect;
  final String baseUrl;

  StreamController<WsMessage>? _controller;
  bool _closed = false;

  VoiceStreamClient({
    required this.userId,
    required this.dialect,
    String? baseUrl,
  }) : baseUrl = baseUrl ?? ApiConstants.wsUrl;

  Stream<WsMessage> get messages =>
      _controller?.stream ?? const Stream.empty();

  bool get isConnected => _channel != null && !_closed;

  Future<void> connect() async {
    _closed = false;
    _controller = StreamController<WsMessage>.broadcast();

    final uri = Uri.parse('$baseUrl?user_id=$userId&dialect=${dialect.code}');
    _channel = WebSocketChannel.connect(uri);

    _channel!.stream.listen(
      (data) {
        if (data is String) {
          _handleMessage(json.decode(data) as Map<String, dynamic>);
        }
      },
      onError: (e) {
        _controller?.add(WsError(e.toString()));
      },
      onDone: () {
        _closed = true;
        _controller?.close();
      },
    );
  }

  void sendAudio(Uint8List pcmData) {
    _channel?.sink.add(pcmData);
  }

  void endUtterance() {
    _channel?.sink.add(json.encode({'type': 'end'}));
  }

  Future<void> close() async {
    _closed = true;
    _channel?.sink.add(json.encode({'type': 'close'}));
    await _channel?.sink.close();
    _channel = null;
    await _controller?.close();
    _controller = null;
  }

  void _handleMessage(Map<String, dynamic> msg) {
    final type = msg['type'] as String?;
    switch (type) {
      case 'asr_partial':
        _controller?.add(WsAsrPartial(msg['text'] as String));
      case 'asr_final':
        _controller?.add(
            WsAsrFinal(msg['text'] as String, msg['dialect_detected'] as String));
      case 'llm_chunk':
        _controller?.add(WsLlmChunk(msg['text'] as String));
      case 'tts_audio':
        final bytes = base64Decode(msg['audio'] as String);
        _controller?.add(WsTtsAudio(
            Uint8List.fromList(bytes), msg['format'] as String? ?? 'mp3'));
      case 'done':
        _controller?.add(WsDone(msg['full_response'] as String? ?? ''));
      case 'error':
        _controller?.add(WsError(msg['reason'] as String? ?? '未知错误'));
    }
  }
}
