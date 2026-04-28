import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:uuid/uuid.dart';

import '../../core/api/api_client.dart';
import '../../core/api/models/user_models.dart';
import '../../core/storage/local_storage.dart';
import '../chat/chat_provider.dart';

/// 全局 LocalStorage 单例。启动时由 main() 初始化。
final localStorageProvider = Provider<LocalStorage>((ref) {
  throw UnimplementedError('LocalStorage must be overridden in main()');
});

/// 用户状态：首次启动生成 device_id → 创建 User → 持久化 user_id；
/// 后续启动直接从本地读取 user_id。
class UserNotifier extends AsyncNotifier<UserResponse> {
  @override
  Future<UserResponse> build() async {
    final storage = ref.read(localStorageProvider);
    final api = ref.read(apiClientProvider);

    var userId = storage.userId;
    var deviceId = storage.deviceId;

    // 1. 已有 user_id：尝试拉取
    if (userId != null) {
      try {
        return await api.getUser(userId);
      } catch (_) {
        // 本地存的 user_id 在后端已不存在（例如后端重建数据库），重新注册
        storage.userId = null;
      }
    }

    // 2. 无 user_id：生成 device_id（若无）→ 创建 User
    deviceId ??= const Uuid().v4();
    storage.deviceId = deviceId;

    final user = await api.createUser(CreateUserRequest(
      deviceId: deviceId,
      dialectPreference: storage.dialectPreference,
    ));
    storage.userId = user.id;
    return user;
  }

  /// 手动刷新（例如设置页修改偏好后）。
  Future<void> refresh() async {
    final api = ref.read(apiClientProvider);
    final storage = ref.read(localStorageProvider);
    final userId = storage.userId;
    if (userId == null) {
      ref.invalidateSelf();
      return;
    }
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(() => api.getUser(userId));
  }
}

final userProvider =
    AsyncNotifierProvider<UserNotifier, UserResponse>(UserNotifier.new);
