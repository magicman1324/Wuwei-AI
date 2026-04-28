import 'package:flutter/material.dart';

/// Wuwei dark palette — OKLCH approximations from index.html.
class WuweiColors {
  static const bg = Color(0xFF0E1116);
  static const bg2 = Color(0xFF161A20);
  static const bg3 = Color(0xFF1E232A);
  static const fg = Color(0xFFECE7DD);
  static const fgDim = Color(0xFF8C857B);
  static const fgDimmer = Color(0xFF4A4540);
  static const accent = Color(0xFF4FB58F);
  static const accentGlow = Color(0x404FB58F);
  static const danger = Color(0xFFD9665B);
}

const _serifFallback = ['Songti SC', 'STSong', 'Noto Serif SC', 'serif'];

const _serifStyle = TextStyle(
  fontFamily: 'serif',
  fontFamilyFallback: _serifFallback,
);

final wuweiTheme = ThemeData(
  useMaterial3: true,
  brightness: Brightness.dark,
  scaffoldBackgroundColor: WuweiColors.bg,
  colorScheme: const ColorScheme.dark(
    primary: WuweiColors.accent,
    onPrimary: WuweiColors.bg,
    secondary: WuweiColors.accent,
    surface: WuweiColors.bg,
    surfaceContainerHighest: WuweiColors.bg2,
    onSurface: WuweiColors.fg,
    error: WuweiColors.danger,
    outline: WuweiColors.bg3,
  ),
  textTheme: TextTheme(
    // 大字回复
    displayLarge: _serifStyle.copyWith(
      fontSize: 44,
      fontWeight: FontWeight.w300,
      letterSpacing: -0.4,
      height: 1.4,
      color: WuweiColors.fg,
    ),
    // 引用 / 副标题（衬线斜体）
    displayMedium: _serifStyle.copyWith(
      fontSize: 22,
      fontWeight: FontWeight.w300,
      fontStyle: FontStyle.italic,
      color: WuweiColors.fgDimmer,
    ),
    headlineLarge: const TextStyle(fontSize: 24, fontWeight: FontWeight.w400, color: WuweiColors.fg),
    headlineMedium: const TextStyle(fontSize: 18, fontWeight: FontWeight.w400, color: WuweiColors.fg),
    titleLarge: const TextStyle(fontSize: 18, fontWeight: FontWeight.w500, color: WuweiColors.fg),
    titleMedium: const TextStyle(fontSize: 15, color: WuweiColors.fgDim, letterSpacing: 0.4),
    bodyLarge: const TextStyle(fontSize: 16, height: 1.7, color: WuweiColors.fg),
    bodyMedium: const TextStyle(fontSize: 14, height: 1.7, color: WuweiColors.fg),
    bodySmall: const TextStyle(fontSize: 12, color: WuweiColors.fgDim, letterSpacing: 1.2),
    labelLarge: const TextStyle(fontSize: 13, color: WuweiColors.fgDim, letterSpacing: 1.5),
    labelMedium: const TextStyle(fontSize: 11, color: WuweiColors.fgDimmer, letterSpacing: 2.0),
  ),
  appBarTheme: const AppBarTheme(
    backgroundColor: WuweiColors.bg,
    foregroundColor: WuweiColors.fg,
    elevation: 0,
    scrolledUnderElevation: 0,
    centerTitle: true,
    titleTextStyle: TextStyle(
      fontSize: 13,
      color: WuweiColors.fgDim,
      letterSpacing: 4.0,
      fontWeight: FontWeight.w400,
    ),
  ),
  navigationBarTheme: NavigationBarThemeData(
    backgroundColor: WuweiColors.bg,
    indicatorColor: Colors.transparent,
    surfaceTintColor: Colors.transparent,
    height: 64,
    labelTextStyle: const WidgetStatePropertyAll(
      TextStyle(fontSize: 11, color: WuweiColors.fgDim, letterSpacing: 1.5),
    ),
    iconTheme: WidgetStateProperty.resolveWith((states) {
      final selected = states.contains(WidgetState.selected);
      return IconThemeData(
        color: selected ? WuweiColors.accent : WuweiColors.fgDim,
        size: 22,
      );
    }),
  ),
  inputDecorationTheme: InputDecorationTheme(
    filled: true,
    fillColor: WuweiColors.bg2,
    contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
    hintStyle: const TextStyle(
      color: WuweiColors.fgDimmer,
      fontFamily: 'serif',
      fontFamilyFallback: _serifFallback,
      fontStyle: FontStyle.italic,
      fontSize: 14,
    ),
    border: OutlineInputBorder(
      borderRadius: BorderRadius.circular(12),
      borderSide: const BorderSide(color: WuweiColors.bg3),
    ),
    enabledBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(12),
      borderSide: const BorderSide(color: WuweiColors.bg3),
    ),
    focusedBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(12),
      borderSide: const BorderSide(color: WuweiColors.accent),
    ),
  ),
  elevatedButtonTheme: ElevatedButtonThemeData(
    style: ElevatedButton.styleFrom(
      backgroundColor: WuweiColors.bg2,
      foregroundColor: WuweiColors.accent,
      side: const BorderSide(color: WuweiColors.bg3),
      minimumSize: const Size(double.infinity, 52),
      textStyle: const TextStyle(fontSize: 14, letterSpacing: 2.0),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
    ),
  ),
  outlinedButtonTheme: OutlinedButtonThemeData(
    style: OutlinedButton.styleFrom(
      foregroundColor: WuweiColors.accent,
      side: const BorderSide(color: WuweiColors.bg3),
      minimumSize: const Size(double.infinity, 52),
      textStyle: const TextStyle(fontSize: 14, letterSpacing: 2.0),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
    ),
  ),
  textButtonTheme: TextButtonThemeData(
    style: TextButton.styleFrom(
      foregroundColor: WuweiColors.fgDim,
    ),
  ),
  sliderTheme: const SliderThemeData(
    activeTrackColor: WuweiColors.accent,
    inactiveTrackColor: WuweiColors.bg3,
    thumbColor: WuweiColors.accent,
  ),
  dividerColor: WuweiColors.bg3,
);

/// Backwards-compat alias used by [WuweiApp].
final elderlyTheme = wuweiTheme;
