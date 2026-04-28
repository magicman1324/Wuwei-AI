import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../../app/theme.dart';

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

class _MicButtonState extends State<MicButton> with TickerProviderStateMixin {
  late final AnimationController _ringCtrl;
  late final AnimationController _spinCtrl;
  late final AnimationController _breatheCtrl;
  late final AnimationController _waveCtrl;
  double _dragY = 0;

  @override
  void initState() {
    super.initState();
    _ringCtrl = AnimationController(vsync: this, duration: const Duration(milliseconds: 1400));
    _spinCtrl = AnimationController(vsync: this, duration: const Duration(milliseconds: 1200));
    _breatheCtrl = AnimationController(vsync: this, duration: const Duration(milliseconds: 4000))
      ..repeat(reverse: true);
    _waveCtrl = AnimationController(vsync: this, duration: const Duration(milliseconds: 900));
    _syncAnimations();
  }

  @override
  void didUpdateWidget(covariant MicButton old) {
    super.didUpdateWidget(old);
    if (widget.isRecording != old.isRecording || widget.isProcessing != old.isProcessing) {
      _syncAnimations();
    }
  }

  void _syncAnimations() {
    if (widget.isRecording) {
      _ringCtrl.repeat();
      _waveCtrl.repeat();
    } else {
      _ringCtrl.stop();
      _ringCtrl.reset();
      _waveCtrl.stop();
      _waveCtrl.reset();
    }
    if (widget.isProcessing) {
      _spinCtrl.repeat();
    } else {
      _spinCtrl.stop();
      _spinCtrl.reset();
    }
  }

  @override
  void dispose() {
    _ringCtrl.dispose();
    _spinCtrl.dispose();
    _breatheCtrl.dispose();
    _waveCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final isIdle = !widget.isRecording && !widget.isProcessing;

    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        SizedBox(
          width: 132,
          height: 132,
          child: Stack(
            alignment: Alignment.center,
            children: [
              // Pulse rings (listening)
              if (widget.isRecording) ...[
                _PulseRing(controller: _ringCtrl, maxScale: 1.7, fromOpacity: 0.6),
                _PulseRing(controller: _ringCtrl, maxScale: 2.1, fromOpacity: 0.4, delay: 0.28),
              ],
              // Spinning arc (thinking)
              if (widget.isProcessing)
                AnimatedBuilder(
                  animation: _spinCtrl,
                  builder: (_, __) => Transform.rotate(
                    angle: _spinCtrl.value * 2 * math.pi,
                    child: CustomPaint(
                      size: const Size(116, 116),
                      painter: _ArcPainter(),
                    ),
                  ),
                ),
              // Breathing button
              GestureDetector(
                onLongPressStart: (_) {
                  if (!widget.isProcessing) {
                    HapticFeedback.mediumImpact();
                    widget.onStart();
                  }
                },
                onLongPressMoveUpdate: (d) {
                  setState(() => _dragY = d.localOffsetFromOrigin.dy);
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
                  animation: _breatheCtrl,
                  builder: (_, child) {
                    final scale = isIdle ? 1.0 + _breatheCtrl.value * 0.04 : 1.0;
                    return Transform.scale(scale: scale, child: child);
                  },
                  child: AnimatedContainer(
                    duration: const Duration(milliseconds: 300),
                    width: 96,
                    height: 96,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: widget.isRecording ? WuweiColors.accent : WuweiColors.bg2,
                      border: Border.all(
                        color: widget.isRecording || widget.isProcessing
                            ? WuweiColors.accent
                            : WuweiColors.bg3,
                        width: 1.2,
                      ),
                      boxShadow: widget.isRecording
                          ? [
                              const BoxShadow(
                                color: WuweiColors.accentGlow,
                                blurRadius: 24,
                                spreadRadius: 2,
                              ),
                            ]
                          : [
                              const BoxShadow(
                                color: Colors.black54,
                                blurRadius: 16,
                              ),
                            ],
                    ),
                    child: Center(child: _buildGlyph()),
                  ),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 18),
        Text(
          widget.isRecording
              ? (_dragY < -60 ? '上滑取消' : '松开发送')
              : widget.isProcessing
                  ? '思考中'
                  : '按住说话',
          style: TextStyle(
            fontSize: 11,
            letterSpacing: 3.0,
            color: _dragY < -60 ? WuweiColors.danger : WuweiColors.fgDimmer,
          ),
        ),
      ],
    );
  }

  Widget _buildGlyph() {
    if (widget.isRecording) {
      return AnimatedBuilder(
        animation: _waveCtrl,
        builder: (_, __) => CustomPaint(
          size: const Size(40, 32),
          painter: _WavePainter(progress: _waveCtrl.value, color: WuweiColors.bg),
        ),
      );
    }
    if (widget.isProcessing) {
      return const Icon(Icons.access_time, size: 24, color: WuweiColors.fgDim);
    }
    return const Icon(Icons.mic_none_outlined, size: 28, color: WuweiColors.fgDim);
  }
}

class _PulseRing extends StatelessWidget {
  final AnimationController controller;
  final double maxScale;
  final double fromOpacity;
  final double delay;

  const _PulseRing({
    required this.controller,
    required this.maxScale,
    required this.fromOpacity,
    this.delay = 0,
  });

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: controller,
      builder: (_, __) {
        final t = ((controller.value + (1 - delay)) % 1.0);
        final scale = 1.0 + (maxScale - 1.0) * t;
        final opacity = (fromOpacity * (1 - t)).clamp(0.0, 1.0);
        return Opacity(
          opacity: opacity,
          child: Transform.scale(
            scale: scale,
            child: Container(
              width: 96,
              height: 96,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                border: Border.all(color: WuweiColors.accent, width: 1.2),
              ),
            ),
          ),
        );
      },
    );
  }
}

class _ArcPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = WuweiColors.accent
      ..strokeWidth = 1.5
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round;
    final rect = Offset.zero & size;
    canvas.drawArc(rect, -math.pi / 2, math.pi, false, paint);
  }

  @override
  bool shouldRepaint(covariant _ArcPainter oldDelegate) => false;
}

class _WavePainter extends CustomPainter {
  final double progress; // 0..1
  final Color color;

  _WavePainter({required this.progress, required this.color});

  @override
  void paint(Canvas canvas, Size size) {
    const barCount = 7;
    const barWidth = 3.0;
    final gap = (size.width - barCount * barWidth) / (barCount - 1);
    final paint = Paint()
      ..color = color
      ..strokeWidth = barWidth
      ..strokeCap = StrokeCap.round;

    for (var i = 0; i < barCount; i++) {
      final phase = (progress + i * 0.13) * 2 * math.pi;
      final norm = (math.sin(phase) + 1) / 2; // 0..1
      final h = 5 + norm * (size.height - 8);
      final x = i * (barWidth + gap) + barWidth / 2;
      final y0 = (size.height - h) / 2;
      canvas.drawLine(Offset(x, y0), Offset(x, y0 + h), paint);
    }
  }

  @override
  bool shouldRepaint(covariant _WavePainter oldDelegate) =>
      oldDelegate.progress != progress;
}
