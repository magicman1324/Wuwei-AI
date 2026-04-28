import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api_client.dart';
import '../../core/api/models/chat_models.dart';
import '../../core/constants.dart';

final apiClientProvider = Provider((ref) => ApiClient());

class ChatMessage {
  final String role; // "user" | "assistant"
  final String content;
  final Uint8List? audioBytes;

  ChatMessage({required this.role, required this.content, this.audioBytes});
}

class ChatState {
  final List<ChatMessage> messages;
  final bool isRecording;
  final bool isProcessing;
  final bool isPlaying;
  final String? partialAsr;
  final DialectCode dialect;
  final String? error;

  const ChatState({
    this.messages = const [],
    this.isRecording = false,
    this.isProcessing = false,
    this.isPlaying = false,
    this.partialAsr,
    this.dialect = DialectCode.mandarin,
    this.error,
  });

  ChatState copyWith({
    List<ChatMessage>? messages,
    bool? isRecording,
    bool? isProcessing,
    bool? isPlaying,
    String? partialAsr,
    DialectCode? dialect,
    String? error,
  }) =>
      ChatState(
        messages: messages ?? this.messages,
        isRecording: isRecording ?? this.isRecording,
        isProcessing: isProcessing ?? this.isProcessing,
        isPlaying: isPlaying ?? this.isPlaying,
        partialAsr: partialAsr,
        dialect: dialect ?? this.dialect,
        error: error,
      );
}

class ChatNotifier extends Notifier<ChatState> {
  @override
  ChatState build() => const ChatState();

  void setDialect(DialectCode dialect) {
    state = state.copyWith(dialect: dialect);
  }

  void setRecording(bool v) {
    state = state.copyWith(isRecording: v);
  }

  void setPlaying(bool v) {
    state = state.copyWith(isPlaying: v);
  }

  void setError(String msg) {
    state = state.copyWith(error: msg);
  }

  Future<void> sendText(String text, String userId) async {
    if (text.trim().isEmpty) return;

    state = state.copyWith(
      messages: [
        ...state.messages,
        ChatMessage(role: 'user', content: text),
      ],
      isProcessing: true,
      error: null,
    );

    try {
      final api = ref.read(apiClientProvider);
      final resp = await api.chat(ChatRequest(
        userId: userId,
        message: text,
        dialect: state.dialect.code,
      ));
      state = state.copyWith(
        messages: [
          ...state.messages,
          ChatMessage(role: 'assistant', content: resp.response),
        ],
        isProcessing: false,
      );
    } on DioException catch (e) {
      state = state.copyWith(
        isProcessing: false,
        error: '发送失败:\n${formatDioError(e)}',
      );
    } catch (e) {
      state = state.copyWith(
        isProcessing: false,
        error: '发送失败: $e',
      );
    }
  }

  Future<Uint8List?> sendVoice(Uint8List pcmData, String userId) async {
    state = state.copyWith(isProcessing: true, error: null);

    try {
      final api = ref.read(apiClientProvider);
      final resp = await api.voiceChat(
        audioData: pcmData,
        userId: userId,
        dialectHint: state.dialect.code,
        audioFormat: 'pcm',
        sampleRate: 16000,
      );

      state = state.copyWith(
        messages: [
          ...state.messages,
          ChatMessage(role: 'user', content: resp.recognizedText),
          ChatMessage(role: 'assistant', content: resp.responseText),
        ],
        isProcessing: false,
      );

      if (resp.audioBase64 != null && resp.audioBase64!.isNotEmpty) {
        return Uint8List.fromList(base64Decode(resp.audioBase64!));
      }
      return null;
    } catch (e) {
      state = state.copyWith(
        isProcessing: false,
        error: '语音识别失败，请重试',
      );
      return null;
    }
  }
}

final chatProvider =
    NotifierProvider<ChatNotifier, ChatState>(ChatNotifier.new);
