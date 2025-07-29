import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/mockito.dart';
import 'package:mockito/annotations.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:get_it/get_it.dart';

import 'package:pafar_mobile/app/app.dart';
import 'package:pafar_mobile/core/constants/app_constants.dart';

import 'app_test.mocks.dart';

@GenerateMocks([SharedPreferences])
void main() {
  group('AppRouter', () {
    late MockSharedPreferences mockPrefs;

    setUp(() {
      mockPrefs = MockSharedPreferences();
      GetIt.instance.registerSingleton<SharedPreferences>(mockPrefs);
    });

    tearDown(() {
      GetIt.instance.reset();
    });

    testWidgets('should show SplashScreen on initial route', (tester) async {
      // Arrange
      when(mockPrefs.getString(AppConstants.accessTokenKey))
          .thenReturn(null);

      // Act
      await tester.pumpWidget(
        MaterialApp.router(
          routerConfig: AppRouter.router,
        ),
      );

      // Assert
      expect(find.byType(SplashScreen), findsOneWidget);
      expect(find.text('Pafar'), findsOneWidget);
      expect(find.text('Your Journey Starts Here'), findsOneWidget);
    });

    testWidgets('should redirect to login when not authenticated', (tester) async {
      // Arrange
      when(mockPrefs.getString(AppConstants.accessTokenKey))
          .thenReturn(null);

      // Act
      await tester.pumpWidget(
        MaterialApp.router(
          routerConfig: AppRouter.router,
        ),
      );
      
      // Navigate to home
      AppRouter.router.go('/home');
      await tester.pumpAndSettle();

      // Assert
      expect(find.byType(LoginScreen), findsOneWidget);
    });

    testWidgets('should redirect to home when authenticated and accessing login', (tester) async {
      // Arrange
      when(mockPrefs.getString(AppConstants.accessTokenKey))
          .thenReturn('valid_token');

      // Act
      await tester.pumpWidget(
        MaterialApp.router(
          routerConfig: AppRouter.router,
        ),
      );
      
      // Navigate to login
      AppRouter.router.go('/login');
      await tester.pumpAndSettle();

      // Assert
      expect(find.byType(HomeScreen), findsOneWidget);
    });
  });

  group('SplashScreen', () {
    testWidgets('should display app branding', (tester) async {
      // Act
      await tester.pumpWidget(
        const MaterialApp(
          home: SplashScreen(),
        ),
      );

      // Assert
      expect(find.text('Pafar'), findsOneWidget);
      expect(find.text('Your Journey Starts Here'), findsOneWidget);
      expect(find.byIcon(Icons.directions_bus), findsOneWidget);
      expect(find.byType(CircularProgressIndicator), findsOneWidget);
    });
  });

  group('HomeScreen', () {
    testWidgets('should display bottom navigation', (tester) async {
      // Act
      await tester.pumpWidget(
        const MaterialApp(
          home: HomeScreen(),
        ),
      );

      // Assert
      expect(find.byType(BottomNavigationBar), findsOneWidget);
      expect(find.text('Home'), findsOneWidget);
      expect(find.text('Book'), findsOneWidget);
      expect(find.text('Track'), findsOneWidget);
      expect(find.text('Profile'), findsOneWidget);
    });
  });

  group('ErrorScreen', () {
    testWidgets('should display error message', (tester) async {
      // Arrange
      const error = Exception('Test error');

      // Act
      await tester.pumpWidget(
        const MaterialApp(
          home: ErrorScreen(error: error),
        ),
      );

      // Assert
      expect(find.text('Something went wrong'), findsOneWidget);
      expect(find.text('Exception: Test error'), findsOneWidget);
      expect(find.byIcon(Icons.error_outline), findsOneWidget);
      expect(find.text('Go Home'), findsOneWidget);
    });

    testWidgets('should display unknown error when no error provided', (tester) async {
      // Act
      await tester.pumpWidget(
        const MaterialApp(
          home: ErrorScreen(),
        ),
      );

      // Assert
      expect(find.text('Something went wrong'), findsOneWidget);
      expect(find.text('Unknown error occurred'), findsOneWidget);
    });
  });
}