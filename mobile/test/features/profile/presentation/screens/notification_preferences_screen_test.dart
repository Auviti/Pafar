import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:pafar_mobile/features/profile/presentation/screens/notification_preferences_screen.dart';

void main() {
  Widget createWidgetUnderTest() {
    return const MaterialApp(
      home: NotificationPreferencesScreen(),
    );
  }

  group('NotificationPreferencesScreen Widget Tests', () {
    testWidgets('should display app bar with correct title', (tester) async {
      // Act
      await tester.pumpWidget(createWidgetUnderTest());
      await tester.pumpAndSettle();

      // Assert
      expect(find.text('Notifications'), findsOneWidget);
      expect(find.byType(AppBar), findsOneWidget);
    });

    testWidgets('should display notification preferences screen', (tester) async {
      // Act
      await tester.pumpWidget(createWidgetUnderTest());
      await tester.pumpAndSettle();

      // Assert
      expect(find.byType(Scaffold), findsOneWidget);
    });
  });
}