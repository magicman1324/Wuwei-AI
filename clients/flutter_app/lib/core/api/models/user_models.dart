class CreateUserRequest {
  final String? phone;
  final String? deviceId;
  final String displayName;
  final String dialectPreference;

  CreateUserRequest({
    this.phone,
    this.deviceId,
    this.displayName = '用户',
    this.dialectPreference = 'cmn',
  });

  Map<String, dynamic> toJson() => {
        if (phone != null) 'phone': phone,
        if (deviceId != null) 'device_id': deviceId,
        'display_name': displayName,
        'dialect_preference': dialectPreference,
      };
}

class UserResponse {
  final String id;
  final String displayName;
  final String dialectPreference;
  final double ttsSpeed;
  final double ttsVolume;
  final String fontSize;

  UserResponse({
    required this.id,
    required this.displayName,
    required this.dialectPreference,
    required this.ttsSpeed,
    required this.ttsVolume,
    required this.fontSize,
  });

  factory UserResponse.fromJson(Map<String, dynamic> json) => UserResponse(
        id: json['id'] as String,
        displayName: json['display_name'] as String,
        dialectPreference: json['dialect_preference'] as String,
        ttsSpeed: (json['tts_speed'] as num).toDouble(),
        ttsVolume: (json['tts_volume'] as num).toDouble(),
        fontSize: json['font_size'] as String,
      );
}

class UpdatePreferencesRequest {
  final String? dialectPreference;
  final double? ttsSpeed;
  final double? ttsVolume;
  final String? fontSize;

  UpdatePreferencesRequest({
    this.dialectPreference,
    this.ttsSpeed,
    this.ttsVolume,
    this.fontSize,
  });

  Map<String, dynamic> toJson() {
    final map = <String, dynamic>{};
    if (dialectPreference != null) map['dialect_preference'] = dialectPreference;
    if (ttsSpeed != null) map['tts_speed'] = ttsSpeed;
    if (ttsVolume != null) map['tts_volume'] = ttsVolume;
    if (fontSize != null) map['font_size'] = fontSize;
    return map;
  }
}

class ConversationSummary {
  final String id;
  final String dialectUsed;
  final DateTime startedAt;
  final int messageCount;

  ConversationSummary({
    required this.id,
    required this.dialectUsed,
    required this.startedAt,
    required this.messageCount,
  });

  factory ConversationSummary.fromJson(Map<String, dynamic> json) =>
      ConversationSummary(
        id: json['id'] as String,
        dialectUsed: json['dialect_used'] as String,
        startedAt: DateTime.parse(json['started_at'] as String),
        messageCount: json['message_count'] as int,
      );
}

class ConversationDetail {
  final String id;
  final String dialectUsed;
  final DateTime startedAt;
  final List<MessageItem> messages;

  ConversationDetail({
    required this.id,
    required this.dialectUsed,
    required this.startedAt,
    required this.messages,
  });

  factory ConversationDetail.fromJson(Map<String, dynamic> json) =>
      ConversationDetail(
        id: json['id'] as String,
        dialectUsed: json['dialect_used'] as String,
        startedAt: DateTime.parse(json['started_at'] as String),
        messages: (json['messages'] as List)
            .map((m) => MessageItem.fromJson(m as Map<String, dynamic>))
            .toList(),
      );
}

class MessageItem {
  final String id;
  final String role;
  final String content;
  final String dialect;
  final DateTime createdAt;

  MessageItem({
    required this.id,
    required this.role,
    required this.content,
    required this.dialect,
    required this.createdAt,
  });

  factory MessageItem.fromJson(Map<String, dynamic> json) => MessageItem(
        id: json['id'] as String,
        role: json['role'] as String,
        content: json['content'] as String,
        dialect: json['dialect'] as String,
        createdAt: DateTime.parse(json['created_at'] as String),
      );
}
