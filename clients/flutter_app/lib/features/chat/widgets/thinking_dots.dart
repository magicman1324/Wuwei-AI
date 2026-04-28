import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../../../app/theme.dart';

class ThinkingDots extends StatefulWidget {
  const ThinkingDots({super.key});

  @override
  State<ThinkingDots> createState() => _ThinkingDotsState();
}

class _ThinkingDotsState extends State<ThinkingDots>
    with SingleTickerProviderStateMixin {
  late final AnimationController _ctrl;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1400),
    )..repeat();
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _ctrl,
      builder: (_, __) => Row(
        mainAxisSize: MainAxisSize.min,
        children: List.generate(3, (i) {
          final phase = (_ctrl.value + i * 0.2) % 1.0;
          // pulse between 0.2 and 1.0 opacity, scale 0.8..1.2
          final t = math.sin(phase * math.pi); // 0..1..0 over a beat
          final opacity = 0.2 + 0.8 * t;
          final scale = 0.8 + 0.4 * t;
          return Padding(
            padding: const EdgeInsets.symmetric(horizontal: 4),
            child: Opacity(
              opacity: opacity,
              child: Transform.scale(
                scale: scale,
                child: Container(
                  width: 8,
                  height: 8,
                  decoration: const BoxDecoration(
                    color: WuweiColors.fgDim,
                    shape: BoxShape.circle,
                  ),
                ),
              ),
            ),
          );
        }),
      ),
    );
  }
}
