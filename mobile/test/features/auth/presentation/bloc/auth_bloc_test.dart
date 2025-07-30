import 'package:bloc_test/bloc_test.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:local_auth/local_auth.dart';
import 'package:mockito/annotations.dart';
import 'package:mockito/mockito.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../../../lib/core/error/failures.dart';
import '../../../../lib/core/utils/either.dart';
import '../../../../lib/features/auth/domain/entities/user.dart';
import '../../../../lib/features/auth/domain/repositories/auth_repository.dart';
import '../../../../lib/features/auth/presentation/bloc/auth_bloc.dart';
import '../../../../lib/features/auth/presentation/bloc/auth_event.dart';
import '../../../../lib/features/auth/presentation/bloc/auth_state.dart';

import 'auth_bloc_test.mocks.dart';

@GenerateMocks([AuthRepository, LocalAuthentication, SharedPreferences])
void main() {
  late AuthBloc authBloc;
  late MockAuthRepository mockAuthRepository;
  late MockLocalAuthentication mockLocalAuth;
  late MockSharedPreferences mockPrefs;

  final testUser = User(
    id: '1',
    email: 'test@example.com',
    firstName: 'John',
    lastName: 'Doe',
    role: 'passenger',
    isVerified: true,
    isActive: true,
    createdAt: DateTime.parse('2023-01-01T00:00:00Z'),
    updatedAt: DateTime.parse('2023-01-01T00:00:00Z'),
  );

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

  group('AuthBloc', () {
    test('initial state is AuthInitial', () {
      expect(authBloc.state, equals(const AuthInitial()));
    });

    group('AuthLoginRequested', () {
      blocTest<AuthBloc, AuthState>(
        'emits [AuthLoading, AuthAuthenticated] when login succeeds',
        build: () {
          when(mockAuthRepository.login(
            email: anyNamed('email'),
            password: anyNamed('password'),
          )).thenAnswer((_) async => const Right(testUser));
          return authBloc;
        },
        act: (bloc) => bloc.add(const AuthLoginRequested(
          email: 'test@example.com',
          password: 'password123',
        )),
        expect: () => [
          const AuthLoading(),
          AuthAuthenticated(user: testUser),
        ],
      );

      blocTest<AuthBloc, AuthState>(
        'emits [AuthLoading, AuthError] when login fails',
        build: () {
          when(mockAuthRepository.login(
            email: anyNamed('email'),
            password: anyNamed('password'),
          )).thenAnswer((_) async => const Left(
            AuthenticationFailure(message: 'Invalid credentials'),
          ));
          return authBloc;
        },
        act: (bloc) => bloc.add(const AuthLoginRequested(
          email: 'test@example.com',
          password: 'wrongpassword',
        )),
        expect: () => [
          const AuthLoading(),
          const AuthError(message: 'Invalid credentials'),
        ],
      );
    });

    group('AuthRegisterRequested', () {
      blocTest<AuthBloc, AuthState>(
        'emits [AuthLoading, AuthRegistrationSuccess] when registration succeeds',
        build: () {
          when(mockAuthRepository.register(
            email: anyNamed('email'),
            password: anyNamed('password'),
            firstName: anyNamed('firstName'),
            lastName: anyNamed('lastName'),
            phone: anyNamed('phone'),
          )).thenAnswer((_) async => const Right(testUser));
          return authBloc;
        },
        act: (bloc) => bloc.add(const AuthRegisterRequested(
          email: 'test@example.com',
          password: 'password123',
          firstName: 'John',
          lastName: 'Doe',
        )),
        expect: () => [
          const AuthLoading(),
          const AuthRegistrationSuccess(
            message: 'Registration successful! Please check your email to verify your account.',
          ),
        ],
      );

      blocTest<AuthBloc, AuthState>(
        'emits [AuthLoading, AuthError] when registration fails',
        build: () {
          when(mockAuthRepository.register(
            email: anyNamed('email'),
            password: anyNamed('password'),
            firstName: anyNamed('firstName'),
            lastName: anyNamed('lastName'),
            phone: anyNamed('phone'),
          )).thenAnswer((_) async => const Left(
            ValidationFailure(message: 'Email already exists'),
          ));
          return authBloc;
        },
        act: (bloc) => bloc.add(const AuthRegisterRequested(
          email: 'existing@example.com',
          password: 'password123',
          firstName: 'John',
          lastName: 'Doe',
        )),
        expect: () => [
          const AuthLoading(),
          const AuthError(message: 'Email already exists'),
        ],
      );
    });

    group('AuthLogoutRequested', () {
      blocTest<AuthBloc, AuthState>(
        'emits [AuthLoading, AuthUnauthenticated] when logout succeeds',
        build: () {
          when(mockAuthRepository.logout())
              .thenAnswer((_) async => const Right(null));
          return authBloc;
        },
        act: (bloc) => bloc.add(const AuthLogoutRequested()),
        expect: () => [
          const AuthLoading(),
          const AuthUnauthenticated(),
        ],
      );
    });

    group('AuthForgotPasswordRequested', () {
      blocTest<AuthBloc, AuthState>(
        'emits [AuthLoading, AuthPasswordResetEmailSent] when forgot password succeeds',
        build: () {
          when(mockAuthRepository.forgotPassword(email: anyNamed('email')))
              .thenAnswer((_) async => const Right(null));
          return authBloc;
        },
        act: (bloc) => bloc.add(const AuthForgotPasswordRequested(
          email: 'test@example.com',
        )),
        expect: () => [
          const AuthLoading(),
          const AuthPasswordResetEmailSent(
            message: 'Password reset instructions have been sent to your email.',
          ),
        ],
      );
    });

    group('AuthCheckStatusRequested', () {
      blocTest<AuthBloc, AuthState>(
        'emits [AuthAuthenticated] when user is logged in',
        build: () {
          when(mockAuthRepository.isLoggedIn())
              .thenAnswer((_) async => true);
          when(mockAuthRepository.getCurrentUser())
              .thenAnswer((_) async => const Right(testUser));
          return authBloc;
        },
        act: (bloc) => bloc.add(const AuthCheckStatusRequested()),
        expect: () => [
          AuthAuthenticated(user: testUser),
        ],
      );

      blocTest<AuthBloc, AuthState>(
        'emits [AuthUnauthenticated] when user is not logged in',
        build: () {
          when(mockAuthRepository.isLoggedIn())
              .thenAnswer((_) async => false);
          return authBloc;
        },
        act: (bloc) => bloc.add(const AuthCheckStatusRequested()),
        expect: () => [
          const AuthUnauthenticated(),
        ],
      );
    });

    group('Biometric Authentication', () {
      blocTest<AuthBloc, AuthState>(
        'emits [AuthAuthenticated] when biometric login succeeds',
        build: () {
          when(mockLocalAuth.canCheckBiometrics)
              .thenAnswer((_) async => true);
          when(mockLocalAuth.authenticate(
            localizedReason: anyNamed('localizedReason'),
            options: anyNamed('options'),
          )).thenAnswer((_) async => true);
          when(mockAuthRepository.isLoggedIn())
              .thenAnswer((_) async => true);
          when(mockAuthRepository.getCurrentUser())
              .thenAnswer((_) async => const Right(testUser));
          return authBloc;
        },
        act: (bloc) => bloc.add(const AuthBiometricLoginRequested()),
        expect: () => [
          AuthAuthenticated(user: testUser, isBiometricEnabled: true),
        ],
      );

      blocTest<AuthBloc, AuthState>(
        'emits [AuthError] when biometric is not available',
        build: () {
          when(mockLocalAuth.canCheckBiometrics)
              .thenAnswer((_) async => false);
          return authBloc;
        },
        act: (bloc) => bloc.add(const AuthBiometricLoginRequested()),
        expect: () => [
          const AuthError(
            message: 'Biometric authentication is not available on this device.',
          ),
        ],
      );
    });
  });
}