import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:pafar_mobile/features/profile/presentation/screens/profile_screen.dart';
import 'package:pafar_mobile/features/auth/domain/entities/user.dart';

void main() {
  late User testUser;

  setUp(() {
    testUser = User(
      id: 'test-id',
      email: 'test@example.com',
      firstName: 'John',
      lastName: 'Doe',
      phone: '+1234567890',
      role: 'passenger',
      isVerified: true,
      isActive: true,
      createdAt: DateTime.parse('2023-01-01T00:00:00Z'),
      updatedAt: DateTime.parse('2023-01-01T00:00:00Z'),
    );
  });

  Widget createWidgetUnderTest() {
    return MaterialApp(
      home: ProfileScreen(user: testUser),
    );
  }

  group('ProfileScreen Widget Tests', () {
    testWidgets('should display profile screen with app bar', (tester) async {
      // Act
      await tester.pumpWidget(createWidgetUnderTest());
      await tester.pumpAndSettle();

      // Assert
      expect(find.text('Profile'), findsOneWidget);
      expect(find.byType(AppBar), findsOneWidget);
    });

    testWidgets('should display edit button in app bar', (tester) async {
      // Act
      await tester.pumpWidget(createWidgetUnderTest());
      await tester.pumpAndSettle();

      // Assert
      expect(find.text('Edit'), findsOneWidget);
    });

    testWidgets('should display profile form fields', (tester) async {
      // Act
      await tester.pumpWidget(createWidgetUnderTest());
      await tester.pumpAndSettle();

      // Assert
      expect(find.byType(TextFormField), findsWidgets);
    });

    testWidgets('should display menu options', (tester) async {
      // Act
      await tester.pumpWidget(createWidgetUnderTest());
      await tester.pumpAndSettle();

      // Assert
      expect(find.text('My Bookings'), findsOneWidget);
      expect(find.text('Notifications'), findsOneWidget);
      expect(find.text('Payment Methods'), findsOneWidget);
      expect(find.text('App Settings'), findsOneWidget);
      expect(find.text('Help & Support'), findsOneWidget);
      expect(find.text('Sign Out'), findsOneWidget);
    });
  });
}