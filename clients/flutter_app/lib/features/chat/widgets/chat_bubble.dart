import 'package:flutter/material.dart';

class ChatBubble extends StatelessWidget {
  final String content;
  final bool isUser;
  final VoidCallback? onReplay;

  const ChatBubble({
    super.key,
    required this.content,
    required this.isUser,
    this.onReplay,
  });

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;

    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        constraints: BoxConstraints(
          maxWidth: MediaQuery.of(context).size.width * 0.78,
        ),
        margin: const EdgeInsets.symmetric(vertical: 6, horizontal: 12),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        decoration: BoxDecoration(
          color: isUser
              ? scheme.primary.withOpacity(0.12)
              : scheme.surfaceContainerHighest,
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(20),
            topRight: const Radius.circular(20),
            bottomLeft: Radius.circular(isUser ? 20 : 4),
            bottomRight: Radius.circular(isUser ? 4 : 20),
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              content,
              style: const TextStyle(fontSize: 20, height: 1.8),
            ),
            if (!isUser && onReplay != null) ...[
              const SizedBox(height: 6),
              GestureDetector(
                onTap: onReplay,
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.volume_up, size: 22, color: scheme.primary),
                    const SizedBox(width: 4),
                    Text('重播',
                        style: TextStyle(
                            fontSize: 16, color: scheme.primary)),
                  ],
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
