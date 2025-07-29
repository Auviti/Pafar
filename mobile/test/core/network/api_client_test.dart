import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/mockito.dart';
import 'package:mockito/annotations.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:dio/dio.dart';

import 'package:pafar_mobile/core/network/api_client.dart';
import 'package:pafar_mobile/core/constants/app_constants.dart';

import 'api_client_test.mocks.dart';

@GenerateMocks([SharedPreferences])
void main() {
  group('ApiClient', () {
    late ApiClient apiClient;
    late MockSharedPreferences mockPrefs;

    setUp(() {
      mockPrefs = MockSharedPreferences();
      apiClient = ApiClient(mockPrefs);
    });

    test('should create Dio instance with correct base configuration', () {
      // Assert
      expect(apiClient.dio.options.baseUrl, equals(AppConstants.baseUrl));
      expect(apiClient.dio.options.connectTimeout?.inMilliseconds, 
             equals(AppConstants.connectionTimeout));
      expect(apiClient.dio.options.receiveTimeout?.inMilliseconds, 
             equals(AppConstants.receiveTimeout));
      expect(apiClient.dio.options.headers['Content-Type'], 
             equals('application/json'));
      expect(apiClient.dio.options.headers['Accept'], 
             equals('application/json'));
    });

    test('should add auth interceptor', () {
      // Assert
      expect(apiClient.dio.interceptors.length, greaterThan(0));
      expect(apiClient.dio.interceptors.any((i) => i is AuthInterceptor), 
             isTrue);
    });
  });

  group('AuthInterceptor', () {
    late AuthInterceptor authInterceptor;
    late MockSharedPreferences mockPrefs;
    late RequestOptions requestOptions;

    setUp(() {
      mockPrefs = MockSharedPreferences();
      authInterceptor = AuthInterceptor(mockPrefs);
      requestOptions = RequestOptions(path: '/test');
    });

    test('should add Authorization header when token exists', () {
      // Arrange
      const token = 'test_token';
      when(mockPrefs.getString(AppConstants.accessTokenKey))
          .thenReturn(token);

      // Act
      authInterceptor.onRequest(requestOptions, RequestInterceptorHandler());

      // Assert
      expect(requestOptions.headers['Authorization'], equals('Bearer $token'));
    });

    test('should not add Authorization header when token does not exist', () {
      // Arrange
      when(mockPrefs.getString(AppConstants.accessTokenKey))
          .thenReturn(null);

      // Act
      authInterceptor.onRequest(requestOptions, RequestInterceptorHandler());

      // Assert
      expect(requestOptions.headers.containsKey('Authorization'), isFalse);
    });
  });
}