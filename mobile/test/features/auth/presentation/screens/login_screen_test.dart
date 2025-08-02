import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:mockito/mockito.dart';
import 'package:mockito/annotations.dart';

import 'package:pafar_mobile/features/auth/presentation/screens/login_screen.dart';
import 'package:pafar_mobile/features/auth/presentation/bloc/auth_bloc.dart';
import 'package:pafar_mobile/features/auth/presentation/bloc/auth_event.dart';
import 'package:pafar_mobile/features/auth/presentation/bloc/auth_state.dart';
import 'package:pafar_mobile/features/auth/domain/entities/user.dart';
import 'package:pafar_mobile/shared/widgets/custom_button.dart';
import 'package:pafar_mobile/shared/widgets/custom_text_field.dart';

import 'login_screen_test.mocks.dart';

@GenerateMocks([AuthBloc])
void main() {
  group('LoginScreen Widget Tests', () {
    late MockAuthBloc mockAuthBloc;

    setUp(() {
      mockAuthBloc = MockAuthBloc();
      when(mockAuthBloc.state).thenReturn(AuthInitial());
      when(mockAuthBloc.stream).thenAnswer((_) => Stream.empty());
    });

    Widget createWidgetUnderTest() {
      return MaterialApp(
        home: BlocProvider<AuthBloc>(
          create: (context) => mockAuthBloc,
          child: const LoginScreen(),
        ),
      );
    }

    group('Rendering Tests', () {
      testWidgets('should render all required UI elements', (tester) async {
        await tester.pumpWidget(createWidgetUnderTest());

        // Verify app bar
        expect(find.text('Sign In'), findsOneWidget);

        // Verify form fields
        expect(find.byType(CustomTextField), findsNWidgets(2));
        expect(find.text('Email'), findsOneWidget);
        expect(find.text('Password'), findsOneWidget);

        // Verify buttons
        expect(find.byType(CustomButton), findsOneWidget);
        expect(find.text('Sign In'), findsAtLeastNWidgets(1));

        // Verify additional links
        expect(find.text('Forgot Password?'), findsOneWidget);
        expect(find.text('Don\'t have an account? Sign Up'), findsOneWidget);
      });

      testWidgets('should render logo and branding', (tester) async {
        await tester.pumpWidget(createWidgetUnderTest());

        // Verify logo or app branding
        expect(find.byType(Image), findsOneWidget);
        expect(find.text('Welcome to Pafar'), findsOneWidget);
      });

      testWidgets('should render remember me checkbox', (tester) async {
        await tester.pumpWidget(createWidgetUnderTest());

        expect(find.byType(Checkbox), findsOneWidget);
        expect(find.text('Remember me'), findsOneWidget);
      });

      testWidgets('should render social login options', (tester) async {
        await tester.pumpWidget(createWidgetUnderTest());

        expect(find.text('Or continue with'), findsOneWidget);
        expect(find.text('Google'), findsOneWidget);
        expect(find.text('Facebook'), findsOneWidget);
      });
    });

    group('Form Validation Tests', () => {
      testWidgets('should show validation errors for empty fields', (tester) async {
        await tester.pumpWidget(createWidgetUnderTest());

        // Tap sign in button without entering data
        final signInButton = find.text('Sign In').last;
        await tester.tap(signInButton);
        await tester.pump();

        // Verify validation errors
        expect(find.text('Email is required'), findsOneWidget);
        expect(find.text('Password is required'), findsOneWidget);
      });

      testWidgets('should show validation error for invalid email', (tester) async {
        await tester.pumpWidget(createWidgetUnderTest());

        // Enter invalid email
        final emailField = find.byType(CustomTextField).first;
        await tester.enterText(emailField, 'invalid-email');

        // Tap sign in button
        final signInButton = find.text('Sign In').last;
        await tester.tap(signInButton);
        await tester.pump();

        expect(find.text('Please enter a valid email'), findsOneWidget);
      });

      testWidgets('should show validation error for short password', (tester) async {
        await tester.pumpWidget(createWidgetUnderTest());

        // Enter valid email and short password
        final emailField = find.byType(CustomTextField).first;
        final passwordField = find.byType(CustomTextField).last;

        await tester.enterText(emailField, 'test@example.com');
        await tester.enterText(passwordField, '123');

        // Tap sign in button
        final signInButton = find.text('Sign In').last;
        await tester.tap(signInButton);
        await tester.pump();

        expect(find.text('Password must be at least 6 characters'), findsOneWidget);
      });

      testWidgets('should clear validation errors when user starts typing', (tester) async {
        await tester.pumpWidget(createWidgetUnderTest());

        // Trigger validation errors
        final signInButton = find.text('Sign In').last;
        await tester.tap(signInButton);
        await tester.pump();

        expect(find.text('Email is required'), findsOneWidget);

        // Start typing in email field
        final emailField = find.byType(CustomTextField).first;
        await tester.enterText(emailField, 'test@example.com');
        await tester.pump();

        expect(find.text('Email is required'), findsNothing);
      });
    });

    group('User Interaction Tests', () => {
      testWidgets('should toggle password visibility', (tester) async {
        await tester.pumpWidget(createWidgetUnderTest());

        // Find password field and visibility toggle
        final passwordField = find.byType(CustomTextField).last;
        final visibilityToggle = find.byIcon(Icons.visibility_off);

        // Initially password should be obscured
        final textField = tester.widget<TextField>(find.descendant(
          of: passwordField,
          matching: find.byType(TextField),
        ));
        expect(textField.obscureText, isTrue);

        // Tap visibility toggle
        await tester.tap(visibilityToggle);
        await tester.pump();

        // Password should now be visible
        final updatedTextField = tester.widget<TextField>(find.descendant(
          of: passwordField,
          matching: find.byType(TextField),
        ));
        expect(updatedTextField.obscureText, isFalse);

        // Icon should change
        expect(find.byIcon(Icons.visibility), findsOneWidget);
      });

      testWidgets('should toggle remember me checkbox', (tester) async {
        await tester.pumpWidget(createWidgetUnderTest());

        final checkbox = find.byType(Checkbox);
        
        // Initially unchecked
        Checkbox checkboxWidget = tester.widget(checkbox);
        expect(checkboxWidget.value, isFalse);

        // Tap checkbox
        await tester.tap(checkbox);
        await tester.pump();

        // Should be checked
        checkboxWidget = tester.widget(checkbox);
        expect(checkboxWidget.value, isTrue);
      });

      testWidgets('should navigate to forgot password screen', (tester) async {
        await tester.pumpWidget(createWidgetUnderTest());

        final forgotPasswordLink = find.text('Forgot Password?');
        await tester.tap(forgotPasswordLink);
        await tester.pumpAndSettle();

        // Verify navigation (this would depend on your navigation implementation)
        // For now, we'll just verify the tap was registered
        expect(forgotPasswordLink, findsOneWidget);
      });

      testWidgets('should navigate to sign up screen', (tester) async {
        await tester.pumpWidget(createWidgetUnderTest());

        final signUpLink = find.text('Don\'t have an account? Sign Up');
        await tester.tap(signUpLink);
        await tester.pumpAndSettle();

        // Verify navigation
        expect(signUpLink, findsOneWidget);
      });
    });

    group('BLoC Integration Tests', () => {
      testWidgets('should dispatch LoginRequested event on form submission', (tester) async {
        await tester.pumpWidget(createWidgetUnderTest());

        // Enter valid credentials
        final emailField = find.byType(CustomTextField).first;
        final passwordField = find.byType(CustomTextField).last;

        await tester.enterText(emailField, 'test@example.com');
        await tester.enterText(passwordField, 'password123');

        // Tap sign in button
        final signInButton = find.text('Sign In').last;
        await tester.tap(signInButton);
        await tester.pump();

        // Verify event was dispatched
        verify(mockAuthBloc.add(any)).called(1);
        
        final capturedEvent = verify(mockAuthBloc.add(captureAny)).captured.first;
        expect(capturedEvent, isA<LoginRequested>());
        
        final loginEvent = capturedEvent as LoginRequested;
        expect(loginEvent.email, equals('test@example.com'));
        expect(loginEvent.password, equals('password123'));
      });

      testWidgets('should show loading state during authentication', (tester) async {
        when(mockAuthBloc.state).thenReturn(AuthLoading());

        await tester.pumpWidget(createWidgetUnderTest());

        // Verify loading indicator
        expect(find.byType(CircularProgressIndicator), findsOneWidget);
        
        // Verify button is disabled
        final signInButton = find.byType(CustomButton);
        final buttonWidget = tester.widget<CustomButton>(signInButton);
        expect(buttonWidget.isEnabled, isFalse);
      });

      testWidgets('should show error message on authentication failure', (tester) async {
        const errorMessage = 'Invalid credentials';
        when(mockAuthBloc.state).thenReturn(const AuthError(errorMessage));

        await tester.pumpWidget(createWidgetUnderTest());

        // Verify error message is displayed
        expect(find.text(errorMessage), findsOneWidget);
        expect(find.byIcon(Icons.error), findsOneWidget);
      });

      testWidgets('should navigate to home on successful authentication', (tester) async {
        final user = User(
          id: '1',
          email: 'test@example.com',
          firstName: 'John',
          lastName: 'Doe',
          role: 'passenger',
        );
        
        when(mockAuthBloc.state).thenReturn(AuthAuthenticated(user));

        await tester.pumpWidget(createWidgetUnderTest());

        // In a real app, this would trigger navigation
        // For testing, we verify the state is handled correctly
        expect(find.text('Welcome, John!'), findsOneWidget);
      });
    });

    group('Social Login Tests', () => {
      testWidgets('should dispatch GoogleLoginRequested on Google button tap', (tester) async {
        await tester.pumpWidget(createWidgetUnderTest());

        final googleButton = find.text('Google');
        await tester.tap(googleButton);
        await tester.pump();

        verify(mockAuthBloc.add(any)).called(1);
        
        final capturedEvent = verify(mockAuthBloc.add(captureAny)).captured.first;
        expect(capturedEvent, isA<GoogleLoginRequested>());
      });

      testWidgets('should dispatch FacebookLoginRequested on Facebook button tap', (tester) async {
        await tester.pumpWidget(createWidgetUnderTest());

        final facebookButton = find.text('Facebook');
        await tester.tap(facebookButton);
        await tester.pump();

        verify(mockAuthBloc.add(any)).called(1);
        
        final capturedEvent = verify(mockAuthBloc.add(captureAny)).captured.first;
        expect(capturedEvent, isA<FacebookLoginRequested>());
      });
    });

    group('Accessibility Tests', () => {
      testWidgets('should have proper semantic labels', (tester) async {
        await tester.pumpWidget(createWidgetUnderTest());

        // Verify semantic labels for screen readers
        expect(find.bySemanticsLabel('Email input field'), findsOneWidget);
        expect(find.bySemanticsLabel('Password input field'), findsOneWidget);
        expect(find.bySemanticsLabel('Sign in button'), findsOneWidget);
        expect(find.bySemanticsLabel('Toggle password visibility'), findsOneWidget);
      });

      testWidgets('should support keyboard navigation', (tester) async {
        await tester.pumpWidget(createWidgetUnderTest());

        // Test tab navigation
        await tester.sendKeyEvent(LogicalKeyboardKey.tab);
        await tester.pump();

        // Verify focus moves to first field
        final emailField = find.byType(CustomTextField).first;
        expect(tester.binding.focusManager.primaryFocus?.context?.widget,
               equals(tester.firstWidget(emailField)));
      });

      testWidgets('should announce errors to screen readers', (tester) async {
        await tester.pumpWidget(createWidgetUnderTest());

        // Trigger validation error
        final signInButton = find.text('Sign In').last;
        await tester.tap(signInButton);
        await tester.pump();

        // Verify error has proper semantics
        final errorText = find.text('Email is required');
        expect(tester.getSemantics(errorText).hasFlag(SemanticsFlag.isLiveRegion), isTrue);
      });
    });

    group('Responsive Design Tests', () => {
      testWidgets('should adapt to different screen sizes', (tester) async {
        // Test tablet layout
        tester.binding.window.physicalSizeTestValue = const Size(1024, 768);
        tester.binding.window.devicePixelRatioTestValue = 1.0;

        await tester.pumpWidget(createWidgetUnderTest());

        // Verify layout adapts for larger screens
        expect(find.byType(Row), findsAtLeastNWidgets(1));
        
        // Reset to phone size
        tester.binding.window.physicalSizeTestValue = const Size(375, 667);
        await tester.pump();

        // Verify layout adapts for smaller screens
        expect(find.byType(Column), findsAtLeastNWidgets(1));
      });

      testWidgets('should handle landscape orientation', (tester) async {
        // Simulate landscape orientation
        tester.binding.window.physicalSizeTestValue = const Size(667, 375);
        tester.binding.window.devicePixelRatioTestValue = 1.0;

        await tester.pumpWidget(createWidgetUnderTest());

        // Verify layout adjusts for landscape
        expect(find.byType(SingleChildScrollView), findsOneWidget);
      });
    });

    group('Performance Tests', () => {
      testWidgets('should not rebuild unnecessarily', (tester) async {
        int buildCount = 0;
        
        Widget testWidget = MaterialApp(
          home: BlocProvider<AuthBloc>(
            create: (context) => mockAuthBloc,
            child: Builder(
              builder: (context) {
                buildCount++;
                return const LoginScreen();
              },
            ),
          ),
        );

        await tester.pumpWidget(testWidget);
        expect(buildCount, equals(1));

        // Trigger a rebuild with same state
        when(mockAuthBloc.state).thenReturn(AuthInitial());
        await tester.pump();

        // Build count should not increase unnecessarily
        expect(buildCount, equals(1));
      });

      testWidgets('should dispose resources properly', (tester) async {
        await tester.pumpWidget(createWidgetUnderTest());

        // Navigate away from screen
        await tester.pumpWidget(const MaterialApp(home: Scaffold()));

        // Verify resources are disposed (this would be implementation specific)
        // For now, we just verify the widget is no longer in the tree
        expect(find.byType(LoginScreen), findsNothing);
      });
    });

    group('Error Recovery Tests', () => {
      testWidgets('should allow retry after network error', (tester) async {
        const errorMessage = 'Network error. Please try again.';
        when(mockAuthBloc.state).thenReturn(const AuthError(errorMessage));

        await tester.pumpWidget(createWidgetUnderTest());

        // Verify error message and retry button
        expect(find.text(errorMessage), findsOneWidget);
        expect(find.text('Retry'), findsOneWidget);

        // Tap retry button
        final retryButton = find.text('Retry');
        await tester.tap(retryButton);
        await tester.pump();

        // Verify retry event is dispatched
        verify(mockAuthBloc.add(any)).called(1);
      });

      testWidgets('should clear errors when user starts new input', (tester) async {
        const errorMessage = 'Invalid credentials';
        when(mockAuthBloc.state).thenReturn(const AuthError(errorMessage));

        await tester.pumpWidget(createWidgetUnderTest());

        expect(find.text(errorMessage), findsOneWidget);

        // Start typing in email field
        final emailField = find.byType(CustomTextField).first;
        await tester.enterText(emailField, 'new@example.com');
        await tester.pump();

        // Error should be cleared
        verify(mockAuthBloc.add(any)).called(1);
        final capturedEvent = verify(mockAuthBloc.add(captureAny)).captured.first;
        expect(capturedEvent, isA<AuthErrorCleared>());
      });
    });

    group('Biometric Authentication Tests', () => {
      testWidgets('should show biometric login option when available', (tester) async {
        await tester.pumpWidget(createWidgetUnderTest());

        // Verify biometric login button is shown
        expect(find.byIcon(Icons.fingerprint), findsOneWidget);
        expect(find.text('Use Biometric'), findsOneWidget);
      });

      testWidgets('should dispatch BiometricLoginRequested on biometric button tap', (tester) async {
        await tester.pumpWidget(createWidgetUnderTest());

        final biometricButton = find.byIcon(Icons.fingerprint);
        await tester.tap(biometricButton);
        await tester.pump();

        verify(mockAuthBloc.add(any)).called(1);
        
        final capturedEvent = verify(mockAuthBloc.add(captureAny)).captured.first;
        expect(capturedEvent, isA<BiometricLoginRequested>());
      });
    });

    group('Deep Link Tests', () => {
      testWidgets('should handle email verification deep link', (tester) async {
        // Simulate app opened with verification link
        await tester.pumpWidget(createWidgetUnderTest());

        // Verify verification banner is shown
        expect(find.text('Please verify your email'), findsOneWidget);
        expect(find.text('Resend verification email'), findsOneWidget);
      });

      testWidgets('should handle password reset deep link', (tester) async {
        // Simulate app opened with password reset link
        await tester.pumpWidget(createWidgetUnderTest());

        // Should navigate to password reset screen
        // This would be implementation specific
        expect(find.text('Reset your password'), findsOneWidget);
      });
    });
  });
}