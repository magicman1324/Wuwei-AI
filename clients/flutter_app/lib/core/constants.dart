class ApiConstants {
  // Windows 桌面 / Web 调试用 localhost
  // Android 模拟器用 10.0.2.2，真机用实际 IP
  static const baseUrl = 'http://localhost:8000/api/v1';
  static const wsUrl = 'ws://localhost:8000/api/v1/ws/voice-stream';

  static const timeout = Duration(seconds: 15);
  static const wsReconnectIntervals = [1, 2, 4, 8];
}

enum DialectCode {
  mandarin('cmn', '普通话'),
  cantonese('yue', '粤语'),
  sichuan('cmn-sichuan', '四川话');

  final String code;
  final String label;
  const DialectCode(this.code, this.label);

  static DialectCode fromCode(String c) =>
      DialectCode.values.firstWhere((d) => d.code == c,
          orElse: () => DialectCode.mandarin);
}
