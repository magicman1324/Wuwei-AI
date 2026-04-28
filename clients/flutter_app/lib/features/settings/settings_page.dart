import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/constants.dart';

class SettingsPage extends ConsumerStatefulWidget {
  const SettingsPage({super.key});

  @override
  ConsumerState<SettingsPage> createState() => _SettingsPageState();
}

class _SettingsPageState extends ConsumerState<SettingsPage> {
  DialectCode _dialect = DialectCode.mandarin;
  double _speed = 0.85;
  double _volume = 1.2;
  String _fontSize = 'large';

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('设置')),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          // 方言选择
          const Text('🗣 方言选择',
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
          const SizedBox(height: 12),
          ...DialectCode.values.map((d) => RadioListTile<DialectCode>(
                title: Text(d.label, style: const TextStyle(fontSize: 22)),
                value: d,
                groupValue: _dialect,
                onChanged: (v) => setState(() => _dialect = v!),
                contentPadding: const EdgeInsets.symmetric(horizontal: 8),
              )),

          const SizedBox(height: 24),

          // 语音速度
          const Text('🔊 语音速度',
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          Row(
            children: [
              const Text('慢', style: TextStyle(fontSize: 20)),
              Expanded(
                child: Slider(
                  value: _speed,
                  min: 0.5,
                  max: 1.5,
                  divisions: 10,
                  label: _speed.toStringAsFixed(1),
                  onChanged: (v) => setState(() => _speed = v),
                ),
              ),
              const Text('快', style: TextStyle(fontSize: 20)),
            ],
          ),

          const SizedBox(height: 24),

          // 语音音量
          const Text('🔊 语音音量',
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          Row(
            children: [
              const Text('小', style: TextStyle(fontSize: 20)),
              Expanded(
                child: Slider(
                  value: _volume,
                  min: 0.5,
                  max: 2.0,
                  divisions: 15,
                  label: _volume.toStringAsFixed(1),
                  onChanged: (v) => setState(() => _volume = v),
                ),
              ),
              const Text('大', style: TextStyle(fontSize: 20)),
            ],
          ),

          const SizedBox(height: 24),

          // 字体大小
          const Text('🔤 字体大小',
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
          const SizedBox(height: 12),
          SegmentedButton<String>(
            segments: const [
              ButtonSegment(value: 'large', label: Text('大')),
              ButtonSegment(value: 'xlarge', label: Text('很大')),
              ButtonSegment(value: 'xxlarge', label: Text('超大')),
            ],
            selected: {_fontSize},
            onSelectionChanged: (s) => setState(() => _fontSize = s.first),
            style: ButtonStyle(
              textStyle: WidgetStatePropertyAll(
                const TextStyle(fontSize: 20),
              ),
            ),
          ),

          const SizedBox(height: 32),

          // 保存
          ElevatedButton(
            onPressed: () {
              // TODO: call API updatePreferences + save to local storage
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text('设置已保存', style: TextStyle(fontSize: 18)),
                ),
              );
            },
            child: const Text('保存设置'),
          ),
        ],
      ),
    );
  }
}
