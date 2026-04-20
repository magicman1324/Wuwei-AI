import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/audio/player.dart';
import '../../core/audio/recorder.dart';
import '../../core/constants.dart';
import '../../shared/widgets/dialect_picker.dart';
import 'chat_provider.dart';
import 'widgets/chat_bubble.dart';
import 'widgets/mic_button.dart';

class ChatPage extends ConsumerStatefulWidget {
  const ChatPage({super.key});

  @override
  ConsumerState<ChatPage> createState() => _ChatPageState();
}

class _ChatPageState extends ConsumerState<ChatPage> {
  final _textController = TextEditingController();
  final _scrollController = ScrollController();
  final _recorder = AudioRecorderService();
  final _player = AudioPlayerService();
  final _audioChunks = <Uint8List>[];
  bool _showTextInput = false;

  @override
  void dispose() {
    _textController.dispose();
    _scrollController.dispose();
    _recorder.dispose();
    _player.dispose();
    super.dispose();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  Future<void> _onMicStart() async {
    final hasPermission = await _recorder.hasPermission();
    if (!hasPermission) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('需要麦克风权限才能录音', style: TextStyle(fontSize: 18)),
          ),
        );
      }
      return;
    }

    _audioChunks.clear();
    ref.read(chatProvider.notifier).setRecording(true);
    await _recorder.startStream(
      onData: (chunk) => _audioChunks.add(chunk),
    );
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

    final userId = 'anonymous'; // TODO: from local storage
    final audioBytes =
        await ref.read(chatProvider.notifier).sendVoice(combined, userId);

    _scrollToBottom();

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

    _textController.clear();
    final userId = 'anonymous';
    await ref.read(chatProvider.notifier).sendText(text, userId);
    _scrollToBottom();
  }

  @override
  Widget build(BuildContext context) {
    final chat = ref.watch(chatProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('🌿 无维AI'),
        actions: [
          DialectPicker(
            selected: chat.dialect,
            onChanged: (d) => ref.read(chatProvider.notifier).setDialect(d),
          ),
          const SizedBox(width: 12),
        ],
      ),
      body: Column(
        children: [
          // Error banner
          if (chat.error != null)
            Container(
              width: double.infinity,
              color: Colors.red[50],
              padding: const EdgeInsets.all(12),
              child: Text(
                chat.error!,
                style: const TextStyle(fontSize: 18, color: Colors.red),
                textAlign: TextAlign.center,
              ),
            ),

          // Chat messages
          Expanded(
            child: chat.messages.isEmpty
                ? Center(
                    child: Text(
                      '按住下方麦克风开始聊天',
                      style: TextStyle(
                          fontSize: 22, color: Colors.grey[500]),
                    ),
                  )
                : ListView.builder(
                    controller: _scrollController,
                    padding: const EdgeInsets.only(top: 12, bottom: 12),
                    itemCount: chat.messages.length,
                    itemBuilder: (_, i) {
                      final msg = chat.messages[i];
                      return ChatBubble(
                        content: msg.content,
                        isUser: msg.role == 'user',
                        onReplay: msg.role == 'assistant' ? () {} : null,
                      );
                    },
                  ),
          ),

          // Partial ASR text
          if (chat.partialAsr != null)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Text(
                '识别中: ${chat.partialAsr}',
                style: TextStyle(fontSize: 18, color: Colors.grey[600]),
              ),
            ),

          // Input area
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: Column(
                children: [
                  // Mic button
                  if (!_showTextInput)
                    MicButton(
                      isRecording: chat.isRecording,
                      isProcessing: chat.isProcessing,
                      onStart: _onMicStart,
                      onStop: _onMicStop,
                      onCancel: _onMicCancel,
                    ),

                  // Text input (toggle)
                  if (_showTextInput)
                    Row(
                      children: [
                        Expanded(
                          child: TextField(
                            controller: _textController,
                            style: const TextStyle(fontSize: 20),
                            decoration: const InputDecoration(
                              hintText: '输入消息...',
                            ),
                            onSubmitted: (_) => _onSendText(),
                          ),
                        ),
                        const SizedBox(width: 8),
                        SizedBox(
                          height: 56,
                          width: 80,
                          child: ElevatedButton(
                            onPressed: chat.isProcessing ? null : _onSendText,
                            child: const Text('发送'),
                          ),
                        ),
                      ],
                    ),

                  const SizedBox(height: 8),
                  // Toggle text/voice mode
                  TextButton.icon(
                    onPressed: () =>
                        setState(() => _showTextInput = !_showTextInput),
                    icon: Icon(
                      _showTextInput ? Icons.mic : Icons.keyboard,
                      size: 24,
                    ),
                    label: Text(
                      _showTextInput ? '切换语音' : '切换键盘',
                      style: const TextStyle(fontSize: 16),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
