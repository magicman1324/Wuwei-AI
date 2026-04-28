import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../core/constants.dart';

class OnboardingPage extends StatefulWidget {
  const OnboardingPage({super.key});

  @override
  State<OnboardingPage> createState() => _OnboardingPageState();
}

class _OnboardingPageState extends State<OnboardingPage> {
  final _controller = PageController();
  int _page = 0;
  DialectCode _selectedDialect = DialectCode.mandarin;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _next() {
    if (_page < 2) {
      _controller.nextPage(
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeInOut,
      );
    } else {
      // TODO: save dialect to local storage + create user via API
      context.go('/chat');
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            Expanded(
              child: PageView(
                controller: _controller,
                onPageChanged: (p) => setState(() => _page = p),
                physics: const NeverScrollableScrollPhysics(),
                children: [
                  // Step 1: Welcome
                  _buildStep(
                    icon: Icons.waving_hand,
                    title: '欢迎使用无维AI',
                    subtitle: '专为长辈设计的语音聊天助手',
                  ),
                  // Step 2: Choose dialect
                  Padding(
                    padding: const EdgeInsets.all(32),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Text('选择您的方言',
                            style: theme.textTheme.headlineLarge),
                        const SizedBox(height: 32),
                        ...DialectCode.values.map((d) =>
                            Padding(
                              padding: const EdgeInsets.only(bottom: 12),
                              child: SizedBox(
                                width: double.infinity,
                                height: 64,
                                child: _selectedDialect == d
                                    ? ElevatedButton(
                                        onPressed: () =>
                                            setState(() => _selectedDialect = d),
                                        child: Text(d.label),
                                      )
                                    : OutlinedButton(
                                        onPressed: () =>
                                            setState(() => _selectedDialect = d),
                                        child: Text(d.label),
                                      ),
                              ),
                            )),
                      ],
                    ),
                  ),
                  // Step 3: Ready
                  _buildStep(
                    icon: Icons.check_circle_outline,
                    title: '准备就绪！',
                    subtitle: '按住麦克风开始和我聊天吧',
                  ),
                ],
              ),
            ),
            // Dots + Next
            Padding(
              padding: const EdgeInsets.all(24),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  // Dots
                  Row(
                    children: List.generate(3, (i) => Container(
                      width: 12, height: 12,
                      margin: const EdgeInsets.only(right: 8),
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: i == _page
                            ? theme.colorScheme.primary
                            : Colors.grey[300],
                      ),
                    )),
                  ),
                  // Next button
                  SizedBox(
                    width: 120,
                    height: 56,
                    child: ElevatedButton(
                      onPressed: _next,
                      child: Text(_page == 2 ? '开始' : '下一步'),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStep({
    required IconData icon,
    required String title,
    required String subtitle,
  }) {
    return Padding(
      padding: const EdgeInsets.all(32),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(icon, size: 96, color: Theme.of(context).colorScheme.primary),
          const SizedBox(height: 32),
          Text(title, style: Theme.of(context).textTheme.headlineLarge,
              textAlign: TextAlign.center),
          const SizedBox(height: 16),
          Text(subtitle, style: Theme.of(context).textTheme.titleLarge,
              textAlign: TextAlign.center),
        ],
      ),
    );
  }
}
