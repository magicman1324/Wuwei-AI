import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../features/chat/chat_page.dart';
import '../features/history/history_page.dart';
import '../features/onboarding/onboarding_page.dart';
import '../features/settings/settings_page.dart';

final _rootNavKey = GlobalKey<NavigatorState>();
final _shellNavKey = GlobalKey<NavigatorState>();

final routerProvider = Provider<GoRouter>((ref) {
  return GoRouter(
    navigatorKey: _rootNavKey,
    initialLocation: '/chat',
    routes: [
      GoRoute(
        path: '/onboarding',
        builder: (_, __) => const OnboardingPage(),
      ),
      ShellRoute(
        navigatorKey: _shellNavKey,
        builder: (_, __, child) => ScaffoldWithNav(child: child),
        routes: [
          GoRoute(
            path: '/chat',
            builder: (_, __) => const ChatPage(),
          ),
          GoRoute(
            path: '/history',
            builder: (_, __) => const HistoryPage(),
          ),
          GoRoute(
            path: '/settings',
            builder: (_, __) => const SettingsPage(),
          ),
        ],
      ),
    ],
  );
});

class ScaffoldWithNav extends StatelessWidget {
  final Widget child;
  const ScaffoldWithNav({super.key, required this.child});

  static const _tabs = ['/chat', '/history', '/settings'];

  @override
  Widget build(BuildContext context) {
    final location = GoRouterState.of(context).uri.path;
    final idx = _tabs.indexOf(location).clamp(0, 2);

    return Scaffold(
      body: child,
      bottomNavigationBar: NavigationBar(
        selectedIndex: idx,
        onDestinationSelected: (i) => context.go(_tabs[i]),
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.mic, size: 28),
            selectedIcon: Icon(Icons.mic, size: 28),
            label: '对话',
          ),
          NavigationDestination(
            icon: Icon(Icons.history, size: 28),
            selectedIcon: Icon(Icons.history, size: 28),
            label: '历史',
          ),
          NavigationDestination(
            icon: Icon(Icons.settings, size: 28),
            selectedIcon: Icon(Icons.settings, size: 28),
            label: '设置',
          ),
        ],
      ),
    );
  }
}
