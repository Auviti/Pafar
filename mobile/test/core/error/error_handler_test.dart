import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/mockito.dart';
import 'package:mockito/annotations.dart';

import '../../../lib/core/error/error_handler.dart';

// Generate mocks
@GenerateMocks([])
class MockErrorCallback extends Mock {
  void call(ErrorEvent error);
}

void main() {
  group('GlobalErrorHandler', () {
    late GlobalErrorHandler errorHandler;
    late MockErrorCallback mockCallback;

    setUp(() {
      errorHandler = GlobalErrorHandler();
      mockCallback = MockErrorCallback();
    });

    tearDown(() {
      errorHandler.clearErrors();
    });

    group('Error Recording', () {
      test('should record API errors', () {
        errorHandler.handleApiError(
          NetworkException('Connection failed'),
          endpoint: '/api/test',
          method: 'GET',
          additionalContext: {'retry_count': 1},
        );

        final recentErrors = errorHandler.getRecentErrors(limit: 1);
        expect(recentErrors, hasLength(1));
        
        final error = recentErrors.first;
        expect(error.type, ErrorType.api);
        expect(error.message, contains('Connection failed'));
        expect(error.context?['endpoint'], '/api/test');
        expect(error.context?['method'], 'GET');
        expect(error.context?['retry_count'], 1);
      });

      test('should record business errors', () {
        errorHandler.handleBusinessError(
          'Booking not available',
          code: 'BOOKING_UNAVAILABLE',
          additionalContext: {'trip_id': '123'},
        );

        final recentErrors = errorHandler.getRecentErrors(limit: 1);
        expect(recentErrors, hasLength(1));
        
        final error = recentErrors.first;
        expect(error.type, ErrorType.business);
        expect(error.message, 'Booking not available');
        expect(error.context?['code'], 'BOOKING_UNAVAILABLE');
        expect(error.context?['trip_id'], '123');
      });

      test('should limit stored error events', () {
        final handler = GlobalErrorHandler();
        
        // Add more errors than the limit
        for (int i = 0; i < 150; i++) {
          handler.handleBusinessError('Error $i');
        }

        final recentErrors = handler.getRecentErrors();
        expect(recentErrors.length, lessThanOrEqualTo(100));
      });
    });

    group('Error Callbacks', () {
      test('should add and call error callbacks', () {
        errorHandler.addErrorCallback(mockCallback);

        errorHandler.handleBusinessError('Test error');

        verify(mockCallback(any)).called(1);
      });

      test('should remove error callbacks', () {
        errorHandler.addErrorCallback(mockCallback);
        errorHandler.removeErrorCallback(mockCallback);

        errorHandler.handleBusinessError('Test error');

        verifyNever(mockCallback(any));
      });

      test('should handle callback errors gracefully', () {
        final faultyCallback = MockErrorCallback();
        when(faultyCallback(any)).thenThrow(Exception('Callback error'));
        
        errorHandler.addErrorCallback(faultyCallback);

        // Should not throw
        expect(
          () => errorHandler.handleBusinessError('Test error'),
          returnsNormally,
        );
      });
    });

    group('User-Friendly Messages', () {
      test('should create user-friendly message for NetworkException', () {
        final error = NetworkException('Connection timeout');
        final message = errorHandler.createUserFriendlyMessage(error);
        
        expect(message, 'Unable to connect to the server. Please check your internet connection.');
      });

      test('should create user-friendly message for ValidationException', () {
        final error = ValidationException('Invalid email format');
        final message = errorHandler.createUserFriendlyMessage(error);
        
        expect(message, 'Please check your input and try again.');
      });

      test('should create user-friendly message for AuthenticationException', () {
        final error = AuthenticationException('Invalid credentials');
        final message = errorHandler.createUserFriendlyMessage(error);
        
        expect(message, 'Please log in to continue.');
      });

      test('should create user-friendly message for AuthorizationException', () {
        final error = AuthorizationException('Access denied');
        final message = errorHandler.createUserFriendlyMessage(error);
        
        expect(message, 'You don\'t have permission to perform this action.');
      });

      test('should create user-friendly message for ServerException', () {
        final error = ServerException('Internal server error');
        final message = errorHandler.createUserFriendlyMessage(error);
        
        expect(message, 'Server error. Please try again later.');
      });

      test('should create generic message for unknown errors', () {
        final error = Exception('Unknown error');
        final message = errorHandler.createUserFriendlyMessage(error);
        
        expect(message, 'An unexpected error occurred. Please try again.');
      });
    });

    group('Error Event Serialization', () {
      test('should serialize error event to JSON', () {
        final timestamp = DateTime.now();
        final event = ErrorEvent(
          type: ErrorType.api,
          message: 'Test error',
          stackTrace: 'Stack trace here',
          timestamp: timestamp,
          context: {'key': 'value'},
        );

        final json = event.toJson();

        expect(json['type'], 'ErrorType.api');
        expect(json['message'], 'Test error');
        expect(json['stackTrace'], 'Stack trace here');
        expect(json['timestamp'], timestamp.toIso8601String());
        expect(json['context'], {'key': 'value'});
      });
    });

    group('Custom Exceptions', () {
      test('NetworkException should format correctly', () {
        final exception = NetworkException('Connection failed', statusCode: 500);
        
        expect(exception.toString(), 'NetworkException: Connection failed');
        expect(exception.statusCode, 500);
      });

      test('ValidationException should include field errors', () {
        final fieldErrors = {'email': 'Invalid format', 'password': 'Too short'};
        final exception = ValidationException('Validation failed', fieldErrors: fieldErrors);
        
        expect(exception.toString(), 'ValidationException: Validation failed');
        expect(exception.fieldErrors, fieldErrors);
      });

      test('AuthenticationException should format correctly', () {
        final exception = AuthenticationException('Invalid token');
        
        expect(exception.toString(), 'AuthenticationException: Invalid token');
      });

      test('AuthorizationException should format correctly', () {
        final exception = AuthorizationException('Access denied');
        
        expect(exception.toString(), 'AuthorizationException: Access denied');
      });

      test('ServerException should include status code', () {
        final exception = ServerException('Internal error', statusCode: 500);
        
        expect(exception.toString(), 'ServerException: Internal error');
        expect(exception.statusCode, 500);
      });

      test('BusinessException should include error code', () {
        final exception = BusinessException('Business rule violated', code: 'BR001');
        
        expect(exception.toString(), 'BusinessException: Business rule violated');
        expect(exception.code, 'BR001');
      });
    });

    group('Error Retrieval', () {
      test('should get recent errors with limit', () {
        // Add multiple errors
        for (int i = 0; i < 10; i++) {
          errorHandler.handleBusinessError('Error $i');
        }

        final recentErrors = errorHandler.getRecentErrors(limit: 5);
        expect(recentErrors, hasLength(5));
        
        // Should be in reverse chronological order (most recent first)
        expect(recentErrors.first.message, 'Error 9');
        expect(recentErrors.last.message, 'Error 5');
      });

      test('should clear all errors', () {
        errorHandler.handleBusinessError('Test error');
        expect(errorHandler.getRecentErrors(), hasLength(1));

        errorHandler.clearErrors();
        expect(errorHandler.getRecentErrors(), isEmpty);
      });
    });
  });
}