import 'package:flutter/material.dart';

const _primaryGreen = Color(0xFF2E7D32);
const _baseFontSize = 20.0;

final elderlyTheme = ThemeData(
  useMaterial3: true,
  colorScheme: ColorScheme.fromSeed(
    seedColor: _primaryGreen,
    primary: _primaryGreen,
    brightness: Brightness.light,
  ),
  textTheme: const TextTheme(
    displayLarge: TextStyle(fontSize: 48, fontWeight: FontWeight.bold),
    displayMedium: TextStyle(fontSize: 36, fontWeight: FontWeight.bold),
    headlineLarge: TextStyle(fontSize: 32, fontWeight: FontWeight.bold),
    headlineMedium: TextStyle(fontSize: 28, fontWeight: FontWeight.w600),
    titleLarge: TextStyle(fontSize: 24, fontWeight: FontWeight.w600),
    bodyLarge: TextStyle(fontSize: _baseFontSize, height: 1.8),
    bodyMedium: TextStyle(fontSize: 18, height: 1.8),
    labelLarge: TextStyle(fontSize: 22, fontWeight: FontWeight.w600),
  ),
  elevatedButtonTheme: ElevatedButtonThemeData(
    style: ElevatedButton.styleFrom(
      minimumSize: const Size(double.infinity, 64),
      textStyle: const TextStyle(fontSize: 22, fontWeight: FontWeight.w600),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
    ),
  ),
  outlinedButtonTheme: OutlinedButtonThemeData(
    style: OutlinedButton.styleFrom(
      minimumSize: const Size(double.infinity, 64),
      textStyle: const TextStyle(fontSize: 22, fontWeight: FontWeight.w600),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
    ),
  ),
  inputDecorationTheme: InputDecorationTheme(
    contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 18),
    border: OutlineInputBorder(borderRadius: BorderRadius.circular(16)),
    labelStyle: const TextStyle(fontSize: 20),
    hintStyle: const TextStyle(fontSize: 18),
  ),
  navigationBarTheme: const NavigationBarThemeData(
    height: 72,
    labelTextStyle: WidgetStatePropertyAll(
      TextStyle(fontSize: 14, fontWeight: FontWeight.w600),
    ),
  ),
  appBarTheme: const AppBarTheme(
    titleTextStyle: TextStyle(
      fontSize: 24,
      fontWeight: FontWeight.bold,
      color: _primaryGreen,
    ),
    centerTitle: true,
  ),
);
