import 'package:shared_preferences/shared_preferences.dart';

class LocalStorage {
  static const _keyUserId = 'user_id';
  static const _keyDeviceId = 'device_id';
  static const _keyDialect = 'dialect_preference';
  static const _keyOnboarded = 'onboarding_completed';
  static const _keyTtsSpeed = 'tts_speed';
  static const _keyTtsVolume = 'tts_volume';
  static const _keyFontSize = 'font_size';

  late SharedPreferences _prefs;

  Future<void> init() async {
    _prefs = await SharedPreferences.getInstance();
  }

  // ── User Identity ──

  String? get userId => _prefs.getString(_keyUserId);
  set userId(String? v) => v == null
      ? _prefs.remove(_keyUserId)
      : _prefs.setString(_keyUserId, v);

  String? get deviceId => _prefs.getString(_keyDeviceId);
  set deviceId(String? v) => v == null
      ? _prefs.remove(_keyDeviceId)
      : _prefs.setString(_keyDeviceId, v);

  // ── Preferences ──

  String get dialectPreference => _prefs.getString(_keyDialect) ?? 'cmn';
  set dialectPreference(String v) => _prefs.setString(_keyDialect, v);

  double get ttsSpeed => _prefs.getDouble(_keyTtsSpeed) ?? 0.85;
  set ttsSpeed(double v) => _prefs.setDouble(_keyTtsSpeed, v);

  double get ttsVolume => _prefs.getDouble(_keyTtsVolume) ?? 1.2;
  set ttsVolume(double v) => _prefs.setDouble(_keyTtsVolume, v);

  String get fontSize => _prefs.getString(_keyFontSize) ?? 'large';
  set fontSize(String v) => _prefs.setString(_keyFontSize, v);

  // ── Onboarding ──

  bool get onboardingCompleted => _prefs.getBool(_keyOnboarded) ?? false;
  set onboardingCompleted(bool v) => _prefs.setBool(_keyOnboarded, v);
}
