import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

class MicButton extends StatefulWidget {
  final bool isRecording;
  final bool isProcessing;
  final VoidCallback onStart;
  final VoidCallback onStop;
  final VoidCallback onCancel;

  const MicButton({
    super.key,
    required this.isRecording,
    required this.isProcessing,
    required this.onStart,
    required this.onStop,
    required this.onCancel,
  });

  @override
  State<MicButton> createState() => _MicButtonState();
}

class _MicButtonState extends State<MicButton>
    with SingleTickerProviderStateMixin {
  late final AnimationController _pulse;
  double _dragY = 0;

  @override
  void initState() {
    super.initState();
    _pulse = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1000),
    );
  }

  @override
  void didUpdateWidget(MicButton old) {
    super.didUpdateWidget(old);
    if (widget.isRecording && !old.isRecording) {
      _pulse.repeat(reverse: true);
    } else if (!widget.isRecording && old.isRecording) {
      _pulse.stop();
      _pulse.reset();
    }
  }

  @override
  void dispose() {
    _pulse.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final color = Theme.of(context).colorScheme.primary;

    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        if (widget.isRecording)
          Text(
            _dragY < -60 ? '松开取消' : '松开发送',
            style: TextStyle(
              fontSize: 18,
              color: _dragY < -60 ? Colors.red : Colors.grey[600],
            ),
          ),
        if (widget.isProcessing)
          const Padding(
            padding: EdgeInsets.only(bottom: 8),
            child: Text('正在处理...', style: TextStyle(fontSize: 18)),
          ),
        const SizedBox(height: 8),
        GestureDetector(
          onLongPressStart: (_) {
            if (!widget.isProcessing) {
              HapticFeedback.mediumImpact();
              widget.onStart();
            }
          },
          onLongPressMoveUpdate: (details) {
            setState(() => _dragY = details.localOffsetFromOrigin.dy);
          },
          onLongPressEnd: (_) {
            if (_dragY < -60) {
              widget.onCancel();
            } else {
              widget.onStop();
            }
            setState(() => _dragY = 0);
          },
          child: AnimatedBuilder(
            animation: _pulse,
            builder: (_, child) {
              final scale =
                  widget.isRecording ? 1.0 + _pulse.value * 0.1 : 1.0;
              return Transform.scale(scale: scale, child: child);
            },
            child: Container(
              width: 96,
              height: 96,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: widget.isRecording
                    ? Colors.red
                    : widget.isProcessing
                        ? Colors.grey
                        : color,
                boxShadow: [
                  BoxShadow(
                    color: (widget.isRecording ? Colors.red : color)
                        .withOpacity(0.3),
                    blurRadius: 16,
                    spreadRadius: 2,
                  ),
                ],
              ),
              child: Icon(
                widget.isRecording ? Icons.stop : Icons.mic,
                size: 48,
                color: Colors.white,
              ),
            ),
          ),
        ),
        const SizedBox(height: 8),
        Text(
          widget.isRecording ? '松开发送' : '按住说话',
          style: TextStyle(
            fontSize: 18,
            color: Colors.grey[600],
          ),
        ),
      ],
    );
  }
}
