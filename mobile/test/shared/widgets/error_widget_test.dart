import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

import '../../../lib/shared/widgets/error_widget.dart';

void main() {
  group('ErrorDisplayWidget', () {
    testWidgets('should display error message and icon', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ErrorDisplayWidget(
              message: 'Test error message',
            ),
          ),
        ),
      );

      expect(find.text('Oops! Something went wrong'), findsOneWidget);
      expect(find.text('Test error message'), findsOneWidget);
      expect(find.byIcon(Icons.error_outline), findsOneWidget);
    });

    testWidgets('should display custom icon when provided', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ErrorDisplayWidget(
              message: 'Test error message',
              icon: Icons.warning,
            ),
          ),
        ),
      );

      expect(find.byIcon(Icons.warning), findsOneWidget);
      expect(find.byIcon(Icons.error_outline), findsNothing);
    });

    testWidgets('should display retry button when onRetry is provided', (tester) async {
      bool retryPressed = false;
      
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ErrorDisplayWidget(
              message: 'Test error message',
              onRetry: () => retryPressed = true,
            ),
          ),
        ),
      );

      expect(find.text('Try Again'), findsOneWidget);
      
      await tester.tap(find.text('Try Again'));
      await tester.pump();
      
      expect(retryPressed, isTrue);
    });

    testWidgets('should not display retry button when onRetry is null', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ErrorDisplayWidget(
              message: 'Test error message',
            ),
          ),
        ),
      );

      expect(find.text('Try Again'), findsNothing);
    });

    testWidgets('should display error ID when provided', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ErrorDisplayWidget(
              message: 'Test error message',
              errorId: 'ERROR-123',
            ),
          ),
        ),
      );

      expect(find.text('Error ID: ERROR-123'), findsOneWidget);
      expect(find.text('Copy ID'), findsOneWidget);
    });

    testWidgets('should copy error ID to clipboard when copy button is pressed', (tester) async {
      // Mock clipboard
      const channel = MethodChannel('flutter/platform');
      final List<MethodCall> log = <MethodCall>[];
      
      tester.binding.defaultBinaryMessenger.setMockMethodCallHandler(channel, (methodCall) async {
        log.add(methodCall);
        return null;
      });

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ErrorDisplayWidget(
              message: 'Test error message',
              errorId: 'ERROR-123',
            ),
          ),
        ),
      );

      await tester.tap(find.text('Copy ID'));
      await tester.pump();

      expect(log, hasLength(1));
      expect(log.first.method, 'Clipboard.setData');
      expect(log.first.arguments['text'], 'ERROR-123');
    });

    testWidgets('should show error details when showDetails is true', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ErrorDisplayWidget(
              message: 'Test error message',
              showDetails: true,
              stackTrace: 'Stack trace here',
            ),
          ),
        ),
      );

      expect(find.text('Error Details'), findsOneWidget);
      
      // Tap to expand details
      await tester.tap(find.text('Error Details'));
      await tester.pumpAndSettle();
      
      expect(find.text('Stack trace here'), findsOneWidget);
    });

    testWidgets('should navigate to home when Go Home is pressed', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ErrorDisplayWidget(
              message: 'Test error message',
            ),
          ),
          routes: {
            '/': (context) => const Scaffold(body: Text('Home')),
          },
        ),
      );

      await tester.tap(find.text('Go Home'));
      await tester.pumpAndSettle();

      expect(find.text('Home'), findsOneWidget);
    });

    testWidgets('should show report dialog when Report Issue is pressed', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ErrorDisplayWidget(
              message: 'Test error message',
            ),
          ),
        ),
      );

      await tester.tap(find.text('Report Issue'));
      await tester.pumpAndSettle();

      expect(find.text('Report Issue'), findsNWidgets(2)); // Button + dialog title
      expect(find.text('Thank you for helping us improve!'), findsOneWidget);
      expect(find.text('Close'), findsOneWidget);
      expect(find.text('Contact Support'), findsOneWidget);
    });
  });

  group('NetworkErrorWidget', () {
    testWidgets('should display network-specific error message', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: NetworkErrorWidget(),
          ),
        ),
      );

      expect(find.text('Please check your internet connection and try again.'), findsOneWidget);
      expect(find.byIcon(Icons.wifi_off), findsOneWidget);
    });

    testWidgets('should call onRetry when provided', (tester) async {
      bool retryPressed = false;
      
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: NetworkErrorWidget(
              onRetry: () => retryPressed = true,
            ),
          ),
        ),
      );

      await tester.tap(find.text('Try Again'));
      await tester.pump();
      
      expect(retryPressed, isTrue);
    });
  });

  group('ValidationErrorWidget', () {
    testWidgets('should display field errors', (tester) async {
      final fieldErrors = {
        'email': 'Invalid email format',
        'password': 'Password too short',
      };

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ValidationErrorWidget(
              fieldErrors: fieldErrors,
            ),
          ),
        ),
      );

      expect(find.text('Please correct the following errors:'), findsOneWidget);
      expect(find.text('• email: Invalid email format'), findsOneWidget);
      expect(find.text('• password: Password too short'), findsOneWidget);
      expect(find.byIcon(Icons.warning), findsOneWidget);
    });

    testWidgets('should display retry button when onRetry is provided', (tester) async {
      bool retryPressed = false;
      
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ValidationErrorWidget(
              fieldErrors: {'email': 'Invalid format'},
              onRetry: () => retryPressed = true,
            ),
          ),
        ),
      );

      expect(find.text('Try Again'), findsOneWidget);
      
      await tester.tap(find.text('Try Again'));
      await tester.pump();
      
      expect(retryPressed, isTrue);
    });
  });

  group('LoadingErrorWidget', () {
    testWidgets('should display default loading error message', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: LoadingErrorWidget(),
          ),
        ),
      );

      expect(find.text('Failed to load data'), findsOneWidget);
      expect(find.byIcon(Icons.error_outline), findsOneWidget);
    });

    testWidgets('should display custom message when provided', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: LoadingErrorWidget(
              message: 'Custom loading error',
            ),
          ),
        ),
      );

      expect(find.text('Custom loading error'), findsOneWidget);
    });

    testWidgets('should call onRetry when retry button is pressed', (tester) async {
      bool retryPressed = false;
      
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: LoadingErrorWidget(
              onRetry: () => retryPressed = true,
            ),
          ),
        ),
      );

      await tester.tap(find.text('Retry'));
      await tester.pump();
      
      expect(retryPressed, isTrue);
    });
  });
}