import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/mockito.dart';
import 'package:mockito/annotations.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:hive/hive.dart';

import 'package:pafar_mobile/core/storage/local_storage.dart';

import 'local_storage_test.mocks.dart';

@GenerateMocks([SharedPreferences, Box])
void main() {
  group('LocalStorageImpl', () {
    late LocalStorageImpl localStorage;
    late MockSharedPreferences mockPrefs;
    late MockBox mockHiveBox;

    setUp(() {
      mockPrefs = MockSharedPreferences();
      mockHiveBox = MockBox();
      localStorage = LocalStorageImpl(mockPrefs, mockHiveBox);
    });

    group('String operations', () {
      test('should save string value', () async {
        // Arrange
        const key = 'test_key';
        const value = 'test_value';
        when(mockPrefs.setString(key, value))
            .thenAnswer((_) async => true);

        // Act
        await localStorage.saveString(key, value);

        // Assert
        verify(mockPrefs.setString(key, value)).called(1);
      });

      test('should get string value', () async {
        // Arrange
        const key = 'test_key';
        const value = 'test_value';
        when(mockPrefs.getString(key)).thenReturn(value);

        // Act
        final result = await localStorage.getString(key);

        // Assert
        expect(result, equals(value));
        verify(mockPrefs.getString(key)).called(1);
      });
    });

    group('Boolean operations', () {
      test('should save boolean value', () async {
        // Arrange
        const key = 'test_key';
        const value = true;
        when(mockPrefs.setBool(key, value))
            .thenAnswer((_) async => true);

        // Act
        await localStorage.saveBool(key, value);

        // Assert
        verify(mockPrefs.setBool(key, value)).called(1);
      });

      test('should get boolean value', () async {
        // Arrange
        const key = 'test_key';
        const value = true;
        when(mockPrefs.getBool(key)).thenReturn(value);

        // Act
        final result = await localStorage.getBool(key);

        // Assert
        expect(result, equals(value));
        verify(mockPrefs.getBool(key)).called(1);
      });
    });

    group('Integer operations', () {
      test('should save integer value', () async {
        // Arrange
        const key = 'test_key';
        const value = 42;
        when(mockPrefs.setInt(key, value))
            .thenAnswer((_) async => true);

        // Act
        await localStorage.saveInt(key, value);

        // Assert
        verify(mockPrefs.setInt(key, value)).called(1);
      });

      test('should get integer value', () async {
        // Arrange
        const key = 'test_key';
        const value = 42;
        when(mockPrefs.getInt(key)).thenReturn(value);

        // Act
        final result = await localStorage.getInt(key);

        // Assert
        expect(result, equals(value));
        verify(mockPrefs.getInt(key)).called(1);
      });
    });

    test('should remove value', () async {
      // Arrange
      const key = 'test_key';
      when(mockPrefs.remove(key)).thenAnswer((_) async => true);

      // Act
      await localStorage.remove(key);

      // Assert
      verify(mockPrefs.remove(key)).called(1);
    });

    test('should clear all values', () async {
      // Arrange
      when(mockPrefs.clear()).thenAnswer((_) async => true);
      when(mockHiveBox.clear()).thenAnswer((_) async => 0);

      // Act
      await localStorage.clear();

      // Assert
      verify(mockPrefs.clear()).called(1);
      verify(mockHiveBox.clear()).called(1);
    });
  });

  group('HiveStorageImpl', () {
    late HiveStorageImpl hiveStorage;
    late MockBox mockBox;

    setUp(() {
      mockBox = MockBox();
      hiveStorage = HiveStorageImpl(mockBox);
    });

    test('should save object', () async {
      // Arrange
      const key = 'test_key';
      const value = {'test': 'data'};
      when(mockBox.put(key, value)).thenAnswer((_) async => {});

      // Act
      await hiveStorage.saveObject(key, value);

      // Assert
      verify(mockBox.put(key, value)).called(1);
    });

    test('should get object', () async {
      // Arrange
      const key = 'test_key';
      const value = {'test': 'data'};
      when(mockBox.get(key)).thenReturn(value);

      // Act
      final result = await hiveStorage.getObject<Map<String, String>>(key);

      // Assert
      expect(result, equals(value));
      verify(mockBox.get(key)).called(1);
    });

    test('should remove object', () async {
      // Arrange
      const key = 'test_key';
      when(mockBox.delete(key)).thenAnswer((_) async => {});

      // Act
      await hiveStorage.removeObject(key);

      // Assert
      verify(mockBox.delete(key)).called(1);
    });

    test('should clear all objects', () async {
      // Arrange
      when(mockBox.clear()).thenAnswer((_) async => 0);

      // Act
      await hiveStorage.clearAll();

      // Assert
      verify(mockBox.clear()).called(1);
    });
  });
}