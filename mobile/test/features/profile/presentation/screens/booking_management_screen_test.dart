import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:pafar_mobile/features/profile/presentation/screens/booking_management_screen.dart';

void main() {
  Widget createWidgetUnderTest() {
    return const MaterialApp(
      home: BookingManagementScreen(),
    );
  }

  group('BookingManagementScreen Widget Tests', () {
    testWidgets('should display app bar with correct title', (tester) async {
      // Act
      await tester.pumpWidget(createWidgetUnderTest());
      await tester.pumpAndSettle();

      // Assert
      expect(find.text('My Bookings'), findsOneWidget);
      expect(find.byType(AppBar), findsOneWidget);
    });

    testWidgets('should display tab bar with correct tabs', (tester) async {
      // Act
      await tester.pumpWidget(createWidgetUnderTest());
      await tester.pumpAndSettle();

      // Assert
      expect(find.text('Upcoming'), findsOneWidget);
      expect(find.text('Completed'), findsOneWidget);
      expect(find.text('Cancelled'), findsOneWidget);
      expect(find.byType(TabBar), findsOneWidget);
    });

    testWidgets('should display tab bar view', (tester) async {
      // Act
      await tester.pumpWidget(createWidgetUnderTest());
      await tester.pumpAndSettle();

      // Assert
      expect(find.byType(TabBarView), findsOneWidget);
    });
  });
}