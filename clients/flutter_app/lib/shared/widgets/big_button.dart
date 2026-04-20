import 'package:flutter/material.dart';

class BigButton extends StatelessWidget {
  final String label;
  final VoidCallback? onPressed;
  final IconData? icon;
  final bool loading;

  const BigButton({
    super.key,
    required this.label,
    this.onPressed,
    this.icon,
    this.loading = false,
  });

  @override
  Widget build(BuildContext context) {
    return ElevatedButton(
      onPressed: loading ? null : onPressed,
      child: loading
          ? const SizedBox(
              width: 28, height: 28,
              child: CircularProgressIndicator(strokeWidth: 3))
          : Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                if (icon != null) ...[
                  Icon(icon, size: 28),
                  const SizedBox(width: 12),
                ],
                Text(label),
              ],
            ),
    );
  }
}
