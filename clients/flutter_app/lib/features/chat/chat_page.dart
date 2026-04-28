import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../app/theme.dart';
import '../../core/audio/player.dart';
import '../../core/audio/recorder.dart';
import '../../shared/widgets/dialect_picker.dart';
import '../user/user_provider.dart';
import 'chat_provider.dart';
import 'widgets/mic_button.dart';
import 'widgets/thinking_dots.dart';
import 'widgets/typewriter_text.dart';

enum _UiState { idle, listening, thinking, responding }

class ChatPage extends ConsumerStatefulWidget {
  const ChatPage({super.key});

  @override
  ConsumerState<ChatPage> createState() => _ChatPageState();
}

class _ChatPageState extends ConsumerState<ChatPage> {
  final _textController = TextEditingController();
  final _recorder = AudioRecorderService();
  final _player = AudioPlayerService();
  final _audioChunks = <Uint8List>[];
  bool _dismissed = false;
  bool _typingDone = false;

  @override
  void dispose() {
    _textController.dispose();
    _recorder.dispose();
    _player.dispose();
    super.dispose();
  }

  Future<void> _onMicStart() async {
    final hasPermission = await _recorder.hasPermission();
    if (!hasPermission) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            backgroundColor: WuweiColors.bg2,
            content: Text(
              '桌面模式暂不支持录音，请使用文字输入',
              style: TextStyle(color: WuweiColors.fg),
            ),
          ),
        );
      }
      return;
    }

    setState(() => _dismissed = true);
    _audioChunks.clear();
    ref.read(chatProvider.notifier).setRecording(true);
    await _recorder.startStream(onData: (chunk) => _audioChunks.add(chunk));
  }

  Future<void> _onMicStop() async {
    ref.read(chatProvider.notifier).setRecording(false);
    await _recorder.stop();
    if (_audioChunks.isEmpty) return;

    final totalLen = _audioChunks.fold<int>(0, (s, c) => s + c.length);
    final combined = Uint8List(totalLen);
    var offset = 0;
    for (final chunk in _audioChunks) {
      combined.setAll(offset, chunk);
      offset += chunk.length;
    }

    final userId = ref.read(userProvider).valueOrNull?.id;
    if (userId == null) {
      ref.read(chatProvider.notifier).setError('用户尚未初始化，请等待或重启应用');
      ref.invalidate(userProvider);
      return;
    }
    final audioBytes = await ref.read(chatProvider.notifier).sendVoice(combined, userId);
    setState(() {
      _dismissed = false;
      _typingDone = false;
    });

    if (audioBytes != null) {
      ref.read(chatProvider.notifier).setPlaying(true);
      await _player.playBytes(audioBytes);
      ref.read(chatProvider.notifier).setPlaying(false);
    }
  }

  void _onMicCancel() {
    ref.read(chatProvider.notifier).setRecording(false);
    _recorder.stop();
    _audioChunks.clear();
  }

  Future<void> _onSendText() async {
    final text = _textController.text.trim();
    if (text.isEmpty) return;
    final userId = ref.read(userProvider).valueOrNull?.id;
    if (userId == null) {
      ref.read(chatProvider.notifier).setError('用户尚未初始化，请等待或重启应用');
      ref.invalidate(userProvider);
      return;
    }
    _textController.clear();
    setState(() {
      _dismissed = false;
      _typingDone = false;
    });
    await ref.read(chatProvider.notifier).sendText(text, userId);
  }

  _UiState _resolveState(ChatState chat) {
    if (chat.isRecording) return _UiState.listening;
    if (chat.isProcessing) return _UiState.thinking;
    final hasResponse = chat.messages.any((m) => m.role == 'assistant');
    if (hasResponse && !_dismissed) return _UiState.responding;
    return _UiState.idle;
  }

  String? _latestAssistant(ChatState chat) {
    for (var i = chat.messages.length - 1; i >= 0; i--) {
      if (chat.messages[i].role == 'assistant') return chat.messages[i].content;
    }
    return null;
  }

  String? _latestUser(ChatState chat) {
    for (var i = chat.messages.length - 1; i >= 0; i--) {
      if (chat.messages[i].role == 'user') return chat.messages[i].content;
    }
    return null;
  }

  List<String> _historyChips(ChatState chat) {
    final seen = <String>{};
    final out = <String>[];
    for (var i = chat.messages.length - 1; i >= 0; i--) {
      final m = chat.messages[i];
      if (m.role == 'user' && !seen.contains(m.content)) {
        seen.add(m.content);
        out.add(m.content);
        if (out.length >= 5) break;
      }
    }
    if (out.isNotEmpty) out.removeAt(0); // skip current
    return out;
  }

  @override
  Widget build(BuildContext context) {
    final chat = ref.watch(chatProvider);
    final user = ref.watch(userProvider);
    final state = _resolveState(chat);
    final isInputDisabled = chat.isProcessing || chat.isRecording;
    final canSend = _textController.text.trim().isNotEmpty && !isInputDisabled;

    return Scaffold(
      backgroundColor: WuweiColors.bg,
      body: SafeArea(
        child: Column(
          children: [
            // Top: dialect picker (right-aligned), no app bar
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 12, 12, 0),
              child: Row(
                children: [
                  const Spacer(),
                  Theme(
                    data: Theme.of(context).copyWith(
                      canvasColor: WuweiColors.bg2,
                    ),
                    child: DialectPicker(
                      selected: chat.dialect,
                      onChanged: (d) => ref.read(chatProvider.notifier).setDialect(d),
                    ),
                  ),
                ],
              ),
            ),

            // Errors
            if (user.hasError || (!user.isLoading && user.valueOrNull == null))
              _ErrorBanner(
                text: '用户初始化失败：${user.error ?? "未知错误"}',
                onTap: () => ref.invalidate(userProvider),
              ),
            if (chat.error != null) _ErrorBanner(text: chat.error!),

            // Main response area
            Expanded(
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 32),
                child: Center(child: _buildResponseArea(state, chat)),
              ),
            ),

            // Mic button row
            Padding(
              padding: const EdgeInsets.only(bottom: 24, top: 8),
              child: MicButton(
                isRecording: chat.isRecording,
                isProcessing: chat.isProcessing,
                onStart: _onMicStart,
                onStop: _onMicStop,
                onCancel: _onMicCancel,
              ),
            ),

            // Bottom bar: history chips + text input
            _BottomBar(
              chips: _historyChips(chat),
              onChipTap: (q) {
                final messages = chat.messages;
                final idx = messages.lastIndexWhere((m) => m.role == 'user' && m.content == q);
                if (idx >= 0 && idx + 1 < messages.length) {
                  setState(() {
                    _dismissed = false;
                    _typingDone = true;
                  });
                }
              },
              controller: _textController,
              disabled: isInputDisabled,
              canSend: canSend,
              onSend: _onSendText,
              onChanged: () => setState(() {}),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildResponseArea(_UiState state, ChatState chat) {
    switch (state) {
      case _UiState.idle:
        return Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text('无维', style: Theme.of(context).textTheme.labelLarge),
            const SizedBox(height: 14),
            Text(
              '按住下方麦克风，或输入问题',
              style: Theme.of(context).textTheme.displayMedium,
            ),
          ],
        ).animate();
      case _UiState.listening:
        final partial = chat.partialAsr;
        return partial != null && partial.isNotEmpty
            ? Text(
                '「$partial」',
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.displayMedium?.copyWith(
                      fontSize: 22,
                      color: WuweiColors.fgDim,
                    ),
              ).animate()
            : const Text(
                '正在聆听…',
                style: TextStyle(
                  fontSize: 13,
                  letterSpacing: 3.0,
                  color: WuweiColors.fgDim,
                ),
              ).animate();
      case _UiState.thinking:
        final q = _latestUser(chat);
        return Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (q != null)
              Text(
                '「$q」',
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.displayMedium?.copyWith(fontSize: 16),
              ),
            const SizedBox(height: 28),
            const ThinkingDots(),
          ],
        ).animate();
      case _UiState.responding:
        final text = _latestAssistant(chat) ?? '';
        return Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Flexible(
              child: SingleChildScrollView(
                child: TypewriterText(
                  text: text,
                  style: Theme.of(context).textTheme.displayLarge!,
                  onDone: () => setState(() => _typingDone = true),
                ),
              ),
            ),
            if (_typingDone) ...[
              const SizedBox(height: 28),
              OutlinedButton(
                onPressed: () => setState(() => _dismissed = true),
                style: OutlinedButton.styleFrom(
                  minimumSize: const Size(0, 36),
                  padding: const EdgeInsets.symmetric(horizontal: 22),
                  side: const BorderSide(color: WuweiColors.bg3),
                  foregroundColor: WuweiColors.fgDim,
                  textStyle: const TextStyle(fontSize: 12, letterSpacing: 2.5),
                  shape: const StadiumBorder(),
                ),
                child: const Text('完成'),
              ),
            ],
          ],
        ).animate();
    }
  }
}

class _ErrorBanner extends StatelessWidget {
  final String text;
  final VoidCallback? onTap;
  const _ErrorBanner({required this.text, this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: double.infinity,
        color: const Color(0x33D9665B),
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
        child: Text(
          onTap != null ? '$text（点击重试）' : text,
          textAlign: TextAlign.center,
          style: const TextStyle(color: Color(0xFFE89A92), fontSize: 13),
        ),
      ),
    );
  }
}

class _BottomBar extends StatelessWidget {
  final List<String> chips;
  final ValueChanged<String> onChipTap;
  final TextEditingController controller;
  final bool disabled;
  final bool canSend;
  final VoidCallback onSend;
  final VoidCallback onChanged;

  const _BottomBar({
    required this.chips,
    required this.onChipTap,
    required this.controller,
    required this.disabled,
    required this.canSend,
    required this.onSend,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        border: Border(top: BorderSide(color: WuweiColors.bg2)),
      ),
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 16),
      child: Column(
        children: [
          if (chips.isNotEmpty)
            Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: SizedBox(
                height: 28,
                child: ListView.separated(
                  scrollDirection: Axis.horizontal,
                  itemCount: chips.length,
                  separatorBuilder: (_, __) => const SizedBox(width: 8),
                  itemBuilder: (_, i) => InkWell(
                    onTap: () => onChipTap(chips[i]),
                    borderRadius: BorderRadius.circular(20),
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 4),
                      decoration: BoxDecoration(
                        border: Border.all(color: WuweiColors.bg3),
                        borderRadius: BorderRadius.circular(20),
                      ),
                      constraints: const BoxConstraints(maxWidth: 200),
                      child: Text(
                        chips[i],
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(fontSize: 12, color: WuweiColors.fgDim),
                      ),
                    ),
                  ),
                ),
              ),
            ),
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: controller,
                  enabled: !disabled,
                  style: const TextStyle(color: WuweiColors.fg, fontSize: 14),
                  decoration: const InputDecoration(
                    hintText: '或者直接输入…',
                    isDense: true,
                  ),
                  textInputAction: TextInputAction.send,
                  onChanged: (_) => onChanged(),
                  onSubmitted: (_) => onSend(),
                ),
              ),
              const SizedBox(width: 8),
              OutlinedButton(
                onPressed: canSend ? onSend : null,
                style: OutlinedButton.styleFrom(
                  minimumSize: const Size(64, 44),
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  side: BorderSide(
                    color: canSend ? WuweiColors.accent : WuweiColors.bg3,
                  ),
                  foregroundColor: canSend ? WuweiColors.accent : WuweiColors.fgDim,
                  textStyle: const TextStyle(fontSize: 13, letterSpacing: 1.5),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                ),
                child: const Text('发送'),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

extension on Widget {
  Widget animate() => AnimatedSwitcher(
        duration: const Duration(milliseconds: 320),
        switchInCurve: Curves.easeOut,
        transitionBuilder: (child, anim) => FadeTransition(
          opacity: anim,
          child: SlideTransition(
            position: Tween<Offset>(begin: const Offset(0, 0.06), end: Offset.zero).animate(anim),
            child: child,
          ),
        ),
        child: KeyedSubtree(key: ValueKey(this), child: this),
      );
}
