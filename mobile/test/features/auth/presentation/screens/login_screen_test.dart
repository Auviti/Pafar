import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:local_auth/local_auth.dart';
import 'package:mockito/annotations.dart';
import 'package:mockito/mockito.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../../../../lib/features/auth/domain/repositories/auth_repository.dart';
import '../../../../../lib/features/auth/domain/entities/user.dart';
import '../../../../../lib/features/auth/presentation/bloc/auth_bloc.dart';
import '../../../../../lib/features/auth/presentation/bloc/auth_state.dart';
import '../../../../../lib/features/auth/presentation/screens/login_screen.dart';
import '../../../../../lib/shared/theme/app_theme.dart';
import '../../../../../lib/core/error/failures.dart';

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
            path: '/register',
            builder: (context, state) => const Scaffold(
              body: Center(child: Text('Register Screen')),
            ),
          ),
          GoRoute(
            path: '/forgot-password',
            builder: (context, state) => const Scaffold(
              body: Center(child: Text('Forgot Password Screen')),
            ),
          ),
          GoRoute(
            path: '/dashboard',
            builder: (context, state) => const Scaffold(
              body: Center(child: Text('Dashboard Screen')),
            ),
          ),
        ],
      ),
    );
  }

  group('LoginScreen Widget Tests', () {
    testWidgets('renders login form with all required fields', (tester) async {
      await tester.pumpWidget(createWidgetUnderTest());
      await tester.pumpAndSettle();

      // Check for main UI elements
      expect(find.text('Welcome Back'), findsOneWidget);
      expect(find.text('Sign in to your account'), findsOneWidget);
      
      // Check for form fields
      expect(find.byType(TextFormField), findsNWidgets(2));
      expect(find.text('Email'), findsOneWidget);
      expect(find.text('Password'), findsOneWidget);
      
      // Check for buttons
      expect(find.text('Sign In'), findsOneWidget);
      expect(find.text('Sign Up'), findsOneWidget);
      expect(find.text('Forgot Password?'), findsOneWidget);
    });

    testWidgets('validates empty email field', (tester) async {
      await tester.pumpWidget(createWidgetUnderTest());
      await tester.pumpAndSettle();

      // Tap sign in without entering email
      await tester.tap(find.text('Sign In'));
      await tester.pumpAndSettle();

      expect(find.text('Please enter your email'), findsOneWidget);
    });

    testWidgets('validates invalid email format', (tester) async {
      await tester.pumpWidget(createWidgetUnderTest());
      await tester.pumpAndSettle();

      // Enter invalid email
      await tester.enterText(
        find.widgetWithText(TextFormField, 'Email'),
        'invalid-email',
      );
      await tester.tap(find.text('Sign In'));
      await tester.pumpAndSettle();

      expect(find.text('Please enter a valid email'), findsOneWidget);
    });

    testWidgets('validates empty password field', (tester) async {
      await tester.pumpWidget(createWidgetUnderTest());
      await tester.pumpAndSettle();

      // Enter email but no password
      await tester.enterText(
        find.widgetWithText(TextFormField, 'Email'),
        'test@example.com',
      );
      await tester.tap(find.text('Sign In'));
      await tester.pumpAndSettle();

      expect(find.text('Please enter your password'), findsOneWidget);
    });

    testWidgets('validates password minimum length', (tester) async {
      await tester.pumpWidget(createWidgetUnderTest());
      await tester.pumpAndSettle();

      // Enter short password
      await tester.enterText(
        find.widgetWithText(TextFormField, 'Email'),
        'test@example.com',
      );
      await tester.enterText(
        find.widgetWithText(TextFormField, 'Password'),
        '123',
      );
      await tester.tap(find.text('Sign In'));
      await tester.pumpAndSettle();

      expect(find.text('Password must be at least 6 characters'), findsOneWidget);
    });

    testWidgets('toggles password visibility', (tester) async {
      await tester.pumpWidget(createWidgetUnderTest());
      await tester.pumpAndSettle();

      final passwordField = find.widgetWithText(TextFormField, 'Password');
      final visibilityToggle = find.byIcon(Icons.visibility_off);

      // Initially password should be obscured
      expect(tester.widget<TextFormField>(passwordField).obscureText, isTrue);

      // Tap visibility toggle
      await tester.tap(visibilityToggle);
      await tester.pumpAndSettle();

      // Password should now be visible
      expect(tester.widget<TextFormField>(passwordField).obscureText, isFalse);
      expect(find.byIcon(Icons.visibility), findsOneWidget);
    });

    testWidgets('submits login form with valid credentials', (tester) async {
      // Mock successful login
      when(mockAuthRepository.login(any, any)).thenAnswer(
        (_) async => const Right(User(
          id: '1',
          email: 'test@example.com',
          firstName: 'John',
          lastName: 'Doe',
          role: 'passenger',
        )),
      );

      await tester.pumpWidget(createWidgetUnderTest());
      await tester.pumpAndSettle();

      // Enter valid credentials
      await tester.enterText(
        find.widgetWithText(TextFormField, 'Email'),
        'test@example.com',
      );
      await tester.enterText(
        find.widgetWithText(TextFormField, 'Password'),
        'password123',
      );

      // Submit form
      await tester.tap(find.text('Sign In'));
      await tester.pumpAndSettle();

      // Verify repository method was called
      verify(mockAuthRepository.login('test@example.com', 'password123')).called(1);
    });

    testWidgets('shows loading state during login', (tester) async {
      // Mock delayed login response
      when(mockAuthRepository.login(any, any)).thenAnswer(
        (_) async {
          await Future.delayed(const Duration(seconds: 1));
          return const Right(User(
            id: '1',
            email: 'test@example.com',
            firstName: 'John',
            lastName: 'Doe',
            role: 'passenger',
          ));
        },
      );

      await tester.pumpWidget(createWidgetUnderTest());
      await tester.pumpAndSettle();

      // Enter credentials and submit
      await tester.enterText(
        find.widgetWithText(TextFormField, 'Email'),
        'test@example.com',
      );
      await tester.enterText(
        find.widgetWithText(TextFormField, 'Password'),
        'password123',
      );
      await tester.tap(find.text('Sign In'));
      await tester.pump();

      // Should show loading indicator
      expect(find.byType(CircularProgressIndicator), findsOneWidget);
      expect(find.text('Signing In...'), findsOneWidget);
    });

    testWidgets('displays error message on login failure', (tester) async {
      // Mock login failure
      when(mockAuthRepository.login(any, any)).thenAnswer(
        (_) async => const Left(ServerFailure('Invalid credentials')),
      );

      await tester.pumpWidget(createWidgetUnderTest());
      await tester.pumpAndSettle();

      // Enter credentials and submit
      await tester.enterText(
        find.widgetWithText(TextFormField, 'Email'),
        'test@example.com',
      );
      await tester.enterText(
        find.widgetWithText(TextFormField, 'Password'),
        'wrongpassword',
      );
      await tester.tap(find.text('Sign In'));
      await tester.pumpAndSettle();

      // Should show error message
      expect(find.text('Invalid credentials'), findsOneWidget);
    });

    testWidgets('navigates to register screen when sign up is tapped', (tester) async {
      await tester.pumpWidget(createWidgetUnderTest());
      await tester.pumpAndSettle();

      await tester.tap(find.text('Sign Up'));
      await tester.pumpAndSettle();

      expect(find.text('Register Screen'), findsOneWidget);
    });

    testWidgets('navigates to forgot password screen', (tester) async {
      await tester.pumpWidget(createWidgetUnderTest());
      await tester.pumpAndSettle();

      await tester.tap(find.text('Forgot Password?'));
      await tester.pumpAndSettle();

      expect(find.text('Forgot Password Screen'), findsOneWidget);
    });

    testWidgets('shows biometric login option when available', (tester) async {
      // Mock biometric availability
      when(mockLocalAuth.canCheckBiometrics).thenAnswer((_) async => true);
      when(mockLocalAuth.isDeviceSupported()).thenAnswer((_) async => true);
      when(mockLocalAuth.getAvailableBiometrics()).thenAnswer(
        (_) async => [BiometricType.fingerprint],
      );

      await tester.pumpWidget(createWidgetUnderTest());
      await tester.pumpAndSettle();

      expect(find.byIcon(Icons.fingerprint), findsOneWidget);
      expect(find.text('Use Fingerprint'), findsOneWidget);
    });

    testWidgets('performs biometric authentication', (tester) async {
      // Mock biometric setup
      when(mockLocalAuth.canCheckBiometrics).thenAnswer((_) async => true);
      when(mockLocalAuth.isDeviceSupported()).thenAnswer((_) async => true);
      when(mockLocalAuth.getAvailableBiometrics()).thenAnswer(
        (_) async => [BiometricType.fingerprint],
      );
      when(mockLocalAuth.authenticate(
        localizedReason: anyNamed('localizedReason'),
        options: anyNamed('options'),
      )).thenAnswer((_) async => true);

      // Mock successful biometric login
      when(mockAuthRepository.loginWithBiometric()).thenAnswer(
        (_) async => const Right(User(
          id: '1',
          email: 'test@example.com',
          firstName: 'John',
          lastName: 'Doe',
          role: 'passenger',
        )),
      );

      await tester.pumpWidget(createWidgetUnderTest());
      await tester.pumpAndSettle();

      await tester.tap(find.byIcon(Icons.fingerprint));
      await tester.pumpAndSettle();

      verify(mockLocalAuth.authenticate(
        localizedReason: anyNamed('localizedReason'),
        options: anyNamed('options'),
      )).called(1);
    });

    testWidgets('remembers login preference', (tester) async {
      await tester.pumpWidget(createWidgetUnderTest());
      await tester.pumpAndSettle();

      // Find and tap remember me checkbox
      final rememberMeCheckbox = find.byType(Checkbox);
      await tester.tap(rememberMeCheckbox);
      await tester.pumpAndSettle();

      // Checkbox should be checked
      expect(tester.widget<Checkbox>(rememberMeCheckbox).value, isTrue);
    });

    testWidgets('handles network connectivity issues', (tester) async {
      // Mock network failure
      when(mockAuthRepository.login(any, any)).thenAnswer(
        (_) async => const Left(NetworkFailure('No internet connection')),
      );

      await tester.pumpWidget(createWidgetUnderTest());
      await tester.pumpAndSettle();

      // Enter credentials and submit
      await tester.enterText(
        find.widgetWithText(TextFormField, 'Email'),
        'test@example.com',
      );
      await tester.enterText(
        find.widgetWithText(TextFormField, 'Password'),
        'password123',
      );
      await tester.tap(find.text('Sign In'));
      await tester.pumpAndSettle();

      // Should show network error
      expect(find.text('No internet connection'), findsOneWidget);
      expect(find.text('Retry'), findsOneWidget);
    });

    testWidgets('auto-fills saved credentials', (tester) async {
      // Mock saved credentials
      when(mockPrefs.getString('saved_email')).thenReturn('saved@example.com');
      when(mockPrefs.getBool('remember_login')).thenReturn(true);

      await tester.pumpWidget(createWidgetUnderTest());
      await tester.pumpAndSettle();

      // Email field should be pre-filled
      final emailField = find.widgetWithText(TextFormField, 'Email');
      expect(tester.widget<TextFormField>(emailField).controller?.text, 
             equals('saved@example.com'));
    });

    testWidgets('clears form on logout', (tester) async {
      await tester.pumpWidget(createWidgetUnderTest());
      await tester.pumpAndSettle();

      // Enter some text
      await tester.enterText(
        find.widgetWithText(TextFormField, 'Email'),
        'test@example.com',
      );
      await tester.enterText(
        find.widgetWithText(TextFormField, 'Password'),
        'password123',
      );

      // Simulate logout event (this would typically come from app state)
      authBloc.add(const LogoutRequested());
      await tester.pumpAndSettle();

      // Fields should be cleared
      final emailField = find.widgetWithText(TextFormField, 'Email');
      final passwordField = find.widgetWithText(TextFormField, 'Password');
      
      expect(tester.widget<TextFormField>(emailField).controller?.text, isEmpty);
      expect(tester.widget<TextFormField>(passwordField).controller?.text, isEmpty);
    });
  });
}
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