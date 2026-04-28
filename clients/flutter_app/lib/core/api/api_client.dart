import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:dio/io.dart';

import '../constants.dart';
import 'models/chat_models.dart';
import 'models/user_models.dart';

/// 文件日志：Windows 调试通道失败时也能看到 Dio 的请求/响应。
class _FileLogger {
  static File? _file;
  static bool _initialized = false;

  static void _init() {
    if (_initialized) return;
    _initialized = true;
    try {
      _file = File('${Directory.current.path}${Platform.pathSeparator}dio_debug.log');
      _file!.writeAsStringSync(
        '\n=== Session: ${DateTime.now()} | baseUrl=${ApiConstants.baseUrl} ===\n',
        mode: FileMode.append,
      );
    } catch (e) {
      print('[DIO-LOG] init failed: $e');
    }
  }

  static void log(Object msg) {
    _init();
    final line = '[${DateTime.now()}] $msg';
    print(line);
    try {
      _file?.writeAsStringSync('$line\n', mode: FileMode.append);
    } catch (_) {}
  }
}

class ApiClient {
  late final Dio _dio;

  ApiClient({String? baseUrl}) {
    _FileLogger.log('ApiClient init baseUrl=${baseUrl ?? ApiConstants.baseUrl}');

    _dio = Dio(BaseOptions(
      baseUrl: baseUrl ?? ApiConstants.baseUrl,
      connectTimeout: ApiConstants.timeout,
      receiveTimeout: ApiConstants.timeout,
      sendTimeout: ApiConstants.timeout,
      contentType: 'application/json',
      responseType: ResponseType.json,
    ));

    // 关键：强制绕过 Windows 系统代理（Dart HttpClient 默认会走 WinHTTP 代理）
    _dio.httpClientAdapter = IOHttpClientAdapter(
      createHttpClient: () {
        final client = HttpClient();
        client.findProxy = (uri) {
          _FileLogger.log('findProxy($uri) -> DIRECT');
          return 'DIRECT';
        };
        client.badCertificateCallback = (cert, host, port) => true;
        return client;
      },
    );

    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) {
        _FileLogger.log('→ ${options.method} ${options.uri}');
        _FileLogger.log('  body=${options.data}');
        handler.next(options);
      },
      onResponse: (response, handler) {
        _FileLogger.log('← ${response.statusCode} ${response.requestOptions.uri}');
        _FileLogger.log('  data=${response.data}');
        handler.next(response);
      },
      onError: (err, handler) {
        _FileLogger.log('✗ ${err.type} ${err.requestOptions.uri}');
        _FileLogger.log('  status=${err.response?.statusCode}');
        _FileLogger.log('  response=${err.response?.data}');
        _FileLogger.log('  message=${err.message}');
        handler.next(err);
      },
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

/// 用于从 UI 访问日志。
String get debugLogPath =>
    '${Directory.current.path}${Platform.pathSeparator}dio_debug.log';

/// 不确定编码下简单使用：dio 返回的 data 可能是 String 或 Map。
String formatDioError(DioException e) {
  final uri = e.requestOptions.uri.toString();
  final status = e.response?.statusCode;
  final data = e.response?.data;
  final body = data is Map
      ? (data['detail']?.toString() ?? jsonEncode(data))
      : data?.toString() ?? e.message ?? 'unknown';
  return '[$status] $uri\n$body';
}
