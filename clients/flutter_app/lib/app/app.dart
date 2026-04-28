import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'routes.dart';
import 'theme.dart';

class WuweiApp extends ConsumerWidget {
  const WuweiApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(routerProvider);

    return MaterialApp.router(
      title: '无维AI',
      theme: elderlyTheme,
      routerConfig: router,
      debugShowCheckedModeBanner: false,
    );
  }
}
