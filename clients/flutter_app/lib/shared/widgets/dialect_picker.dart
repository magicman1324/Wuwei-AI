import 'package:flutter/material.dart';

import '../../core/constants.dart';

class DialectPicker extends StatelessWidget {
  final DialectCode selected;
  final ValueChanged<DialectCode> onChanged;

  const DialectPicker({
    super.key,
    required this.selected,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return DropdownButton<DialectCode>(
      value: selected,
      underline: const SizedBox(),
      style: Theme.of(context).textTheme.bodyLarge,
      items: DialectCode.values
          .map((d) => DropdownMenuItem(value: d, child: Text(d.label)))
          .toList(),
      onChanged: (v) {
        if (v != null) onChanged(v);
      },
    );
  }
}
