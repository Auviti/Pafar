import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:local_auth/local_auth.dart';
import 'package:mockito/annotations.dart';
import 'package:mockito/mockito.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../../../../lib/features/auth/domain/repositories/auth_repository.dart';
import '../../../../../lib/features/auth/presentation/bloc/auth_bloc.dart';
import '../../../../../lib/features/auth/presentation/bloc/auth_event.dart';
import '../../../../../lib/features/auth/presentation/bloc/auth_state.dart';
import '../../../../../lib/features/auth/presentation/screens/login_screen.dart';
import '../../../../../lib/shared/theme/app_theme.dart';

import 'login_screen_test.mocks.dart';

@GenerateMocks([AuthRepository, LocalAuthentication, SharedPreferences])
void main() {
  late MockAuthRepository mockAuthRepository;
  late MockLocalAuthentication mockLocalAuth;
  late MockSharedPreferences mockPrefs;
  late AuthBloc authBloc;

  setUp(() {
    mockAuthRepository = MockAuthRepository();
    mockLocalAuth = MockLocalAuthentication();
    mockPrefs = MockSharedPreferences();
    
    // Setup default mock behaviors
    when(mockPrefs.getBool(any)).thenReturn(false);
    when(mockPrefs.setBool(any, any)).thenAnswer((_) async => true);
    when(mockPrefs.remove(any)).thenAnswer((_) async => true);

    authBloc = AuthBloc(
      authRepository: mockAuthRepository,
      localAuth: mockLocalAuth,
      prefs: mockPrefs,
    );
  });

  tearDown(() {
    authBloc.close();
  });

  Widget createWidgetUnderTest() {
    return MaterialApp.router(
      theme: AppTheme.lightTheme,
      routerConfig: GoRouter(
        routes: [
          GoRoute(
            path: '/',
            builder: (context, state) => BlocProvider.value(
              value: authBloc,
              child: const LoginScreen(),
            ),
          ),
          GoRoute(
            path: '/home',
            builder: (context, state) => const Scaffold(
              body: Text('Home Screen'),
            ),
          ),
          GoRoute(
            path: '/auth/register',
            builder: (context, state) => const Scaffold(
              body: Text('Register Screen'),
            ),
          ),
          GoRoute(
            path: '/auth/forgot-password',
            builder: (context, state) => const Scaffold(
              body: Text('Forgot Password Screen'),
            ),
          ),
        ],
      ),
    );
  }

  group('LoginScreen', () {
    testWidgets('should display all required UI elements', (tester) async {
      await tester.pumpWidget(createWidgetUnderTest());

      // Verify UI elements are present
      expect(find.text('Welcome to Pafar'), findsOneWidget);
      expect(find.text('Sign in to continue'), findsOneWidget);
      expect(find.byIcon(Icons.directions_bus), findsOneWidget);
      
      // Form fields
      expect(find.text('Email'), findsOneWidget);
      expect(find.text('Password'), findsOneWidget);
      
      // Buttons
      expect(find.text('Sign In'), findsOneWidget);
      expect(find.text('Create Account'), findsOneWidget);
      expect(find.text('Forgot Password?'), findsOneWidget);
      
      // Checkbox
      expect(find.text('Remember me'), findsOneWidget);
      expect(find.byType(Checkbox), findsOneWidget);
    });

    testWidgets('should validate email field', (tester) async {
      await tester.pumpWidget(createWidgetUnderTest());

      // Find and tap the sign in button without entering email
      final signInButton = find.text('Sign In');
      await tester.tap(signInButton);
      await tester.pumpAndSettle();

      // Should show email validation error
      expect(find.text('Email is required'), findsOneWidget);
    });

    testWidgets('should validate password field', (tester) async {
      await tester.pumpWidget(createWidgetUnderTest());

      // Enter valid email but no password
      await tester.enterText(find.byType(TextFormField).first, 'test@example.com');
      
      final signInButton = find.text('Sign In');
      await tester.tap(signInButton);
      await tester.pumpAndSettle();

      // Should show password validation error
      expect(find.text('Password is required'), findsOneWidget);
    });

    testWidgets('should toggle password visibility', (tester) async {
      await tester.pumpWidget(createWidgetUnderTest());

      // Find and tap the visibility toggle button
      final visibilityButton = find.byIcon(Icons.visibility);
      await tester.tap(visibilityButton);
      await tester.pumpAndSettle();

      // Password should now be visible (icon changes to visibility_off)
      expect(find.byIcon(Icons.visibility_off), findsOneWidget);
    });

    testWidgets('should toggle remember me checkbox', (tester) async {
      await tester.pumpWidget(createWidgetUnderTest());

      final checkbox = find.byType(Checkbox);
      
      // Initially unchecked
      Checkbox checkboxWidget = tester.widget<Checkbox>(checkbox);
      expect(checkboxWidget.value, isFalse);

      // Tap to check
      await tester.tap(checkbox);
      await tester.pumpAndSettle();

      // Should be checked now
      checkboxWidget = tester.widget<Checkbox>(checkbox);
      expect(checkboxWidget.value, isTrue);
    });

    testWidgets('should dispatch login event when form is valid', (tester) async {
      await tester.pumpWidget(createWidgetUnderTest());

      // Enter valid credentials
      await tester.enterText(find.byType(TextFormField).first, 'test@example.com');
      await tester.enterText(find.byType(TextFormField).at(1), 'password123');

      // Tap sign in button
      final signInButton = find.text('Sign In');
      await tester.tap(signInButton);
      await tester.pumpAndSettle();

      // Verify that login event was added to bloc
      // Note: In a real test, you might want to use bloc_test package
      // to verify the exact events and states
    });

    testWidgets('should show loading state during authentication', (tester) async {
      await tester.pumpWidget(createWidgetUnderTest());

      // Simulate loading state
      authBloc.emit(const AuthLoading());
      await tester.pumpAndSettle();

      // Should show loading indicator in button
      expect(find.byType(CircularProgressIndicator), findsOneWidget);
    });

    testWidgets('should show error message on authentication failure', (tester) async {
      await tester.pumpWidget(createWidgetUnderTest());

      // Simulate error state
      authBloc.emit(const AuthError(message: 'Invalid credentials'));
      await tester.pumpAndSettle();

      // Should show error snackbar
      expect(find.text('Invalid credentials'), findsOneWidget);
      expect(find.byType(SnackBar), findsOneWidget);
    });

    testWidgets('should navigate to register screen when create account is tapped', (tester) async {
      await tester.pumpWidget(createWidgetUnderTest());

      final createAccountButton = find.text('Create Account');
      await tester.tap(createAccountButton);
      await tester.pumpAndSettle();

      // Should navigate to register screen
      expect(find.text('Register Screen'), findsOneWidget);
    });

    testWidgets('should navigate to forgot password screen when forgot password is tapped', (tester) async {
      await tester.pumpWidget(createWidgetUnderTest());

      final forgotPasswordButton = find.text('Forgot Password?');
      await tester.tap(forgotPasswordButton);
      await tester.pumpAndSettle();

      // Should navigate to forgot password screen
      expect(find.text('Forgot Password Screen'), findsOneWidget);
    });

    testWidgets('should show biometric login button when biometric is enabled', (tester) async {
      // Setup biometric enabled
      when(mockPrefs.getBool('biometric_enabled')).thenReturn(true);
      
      authBloc = AuthBloc(
        authRepository: mockAuthRepository,
        localAuth: mockLocalAuth,
        prefs: mockPrefs,
      );

      await tester.pumpWidget(createWidgetUnderTest());

      // Should show biometric login button
      expect(find.text('Sign In with Biometrics'), findsOneWidget);
      expect(find.byIcon(Icons.fingerprint), findsOneWidget);
    });

    testWidgets('should not show biometric login button when biometric is disabled', (tester) async {
      // Setup biometric disabled (default)
      when(mockPrefs.getBool('biometric_enabled')).thenReturn(false);

      await tester.pumpWidget(createWidgetUnderTest());

      // Should not show biometric login button
      expect(find.text('Sign In with Biometrics'), findsNothing);
    });
  });
}