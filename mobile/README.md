# Pafar Mobile App

A Flutter mobile application for the Pafar ride booking platform, built with clean architecture principles and modern Flutter development practices.

## Architecture

This app follows Clean Architecture principles with the following structure:

```
lib/
├── app/                    # App configuration and routing
├── core/                   # Core utilities and shared functionality
│   ├── bloc/              # Base BLoC classes
│   ├── constants/         # App constants
│   ├── di/                # Dependency injection setup
│   ├── error/             # Error handling and failures
│   ├── network/           # HTTP client and API configuration
│   ├── storage/           # Local storage abstractions
│   └── utils/             # Utility classes and functions
├── features/              # Feature modules (Clean Architecture)
│   └── auth/              # Authentication feature example
│       ├── data/          # Data sources and repositories implementation
│       ├── domain/        # Business logic and entities
│       └── presentation/  # UI and BLoC
└── shared/                # Shared UI components and themes
    ├── theme/             # App theming
    └── widgets/           # Reusable widgets
```

## Key Features

### 🏗️ Clean Architecture
- **Domain Layer**: Business logic, entities, and repository interfaces
- **Data Layer**: Repository implementations, data sources, and models
- **Presentation Layer**: UI components and state management

### 🎯 State Management
- **BLoC Pattern**: Using flutter_bloc for predictable state management
- **Base Classes**: Common BLoC functionality with logging and error handling

### 🌐 Networking
- **Dio HTTP Client**: Configured with interceptors for authentication and logging
- **Automatic Token Refresh**: Handles JWT token refresh automatically
- **Error Handling**: Comprehensive error handling with custom exceptions

### 💾 Local Storage
- **SharedPreferences**: For simple key-value storage
- **Hive**: For complex object storage and offline capabilities
- **Abstraction Layer**: Clean interfaces for storage operations

### 🎨 UI/UX
- **Material Design 3**: Modern Material Design components
- **Custom Theme**: Consistent theming across light and dark modes
- **Reusable Widgets**: Custom buttons, text fields, and other components
- **Responsive Design**: Adaptive layouts for different screen sizes

### 🧪 Testing
- **Unit Tests**: Core business logic and utilities
- **Widget Tests**: UI component testing
- **Integration Tests**: Feature flow testing
- **Mocking**: Using Mockito for test doubles

### 🔧 Development Tools
- **Dependency Injection**: GetIt for service location
- **Code Generation**: For JSON serialization and routing
- **Linting**: Flutter lints for code quality
- **Hot Reload**: Fast development iteration

## Getting Started

### Prerequisites
- Flutter SDK (>=3.10.0)
- Dart SDK (>=3.0.0)
- Android Studio / VS Code
- iOS development tools (for iOS builds)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd mobile
   ```

2. **Install dependencies**
   ```bash
   flutter pub get
   ```

3. **Generate code**
   ```bash
   flutter packages pub run build_runner build
   ```

4. **Run the app**
   ```bash
   flutter run
   ```

### Configuration

1. **Environment Variables**
   - Update `lib/core/constants/app_constants.dart` with your API endpoints
   - Configure Firebase settings for push notifications

2. **API Configuration**
   - Set your backend API URL in `AppConstants.baseUrl`
   - Configure WebSocket URL in `AppConstants.wsUrl`

## Project Structure Details

### Core Module

#### Dependency Injection (`core/di/`)
```dart
// Register services
sl.registerLazySingleton<ApiClient>(() => ApiClient(sl()));
sl.registerLazySingleton<AuthRepository>(() => AuthRepositoryImpl(sl()));
```

#### Network Layer (`core/network/`)
- **ApiClient**: Configured Dio instance with interceptors
- **AuthInterceptor**: Automatic token attachment and refresh
- **Error Handling**: Converts HTTP errors to domain failures

#### Storage Layer (`core/storage/`)
- **LocalStorage**: SharedPreferences wrapper
- **HiveStorage**: Hive database wrapper for complex objects

#### Utilities (`core/utils/`)
- **Either**: Functional error handling
- **Validators**: Form validation utilities
- **DateUtils**: Date formatting and manipulation

### Features Module

Each feature follows Clean Architecture:

```
features/auth/
├── data/
│   ├── datasources/       # Remote and local data sources
│   ├── models/           # Data models with JSON serialization
│   └── repositories/     # Repository implementations
├── domain/
│   ├── entities/         # Business entities
│   ├── repositories/     # Repository interfaces
│   └── usecases/         # Business use cases
└── presentation/
    ├── bloc/             # BLoC state management
    ├── pages/            # Screen widgets
    └── widgets/          # Feature-specific widgets
```

### Shared Module

#### Theme (`shared/theme/`)
- **AppTheme**: Light and dark theme configurations
- **AppColors**: Semantic color definitions
- **AppTextStyles**: Typography styles

#### Widgets (`shared/widgets/`)
- **CustomButton**: Styled button with loading states
- **CustomTextField**: Form input with validation
- **LoadingWidget**: Loading indicators
- **ErrorWidget**: Error display components

## State Management

### BLoC Pattern
```dart
class AuthBloc extends BaseBloc<AuthEvent, AuthState> {
  AuthBloc(this._authRepository) : super(AuthInitial()) {
    on<LoginRequested>(_onLoginRequested);
    on<LogoutRequested>(_onLogoutRequested);
  }

  Future<void> _onLoginRequested(
    LoginRequested event,
    Emitter<AuthState> emit,
  ) async {
    emit(AuthLoading());
    
    final result = await _authRepository.login(
      email: event.email,
      password: event.password,
    );
    
    result.fold(
      (failure) => emit(AuthError(failure.message)),
      (user) => emit(AuthSuccess(user)),
    );
  }
}
```

### State Classes
```dart
abstract class AuthState extends BaseState {}

class AuthInitial extends AuthState {}
class AuthLoading extends AuthState {}
class AuthSuccess extends AuthState {
  final User user;
  AuthSuccess(this.user);
}
class AuthError extends AuthState {
  final String message;
  AuthError(this.message);
}
```

## Testing

### Running Tests
```bash
# Run all tests
flutter test

# Run specific test file
flutter test test/core/utils/validators_test.dart

# Run with coverage
flutter test --coverage
```

### Test Structure
- **Unit Tests**: `test/core/` - Test business logic and utilities
- **Widget Tests**: `test/shared/widgets/` - Test UI components
- **Integration Tests**: `test/features/` - Test feature flows

### Example Test
```dart
group('Validators', () {
  test('should return null for valid email', () {
    expect(Validators.email('test@example.com'), isNull);
  });

  test('should return error for invalid email', () {
    expect(Validators.email('invalid-email'), isNotNull);
  });
});
```

## Code Generation

### JSON Serialization
```dart
@JsonSerializable()
class UserModel {
  final String id;
  final String email;
  
  UserModel({required this.id, required this.email});
  
  factory UserModel.fromJson(Map<String, dynamic> json) => 
      _$UserModelFromJson(json);
  Map<String, dynamic> toJson() => _$UserModelToJson(this);
}
```

### Build Runner Commands
```bash
# Generate code once
flutter packages pub run build_runner build

# Watch for changes and regenerate
flutter packages pub run build_runner watch

# Clean generated files
flutter packages pub run build_runner clean
```

## Best Practices

### Error Handling
- Use `Either<Failure, Success>` for repository methods
- Convert exceptions to domain failures
- Provide user-friendly error messages

### State Management
- Keep BLoCs focused on single responsibilities
- Use events for user actions
- Emit loading states for async operations

### UI Development
- Use semantic colors from the theme
- Implement proper loading and error states
- Follow Material Design guidelines

### Testing
- Write tests for all business logic
- Mock external dependencies
- Test error scenarios

## Contributing

1. Follow the established architecture patterns
2. Write tests for new features
3. Use the provided linting rules
4. Update documentation for significant changes

## Dependencies

### Core Dependencies
- `flutter_bloc`: State management
- `get_it`: Dependency injection
- `dio`: HTTP client
- `hive`: Local database
- `go_router`: Navigation
- `equatable`: Value equality

### Development Dependencies
- `build_runner`: Code generation
- `mockito`: Mocking for tests
- `flutter_test`: Testing framework
- `bloc_test`: BLoC testing utilities

## License

This project is part of the Pafar ride booking platform.