import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/mockito.dart';
import 'package:mockito/annotations.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:get_it/get_it.dart';

import 'package:mobile/features/auth/presentation/screens/login_screen.dart';
import 'package:mobile/features/auth/presentation/bloc/auth_bloc.dart';
import 'package:mobile/features/auth/presentation/bloc/auth_event.dart';
import 'package:mobile/features/auth/presentation/bloc/auth_state.dart';
import 'package:mobile/features/auth/domain/entities/user.dart';
import 'package:mobile/core/error/failures.dart';
import 'package:mobile/shared/widgets/custom_button.dart';
import 'package:mobile/shared/widgets/custom_text_field.dart';
import 'package:mobile/shared/widgets/loading_widget.dart';
import 'package:mobile/shared/widgets/error_widget.dart' as custom_error;

import 'login_screen_comprehensive_test.mocks.dart';

@GenerateMocks([AuthBloc])
void main() {
  group('LoginScreen Comprehensive Tests', () {
    late MockAuthBloc mockAuthBloc;
    late GetIt getIt;

    setUp(() {
      mockAuthBloc = MockAuthBloc();
      getIt = GetIt.instance;
      
      // Reset GetIt
      if (getIt.isRegistered<AuthBloc>()) {
        getIt.unregister<AuthBloc>();
      }
      getIt.registerFactory<AuthBloc>(() => mockAuthBloc);

      // Set up default mock behavior
      when(mockAuthBloc.state).thenReturn(AuthInitial());
      when(mockAuthBloc.stream).thenAnswer((_) => Stream.fromIterable([AuthInitial()]));
    });

    tearDown(() {
      getIt.reset();
    });

    Widget createWidgetUnderTest() {
      return MaterialApp(
        home: BlocProvider<AuthBloc>(
          create: (context) => mockAuthBloc,
          child: const LoginScreen(),
        ),
      );
    }

    group('Widget Rendering', () {
      testWidgets('renders all required UI elements', (WidgetTester tester) async {
        await tester.pumpWidget(createWidgetUnderTest());

        // Check for main UI elements
        expect(find.text('Welcome Back'), findsOneWidget);
        expect(find.text('Sign in to your account'), findsOneWidget);
        
        // Check for form fields
        expect(find.byType(CustomTextField), findsNWidgets(2));
        expect(find.text('Email'), findsOneWidget);
        expect(find.text('Password'), findsOneWidget);
        
        // Check for buttons
        expect(find.byType(CustomButton), findsOneWidget);
        expect(find.text('Sign In'), findsOneWidget);
        
        // Check for additional links
        expect(find.text('Forgot Password?'), findsOneWidget);
        expect(find.text('Don\'t have an account?'), findsOneWidget);
        expect(find.text('Sign Up'), findsOneWidget);
      });

      testWidgets('has proper accessibility labels', (WidgetTester tester) async {
        await tester.pumpWidget(createWidgetUnderTest());

        // Check for semantic labels
        expect(find.bySemanticsLabel('Email input field'), findsOneWidget);
        expect(find.bySemanticsLabel('Password input field'), findsOneWidget);
        expect(find.bySemanticsLabel('Sign in button'), findsOneWidget);
        expect(find.bySemanticsLabel('Forgot password link'), findsOneWidget);
        expect(find.bySemanticsLabel('Sign up link'), findsOneWidget);
      });

      testWidgets('displays app logo and branding', (WidgetTester tester) async {
        await tester.pumpWidget(createWidgetUnderTest());

        // Check for logo or app branding
        expect(find.byType(Image), findsAtLeastNWidgets(1));
        expect(find.text('Pafar'), findsOneWidget);
      });
    });

    group('Form Validation', () {
      testWidgets('shows validation errors for empty fields', (WidgetTester tester) async {
        await tester.pumpWidget(createWidgetUnderTest());

        // Tap sign in button without entering any data
        await tester.tap(find.byType(CustomButton));
        await tester.pump();

        // Check for validation error messages
        expect(find.text('Email is required'), findsOneWidget);
        expect(find.text('Password is required'), findsOneWidget);
      });

      testWidgets('validates email format', (WidgetTester tester) async {
        await tester.pumpWidget(createWidgetUnderTest());

        // Enter invalid email
        await tester.enterText(
          find.byType(CustomTextField).first,
          'invalid-email'
        );
        await tester.tap(find.byType(CustomButton));
        await tester.pump();

        expect(find.text('Please enter a valid email'), findsOneWidget);
      });

      testWidgets('validates password length', (WidgetTester tester) async {
        await tester.pumpWidget(createWidgetUnderTest());

        // Enter short password
        await tester.enterText(
          find.byType(CustomTextField).last,
          '123'
        );
        await tester.tap(find.byType(CustomButton));
        await tester.pump();

        expect(find.text('Password must be at least 6 characters'), findsOneWidget);
      });

      testWidgets('clears validation errors when user corrects input', (WidgetTester tester) async {
        await tester.pumpWidget(createWidgetUnderTest());

        // Trigger validation error
        await tester.tap(find.byType(CustomButton));
        await tester.pump();
        expect(find.text('Email is required'), findsOneWidget);

        // Correct the input
        await tester.enterText(
          find.byType(CustomTextField).first,
          'test@example.com'
        );
        await tester.pump();

        // Error should be cleared
        expect(find.text('Email is required'), findsNothing);
      });

      testWidgets('validates both fields before submission', (WidgetTester tester) async {
        await tester.pumpWidget(createWidgetUnderTest());

        // Enter valid email but invalid password
        await tester.enterText(
          find.byType(CustomTextField).first,
          'test@example.com'
        );
        await tester.enterText(
          find.byType(CustomTextField).last,
          '123'
        );
        await tester.tap(find.byType(CustomButton));
        await tester.pump();

        // Should show password error but not email error
        expect(find.text('Email is required'), findsNothing);
        expect(find.text('Password must be at least 6 characters'), findsOneWidget);
      });
    });

    group('Authentication Flow', () {
      testWidgets('triggers login event with valid credentials', (WidgetTester tester) async {
        await tester.pumpWidget(createWidgetUnderTest());

        // Enter valid credentials
        await tester.enterText(
          find.byType(CustomTextField).first,
          'test@example.com'
        );
        await tester.enterText(
          find.byType(CustomTextField).last,
          'password123'
        );

        // Tap sign in button
        await tester.tap(find.byType(CustomButton));
        await tester.pump();

        // Verify that login event was triggered
        verify(mockAuthBloc.add(any)).called(1);
        
        // Verify the event contains correct data
        final capturedEvents = verify(mockAuthBloc.add(captureAny)).captured;
        final loginEvent = capturedEvents.first as LoginRequested;
        expect(loginEvent.email, 'test@example.com');
        expect(loginEvent.password, 'password123');
      });

      testWidgets('shows loading state during authentication', (WidgetTester tester) async {
        // Set up loading state
        when(mockAuthBloc.state).thenReturn(AuthLoading());
        when(mockAuthBloc.stream).thenAnswer((_) => Stream.fromIterable([AuthLoading()]));

        await tester.pumpWidget(createWidgetUnderTest());

        // Should show loading widget
        expect(find.byType(LoadingWidget), findsOneWidget);
        expect(find.text('Signing in...'), findsOneWidget);
        
        // Sign in button should be disabled
        final button = tester.widget<CustomButton>(find.byType(CustomButton));
        expect(button.isEnabled, false);
      });

      testWidgets('shows error message on authentication failure', (WidgetTester tester) async {
        const errorMessage = 'Invalid credentials';
        
        // Set up error state
        when(mockAuthBloc.state).thenReturn(
          AuthError(ServerFailure(errorMessage))
        );
        when(mockAuthBloc.stream).thenAnswer((_) => Stream.fromIterable([
          AuthError(ServerFailure(errorMessage))
        ]));

        await tester.pumpWidget(createWidgetUnderTest());

        // Should show error message
        expect(find.byType(custom_error.ErrorWidget), findsOneWidget);
        expect(find.text(errorMessage), findsOneWidget);
        
        // Form should be re-enabled
        final button = tester.widget<CustomButton>(find.byType(CustomButton));
        expect(button.isEnabled, true);
      });

      testWidgets('navigates to home screen on successful authentication', (WidgetTester tester) async {
        const user = User(
          id: '1',
          email: 'test@example.com',
          firstName: 'Test',
          lastName: 'User',
          role: UserRole.passenger,
        );

        // Set up success state
        when(mockAuthBloc.state).thenReturn(AuthAuthenticated(user));
        when(mockAuthBloc.stream).thenAnswer((_) => Stream.fromIterable([
          AuthAuthenticated(user)
        ]));

        await tester.pumpWidget(
          MaterialApp(
            home: BlocProvider<AuthBloc>(
              create: (context) => mockAuthBloc,
              child: const LoginScreen(),
            ),
            routes: {
              '/home': (context) => const Scaffold(body: Text('Home Screen')),
            },
          ),
        );

        await tester.pumpAndSettle();

        // Should navigate to home screen
        expect(find.text('Home Screen'), findsOneWidget);
      });
    });

    group('User Interactions', () => {
      testWidgets('toggles password visibility', (WidgetTester tester) async {
        await tester.pumpWidget(createWidgetUnderTest());

        // Find password field
        final passwordField = find.byType(CustomTextField).last;
        final passwordWidget = tester.widget<CustomTextField>(passwordField);
        
        // Initially should be obscured
        expect(passwordWidget.obscureText, true);

        // Tap visibility toggle
        await tester.tap(find.byIcon(Icons.visibility));
        await tester.pump();

        // Should now be visible
        final updatedPasswordWidget = tester.widget<CustomTextField>(passwordField);
        expect(updatedPasswordWidget.obscureText, false);

        // Tap again to hide
        await tester.tap(find.byIcon(Icons.visibility_off));
        await tester.pump();

        // Should be obscured again
        final finalPasswordWidget = tester.widget<CustomTextField>(passwordField);
        expect(finalPasswordWidget.obscureText, true);
      });

      testWidgets('handles keyboard navigation', (WidgetTester tester) async {
        await tester.pumpWidget(createWidgetUnderTest());

        // Focus on email field
        await tester.tap(find.byType(CustomTextField).first);
        await tester.pump();

        // Enter email and press tab (or next)
        await tester.enterText(
          find.byType(CustomTextField).first,
          'test@example.com'
        );
        await tester.testTextInput.receiveAction(TextInputAction.next);
        await tester.pump();

        // Password field should now have focus
        final passwordField = find.byType(CustomTextField).last;
        expect(tester.binding.focusManager.primaryFocus?.context?.widget,
               tester.widget(passwordField));
      });

      testWidgets('submits form on enter key press', (WidgetTester tester) async {
        await tester.pumpWidget(createWidgetUnderTest());

        // Enter valid credentials
        await tester.enterText(
          find.byType(CustomTextField).first,
          'test@example.com'
        );
        await tester.enterText(
          find.byType(CustomTextField).last,
          'password123'
        );

        // Press enter on password field
        await tester.testTextInput.receiveAction(TextInputAction.done);
        await tester.pump();

        // Should trigger login
        verify(mockAuthBloc.add(any)).called(1);
      });

      testWidgets('handles forgot password tap', (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: BlocProvider<AuthBloc>(
              create: (context) => mockAuthBloc,
              child: const LoginScreen(),
            ),
            routes: {
              '/forgot-password': (context) => const Scaffold(
                body: Text('Forgot Password Screen')
              ),
            },
          ),
        );

        // Tap forgot password link
        await tester.tap(find.text('Forgot Password?'));
        await tester.pumpAndSettle();

        // Should navigate to forgot password screen
        expect(find.text('Forgot Password Screen'), findsOneWidget);
      });

      testWidgets('handles sign up tap', (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: BlocProvider<AuthBloc>(
              create: (context) => mockAuthBloc,
              child: const LoginScreen(),
            ),
            routes: {
              '/register': (context) => const Scaffold(
                body: Text('Register Screen')
              ),
            },
          ),
        );

        // Tap sign up link
        await tester.tap(find.text('Sign Up'));
        await tester.pumpAndSettle();

        // Should navigate to register screen
        expect(find.text('Register Screen'), findsOneWidget);
      });
    });

    group('State Management', () => {
      testWidgets('responds to auth state changes', (WidgetTester tester) async {
        // Start with initial state
        when(mockAuthBloc.state).thenReturn(AuthInitial());
        
        final stateController = StreamController<AuthState>();
        when(mockAuthBloc.stream).thenAnswer((_) => stateController.stream);

        await tester.pumpWidget(createWidgetUnderTest());

        // Initial state - form should be enabled
        expect(find.byType(LoadingWidget), findsNothing);
        expect(find.byType(custom_error.ErrorWidget), findsNothing);

        // Emit loading state
        stateController.add(AuthLoading());
        await tester.pump();

        // Should show loading
        expect(find.byType(LoadingWidget), findsOneWidget);

        // Emit error state
        stateController.add(AuthError(ServerFailure('Login failed')));
        await tester.pump();

        // Should show error
        expect(find.byType(LoadingWidget), findsNothing);
        expect(find.byType(custom_error.ErrorWidget), findsOneWidget);
        expect(find.text('Login failed'), findsOneWidget);

        stateController.close();
      });

      testWidgets('preserves form data during state changes', (WidgetTester tester) async {
        final stateController = StreamController<AuthState>();
        when(mockAuthBloc.stream).thenAnswer((_) => stateController.stream);

        await tester.pumpWidget(createWidgetUnderTest());

        // Enter some data
        await tester.enterText(
          find.byType(CustomTextField).first,
          'test@example.com'
        );
        await tester.enterText(
          find.byType(CustomTextField).last,
          'password123'
        );

        // Change state to loading
        stateController.add(AuthLoading());
        await tester.pump();

        // Change back to initial
        stateController.add(AuthInitial());
        await tester.pump();

        // Form data should be preserved
        expect(find.text('test@example.com'), findsOneWidget);
        expect(find.text('password123'), findsOneWidget);

        stateController.close();
      });
    });

    group('Error Handling', () => {
      testWidgets('handles network errors', (WidgetTester tester) async {
        when(mockAuthBloc.state).thenReturn(
          AuthError(NetworkFailure('No internet connection'))
        );
        when(mockAuthBloc.stream).thenAnswer((_) => Stream.fromIterable([
          AuthError(NetworkFailure('No internet connection'))
        ]));

        await tester.pumpWidget(createWidgetUnderTest());

        expect(find.text('No internet connection'), findsOneWidget);
        expect(find.byType(custom_error.ErrorWidget), findsOneWidget);
      });

      testWidgets('handles server errors', (WidgetTester tester) async {
        when(mockAuthBloc.state).thenReturn(
          AuthError(ServerFailure('Server is temporarily unavailable'))
        );
        when(mockAuthBloc.stream).thenAnswer((_) => Stream.fromIterable([
          AuthError(ServerFailure('Server is temporarily unavailable'))
        ]));

        await tester.pumpWidget(createWidgetUnderTest());

        expect(find.text('Server is temporarily unavailable'), findsOneWidget);
        expect(find.byType(custom_error.ErrorWidget), findsOneWidget);
      });

      testWidgets('handles validation errors from server', (WidgetTester tester) async {
        when(mockAuthBloc.state).thenReturn(
          AuthError(ValidationFailure('Invalid email or password'))
        );
        when(mockAuthBloc.stream).thenAnswer((_) => Stream.fromIterable([
          AuthError(ValidationFailure('Invalid email or password'))
        ]));

        await tester.pumpWidget(createWidgetUnderTest());

        expect(find.text('Invalid email or password'), findsOneWidget);
      });

      testWidgets('shows retry option on error', (WidgetTester tester) async {
        when(mockAuthBloc.state).thenReturn(
          AuthError(NetworkFailure('Connection failed'))
        );
        when(mockAuthBloc.stream).thenAnswer((_) => Stream.fromIterable([
          AuthError(NetworkFailure('Connection failed'))
        ]));

        await tester.pumpWidget(createWidgetUnderTest());

        // Should show retry button
        expect(find.text('Retry'), findsOneWidget);

        // Tap retry
        await tester.tap(find.text('Retry'));
        await tester.pump();

        // Should trigger retry event
        verify(mockAuthBloc.add(any)).called(1);
      });
    });

    group('Accessibility', () => {
      testWidgets('has proper semantic structure', (WidgetTester tester) async {
        await tester.pumpWidget(createWidgetUnderTest());

        // Check for semantic structure
        expect(find.bySemanticsLabel('Login form'), findsOneWidget);
        expect(find.bySemanticsLabel('Email input field'), findsOneWidget);
        expect(find.bySemanticsLabel('Password input field'), findsOneWidget);
        expect(find.bySemanticsLabel('Sign in button'), findsOneWidget);
      });

      testWidgets('supports screen reader navigation', (WidgetTester tester) async {
        await tester.pumpWidget(createWidgetUnderTest());

        // Test semantic traversal order
        final semantics = tester.binding.pipelineOwner.semanticsOwner!;
        final rootNode = semantics.rootSemanticsNode!;
        
        // Should have proper semantic tree structure
        expect(rootNode.childrenCount, greaterThan(0));
      });

      testWidgets('announces errors to screen readers', (WidgetTester tester) async {
        await tester.pumpWidget(createWidgetUnderTest());

        // Trigger validation error
        await tester.tap(find.byType(CustomButton));
        await tester.pump();

        // Error messages should be announced
        final errorWidget = find.text('Email is required');
        expect(errorWidget, findsOneWidget);
        
        final semantics = tester.getSemantics(errorWidget);
        expect(semantics.hasFlag(SemanticsFlag.isLiveRegion), true);
      });
    });

    group('Performance', () => {
      testWidgets('does not rebuild unnecessarily', (WidgetTester tester) async {
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
        expect(buildCount, 1);

        // Pump again with same widget
        await tester.pumpWidget(testWidget);
        expect(buildCount, 1); // Should not rebuild
      });

      testWidgets('handles rapid user input efficiently', (WidgetTester tester) async {
        await tester.pumpWidget(createWidgetUnderTest());

        final emailField = find.byType(CustomTextField).first;

        // Rapidly enter text
        for (int i = 0; i < 10; i++) {
          await tester.enterText(emailField, 'test$i@example.com');
          await tester.pump(const Duration(milliseconds: 10));
        }

        // Should handle all input without errors
        expect(tester.takeException(), isNull);
      });
    });

    group('Edge Cases', () => {
      testWidgets('handles very long email addresses', (WidgetTester tester) async {
        await tester.pumpWidget(createWidgetUnderTest());

        final longEmail = 'a' * 100 + '@example.com';
        await tester.enterText(
          find.byType(CustomTextField).first,
          longEmail
        );

        expect(find.text(longEmail), findsOneWidget);
      });

      testWidgets('handles special characters in password', (WidgetTester tester) async {
        await tester.pumpWidget(createWidgetUnderTest());

        const specialPassword = 'P@ssw0rd!@#\$%^&*()';
        await tester.enterText(
          find.byType(CustomTextField).last,
          specialPassword
        );

        // Should handle special characters without issues
        expect(tester.takeException(), isNull);
      });

      testWidgets('handles empty responses from server', (WidgetTester tester) async {
        when(mockAuthBloc.state).thenReturn(
          AuthError(ServerFailure(''))
        );
        when(mockAuthBloc.stream).thenAnswer((_) => Stream.fromIterable([
          AuthError(ServerFailure(''))
        ]));

        await tester.pumpWidget(createWidgetUnderTest());

        // Should show generic error message for empty server response
        expect(find.text('An error occurred'), findsOneWidget);
      });

      testWidgets('handles multiple rapid button taps', (WidgetTester tester) async {
        await tester.pumpWidget(createWidgetUnderTest());

        // Enter valid credentials
        await tester.enterText(
          find.byType(CustomTextField).first,
          'test@example.com'
        );
        await tester.enterText(
          find.byType(CustomTextField).last,
          'password123'
        );

        // Rapidly tap sign in button multiple times
        for (int i = 0; i < 5; i++) {
          await tester.tap(find.byType(CustomButton));
          await tester.pump(const Duration(milliseconds: 10));
        }

        // Should only trigger login once (debounced)
        verify(mockAuthBloc.add(any)).called(1);
      });
    });
  });
}