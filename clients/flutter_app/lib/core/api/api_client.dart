import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';

import '../constants.dart';
import 'models/chat_models.dart';
import 'models/user_models.dart';

class ApiClient {
  late final Dio _dio;

  ApiClient({String? baseUrl}) {
    _dio = Dio(BaseOptions(
      baseUrl: baseUrl ?? ApiConstants.baseUrl,
      connectTimeout: ApiConstants.timeout,
      receiveTimeout: ApiConstants.timeout,
    ));
    _dio.interceptors.add(LogInterceptor(
      requestHeader: false,
      responseHeader: false,
      requestBody: true,
      responseBody: true,
      logPrint: (o) => print('[DIO] $o'),
    ));
  }

  // ── Health ──

  Future<Map<String, dynamic>> healthCheck() async {
    final resp = await _dio.get('/health');
    return resp.data as Map<String, dynamic>;
  }

  // ── Chat ──

  Future<ChatResponse> chat(ChatRequest req) async {
    final resp = await _dio.post('/chat', data: req.toJson());
    return ChatResponse.fromJson(resp.data as Map<String, dynamic>);
  }

  // ── Voice ──

  Future<VoiceResponse> voiceChat({
    required Uint8List audioData,
    String userId = '',
    String dialectHint = '',
    String audioFormat = 'pcm',
    int sampleRate = 16000,
  }) async {
    final formData = FormData.fromMap({
      'audio': MultipartFile.fromBytes(audioData, filename: 'audio.$audioFormat'),
      'user_id': userId,
      'dialect_hint': dialectHint,
      'audio_format': audioFormat,
      'sample_rate': sampleRate.toString(),
    });
    final resp = await _dio.post('/voice', data: formData);
    return VoiceResponse.fromJson(resp.data as Map<String, dynamic>);
  }

  // ── User ──

  Future<UserResponse> createUser(CreateUserRequest req) async {
    final resp = await _dio.post('/users', data: req.toJson());
    return UserResponse.fromJson(resp.data as Map<String, dynamic>);
  }

  Future<UserResponse> getUser(String userId) async {
    final resp = await _dio.get('/users/$userId');
    return UserResponse.fromJson(resp.data as Map<String, dynamic>);
  }

  Future<UserResponse> updatePreferences(
      String userId, UpdatePreferencesRequest req) async {
    final resp =
        await _dio.patch('/users/$userId/preferences', data: req.toJson());
    return UserResponse.fromJson(resp.data as Map<String, dynamic>);
  }

  // ── Conversations ──

  Future<List<ConversationSummary>> listConversations(String userId,
      {int limit = 50}) async {
    final resp =
        await _dio.get('/conversations/$userId', queryParameters: {'limit': limit});
    return (resp.data as List)
        .map((e) => ConversationSummary.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<ConversationDetail> getConversation(
      String userId, String conversationId) async {
    final resp = await _dio.get('/conversations/$userId/$conversationId');
    return ConversationDetail.fromJson(resp.data as Map<String, dynamic>);
  }

  Future<void> deleteConversation(
      String userId, String conversationId) async {
    await _dio.delete('/conversations/$userId/$conversationId');
  }
}
