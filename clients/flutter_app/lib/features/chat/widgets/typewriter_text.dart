import 'dart:async';

import 'package:flutter/material.dart';

import '../../../app/theme.dart';

class TypewriterText extends StatefulWidget {
  final String text;
  final TextStyle style;
  final Duration tick;
  final VoidCallback? onDone;

  const TypewriterText({
    super.key,
    required this.text,
    required this.style,
    this.tick = const Duration(milliseconds: 28),
    this.onDone,
  });

  @override
  State<TypewriterText> createState() => _TypewriterTextState();
}

class _TypewriterTextState extends State<TypewriterText>
    with SingleTickerProviderStateMixin {
  Timer? _timer;
  late final AnimationController _caretCtrl;
  int _i = 0;

  @override
  void initState() {
    super.initState();
    _caretCtrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 800),
    )..repeat(reverse: true);
    _start();
  }

  @override
  void didUpdateWidget(covariant TypewriterText old) {
    super.didUpdateWidget(old);
    if (widget.text != old.text) {
      _i = 0;
      _start();
    }
  }

  void _start() {
    _timer?.cancel();
    if (widget.text.isEmpty) {
      widget.onDone?.call();
      return;
    }
    _timer = Timer.periodic(widget.tick, (t) {
      if (_i >= widget.text.length) {
        t.cancel();
        widget.onDone?.call();
        if (mounted) setState(() {});
        return;
      }
      _i++;
      if (mounted) setState(() {});
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    _caretCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final shown = widget.text.substring(0, _i.clamp(0, widget.text.length));
    final isTyping = _i < widget.text.length;
    return RichText(
      textAlign: TextAlign.center,
      text: TextSpan(
        style: widget.style,
        children: [
          TextSpan(text: shown),
          if (isTyping)
            WidgetSpan(
              alignment: PlaceholderAlignment.middle,
              child: FadeTransition(
                opacity: _caretCtrl,
                child: Container(
                  margin: const EdgeInsets.only(left: 4),
                  width: 2,
                  height: (widget.style.fontSize ?? 24) * 0.85,
                  color: WuweiColors.accent,
                ),
              ),
            ),
        ],
      ),
    );
  }
}
