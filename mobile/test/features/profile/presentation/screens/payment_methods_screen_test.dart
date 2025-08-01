import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:pafar_mobile/features/profile/presentation/screens/payment_methods_screen.dart';

void main() {
  Widget createWidgetUnderTest() {
    return const MaterialApp(
      home: PaymentMethodsScreen(),
    );
  }

  group('PaymentMethodsScreen Widget Tests', () {
    testWidgets('should display app bar with correct title', (tester) async {
      // Act
      await tester.pumpWidget(createWidgetUnderTest());
      await tester.pumpAndSettle();

      // Assert
      expect(find.text('Payment Methods'), findsOneWidget);
      expect(find.byType(AppBar), findsOneWidget);
    });

    testWidgets('should display add button in app bar', (tester) async {
      // Act
      await tester.pumpWidget(createWidgetUnderTest());
      await tester.pumpAndSettle();

      // Assert
      expect(find.byIcon(Icons.add), findsOneWidget);
    });

    testWidgets('should display payment methods screen', (tester) async {
      // Act
      await tester.pumpWidget(createWidgetUnderTest());
      await tester.pumpAndSettle();

      // Assert
      expect(find.byType(Scaffold), findsOneWidget);
    });
  });
}