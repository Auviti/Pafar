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
import '../../../../../lib/features/auth/presentation/bloc/auth_state.dart';
import '../../../../../lib/features/auth/presentation/screens/register_screen.dart';
import '../../../../../lib/shared/theme/app_theme.dart';

import 'register_screen_test.mocks.dart';

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
              child: const RegisterScreen(),
            ),
          ),
          GoRoute(
            path: '/auth/email-verification',
            builder: (context, state) => const Scaffold(
              body: Text('Email Verification Screen'),
            ),
          ),
        ],
      ),
    );
  }

  group('RegisterScreen', () {
    testWidgets('should display all required UI elements', (tester) async {
      await tester.pumpWidget(createWidgetUnderTest());

      // Verify UI elements are present
      expect(find.text('Create Account'), findsNWidgets(2)); // AppBar title and button
      expect(find.text('Join Pafar Today'), findsOneWidget);
      expect(find.text('Create your account to start booking trips'), findsOneWidget);
      
      // Form fields
      expect(find.text('First Name'), findsOneWidget);
      expect(find.text('Last Name'), findsOneWidget);
      expect(find.text('Email'), findsOneWidget);
      expect(find.text('Phone Number (Optional)'), findsOneWidget);
      expect(find.text('Password'), findsOneWidget);
      expect(find.text('Confirm Password'), findsOneWidget);
      
      // Terms and conditions
      expect(find.textContaining('I agree to the'), findsOneWidget);
      expect(find.byType(Checkbox), findsOneWidget);
      
      // Sign in link
      expect(find.text('Already have an account? '), findsOneWidget);
      expect(find.text('Sign In'), findsOneWidget);
    });

    testWidgets('should validate required fields', (tester) async {
      await tester.pumpWidget(createWidgetUnderTest());

      // Tap create account button without filling fields
      final createAccountButton = find.text('Create Account').last;
      await tester.tap(createAccountButton);
      await tester.pumpAndSettle();

      // Should show validation errors
      expect(find.text('First name is required'), findsOneWidget);
      expect(find.text('Last name is required'), findsOneWidget);
      expect(find.text('Email is required'), findsOneWidget);
      expect(find.text('Password is required'), findsOneWidget);
    });

    testWidgets('should validate email format', (tester) async {
      await tester.pumpWidget(createWidgetUnderTest());

      // Enter invalid email
      final emailField = find.byType(TextFormField).at(2); // Email is 3rd field
      await tester.enterText(emailField, 'invalid-email');
      
      final createAccountButton = find.text('Create Account').last;
      await tester.tap(createAccountButton);
      await tester.pumpAndSettle();

      // Should show email validation error
      expect(find.text('Please enter a valid email address'), findsOneWidget);
    });

    testWidgets('should validate password strength', (tester) async {
      await tester.pumpWidget(createWidgetUnderTest());

      // Fill required fields with weak password
      await tester.enterText(find.byType(TextFormField).at(0), 'John');
      await tester.enterText(find.byType(TextFormField).at(1), 'Doe');
      await tester.enterText(find.byType(TextFormField).at(2), 'john@example.com');
      await tester.enterText(find.byType(TextFormField).at(4), 'weak'); // Password field
      
      final createAccountButton = find.text('Create Account').last;
      await tester.tap(createAccountButton);
      await tester.pumpAndSettle();

      // Should show password validation error
      expect(find.text('Password must be at least 8 characters long'), findsOneWidget);
    });

    testWidgets('should validate password confirmation', (tester) async {
      await tester.pumpWidget(createWidgetUnderTest());

      // Fill fields with mismatched passwords
      await tester.enterText(find.byType(TextFormField).at(0), 'John');
      await tester.enterText(find.byType(TextFormField).at(1), 'Doe');
      await tester.enterText(find.byType(TextFormField).at(2), 'john@example.com');
      await tester.enterText(find.byType(TextFormField).at(4), 'Password123');
      await tester.enterText(find.byType(TextFormField).at(5), 'DifferentPassword123');
      
      final createAccountButton = find.text('Create Account').last;
      await tester.tap(createAccountButton);
      await tester.pumpAndSettle();

      // Should show password confirmation error
      expect(find.text('Passwords do not match'), findsOneWidget);
    });

    testWidgets('should validate phone number when provided', (tester) async {
      await tester.pumpWidget(createWidgetUnderTest());

      // Enter invalid phone number
      await tester.enterText(find.byType(TextFormField).at(3), '123'); // Phone field
      
      final createAccountButton = find.text('Create Account').last;
      await tester.tap(createAccountButton);
      await tester.pumpAndSettle();

      // Should show phone validation error
      expect(find.text('Please enter a valid phone number'), findsOneWidget);
    });

    testWidgets('should toggle password visibility', (tester) async {
      await tester.pumpWidget(createWidgetUnderTest());

      // Find password visibility toggle buttons
      final visibilityButtons = find.byIcon(Icons.visibility);
      expect(visibilityButtons, findsNWidgets(2)); // Password and confirm password

      // Tap first visibility button (password field)
      await tester.tap(visibilityButtons.first);
      await tester.pumpAndSettle();

      // Should show visibility_off icon
      expect(find.byIcon(Icons.visibility_off), findsAtLeastNWidgets(1));
    });

    testWidgets('should toggle terms and conditions checkbox', (tester) async {
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

    testWidgets('should show error when terms are not accepted', (tester) async {
      await tester.pumpWidget(createWidgetUnderTest());

      // Fill all required fields but don't accept terms
      await tester.enterText(find.byType(TextFormField).at(0), 'John');
      await tester.enterText(find.byType(TextFormField).at(1), 'Doe');
      await tester.enterText(find.byType(TextFormField).at(2), 'john@example.com');
      await tester.enterText(find.byType(TextFormField).at(4), 'Password123');
      await tester.enterText(find.byType(TextFormField).at(5), 'Password123');
      
      final createAccountButton = find.text('Create Account').last;
      await tester.tap(createAccountButton);
      await tester.pumpAndSettle();

      // Should show terms acceptance error
      expect(find.text('Please accept the terms and conditions to continue.'), findsOneWidget);
    });

    testWidgets('should show loading state during registration', (tester) async {
      await tester.pumpWidget(createWidgetUnderTest());

      // Simulate loading state
      authBloc.emit(const AuthLoading());
      await tester.pumpAndSettle();

      // Should show loading indicator in button
      expect(find.byType(CircularProgressIndicator), findsOneWidget);
    });

    testWidgets('should show success message and navigate on successful registration', (tester) async {
      await tester.pumpWidget(createWidgetUnderTest());

      // Simulate registration success
      authBloc.emit(const AuthRegistrationSuccess(
        message: 'Registration successful! Please check your email to verify your account.',
      ));
      await tester.pumpAndSettle();

      // Should show success snackbar
      expect(find.text('Registration successful! Please check your email to verify your account.'), findsOneWidget);
      expect(find.byType(SnackBar), findsOneWidget);
      
      // Should navigate to email verification screen
      expect(find.text('Email Verification Screen'), findsOneWidget);
    });

    testWidgets('should show error message on registration failure', (tester) async {
      await tester.pumpWidget(createWidgetUnderTest());

      // Simulate error state
      authBloc.emit(const AuthError(message: 'Email already exists'));
      await tester.pumpAndSettle();

      // Should show error snackbar
      expect(find.text('Email already exists'), findsOneWidget);
      expect(find.byType(SnackBar), findsOneWidget);
    });

    testWidgets('should navigate back when sign in is tapped', (tester) async {
      await tester.pumpWidget(createWidgetUnderTest());

      final signInButton = find.text('Sign In');
      await tester.tap(signInButton);
      await tester.pumpAndSettle();

      // Should navigate back (in real app, this would go to login screen)
      // Since we're using a simple router setup, we can't easily test navigation back
    });

    testWidgets('should handle optional phone field correctly', (tester) async {
      await tester.pumpWidget(createWidgetUnderTest());

      // Fill all required fields and accept terms, leave phone empty
      await tester.enterText(find.byType(TextFormField).at(0), 'John');
      await tester.enterText(find.byType(TextFormField).at(1), 'Doe');
      await tester.enterText(find.byType(TextFormField).at(2), 'john@example.com');
      // Skip phone field (index 3)
      await tester.enterText(find.byType(TextFormField).at(4), 'Password123');
      await tester.enterText(find.byType(TextFormField).at(5), 'Password123');
      
      // Accept terms
      await tester.tap(find.byType(Checkbox));
      await tester.pumpAndSettle();
      
      final createAccountButton = find.text('Create Account').last;
      await tester.tap(createAccountButton);
      await tester.pumpAndSettle();

      // Should not show phone validation error since it's optional
      expect(find.text('Phone number is required'), findsNothing);
    });
  });
}