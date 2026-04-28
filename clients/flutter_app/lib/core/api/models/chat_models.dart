class ChatRequest {
  final String userId;
  final String message;
  final String dialect;
  final String? conversationId;

  ChatRequest({
    required this.userId,
    required this.message,
    this.dialect = 'cmn',
    this.conversationId,
  });

  Map<String, dynamic> toJson() => {
        'user_id': userId,
        'message': message,
        'dialect': dialect,
        if (conversationId != null) 'conversation_id': conversationId,
      };
}

class ChatResponse {
  final String response;
  final String dialect;
  final String? conversationId;

  ChatResponse({
    required this.response,
    required this.dialect,
    this.conversationId,
  });

  factory ChatResponse.fromJson(Map<String, dynamic> json) => ChatResponse(
        response: json['response'] as String,
        dialect: json['dialect'] as String,
        conversationId: json['conversation_id'] as String?,
      );
}

class VoiceResponse {
  final String recognizedText;
  final String normalizedText;
  final String responseText;
  final String dialectDetected;
  final String? audioBase64;
  final String audioFormat;

  VoiceResponse({
    required this.recognizedText,
    required this.normalizedText,
    required this.responseText,
    required this.dialectDetected,
    this.audioBase64,
    this.audioFormat = 'mp3',
  });

  factory VoiceResponse.fromJson(Map<String, dynamic> json) => VoiceResponse(
        recognizedText: json['recognized_text'] as String,
        normalizedText: json['normalized_text'] as String,
        responseText: json['response_text'] as String,
        dialectDetected: json['dialect_detected'] as String,
        audioBase64: json['audio_base64'] as String?,
        audioFormat: json['audio_format'] as String? ?? 'mp3',
      );
}
