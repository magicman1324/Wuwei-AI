import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api_client.dart';
import '../../core/api/models/user_models.dart';
import '../chat/chat_provider.dart';
import '../user/user_provider.dart';

class HistoryPage extends ConsumerStatefulWidget {
  const HistoryPage({super.key});

  @override
  ConsumerState<HistoryPage> createState() => _HistoryPageState();
}

class _HistoryPageState extends ConsumerState<HistoryPage> {
  List<ConversationSummary>? _conversations;
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final userId = ref.read(userProvider).valueOrNull?.id;
      if (userId == null) {
        setState(() {
          _error = '用户尚未初始化';
          _loading = false;
        });
        return;
      }
      final api = ref.read(apiClientProvider);
      final list = await api.listConversations(userId);
      setState(() {
        _conversations = list;
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = '加载失败，请检查网络';
        _loading = false;
      });
    }
  }

  String _formatDate(DateTime dt) {
    final now = DateTime.now();
    final diff = now.difference(dt);
    if (diff.inMinutes < 60) return '${diff.inMinutes}分钟前';
    if (diff.inHours < 24) return '${diff.inHours}小时前';
    if (diff.inDays < 7) return '${diff.inDays}天前';
    return '${dt.month}月${dt.day}日';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('对话历史')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(_error!,
                          style: const TextStyle(fontSize: 20, color: Colors.red)),
                      const SizedBox(height: 16),
                      ElevatedButton(
                        onPressed: _load,
                        child: const Text('重试'),
                      ),
                    ],
                  ),
                )
              : _conversations == null || _conversations!.isEmpty
                  ? Center(
                      child: Text(
                        '暂无对话记录',
                        style: TextStyle(fontSize: 22, color: Colors.grey[500]),
                      ),
                    )
                  : RefreshIndicator(
                      onRefresh: _load,
                      child: ListView.separated(
                        padding: const EdgeInsets.all(16),
                        itemCount: _conversations!.length,
                        separatorBuilder: (_, __) => const Divider(height: 1),
                        itemBuilder: (_, i) {
                          final conv = _conversations![i];
                          return ListTile(
                            contentPadding: const EdgeInsets.symmetric(
                                vertical: 8, horizontal: 8),
                            title: Text(
                              '${conv.messageCount} 条消息',
                              style: const TextStyle(fontSize: 22),
                            ),
                            subtitle: Text(
                              _formatDate(conv.startedAt),
                              style: const TextStyle(fontSize: 18),
                            ),
                            trailing: const Icon(Icons.chevron_right, size: 32),
                            onTap: () {
                              // TODO: navigate to detail page
                            },
                          );
                        },
                      ),
                    ),
    );
  }
}
