import 'package:flutter_test/flutter_test.dart';
import 'package:pafar_mobile/core/utils/either.dart';

void main() {
  group('Either', () {
    group('Left', () {
      const left = Left<String, int>('error');

      test('should be identified as left', () {
        expect(left.isLeft, isTrue);
        expect(left.isRight, isFalse);
      });

      test('should execute left function in fold', () {
        final result = left.fold(
          (error) => 'Error: $error',
          (value) => 'Value: $value',
        );
        expect(result, equals('Error: error'));
      });

      test('should return left unchanged when mapping right', () {
        final result = left.map((value) => value * 2);
        expect(result, isA<Left<String, int>>());
        expect((result as Left).value, equals('error'));
      });

      test('should map left value when mapping left', () {
        final result = left.mapLeft((error) => 'Mapped: $error');
        expect(result, isA<Left<String, int>>());
        expect((result as Left).value, equals('Mapped: error'));
      });

      test('should return default value in getOrElse', () {
        final result = left.getOrElse(() => 42);
        expect(result, equals(42));
      });

      test('should throw exception in getOrThrow', () {
        expect(() => left.getOrThrow(), throwsException);
      });

      test('should support equality', () {
        const left1 = Left<String, int>('error');
        const left2 = Left<String, int>('error');
        const left3 = Left<String, int>('different');

        expect(left1, equals(left2));
        expect(left1, isNot(equals(left3)));
      });
    });

    group('Right', () {
      const right = Right<String, int>(42);

      test('should be identified as right', () {
        expect(right.isRight, isTrue);
        expect(right.isLeft, isFalse);
      });

      test('should execute right function in fold', () {
        final result = right.fold(
          (error) => 'Error: $error',
          (value) => 'Value: $value',
        );
        expect(result, equals('Value: 42'));
      });

      test('should map right value when mapping right', () {
        final result = right.map((value) => value * 2);
        expect(result, isA<Right<String, int>>());
        expect((result as Right).value, equals(84));
      });

      test('should return right unchanged when mapping left', () {
        final result = right.mapLeft((error) => 'Mapped: $error');
        expect(result, isA<Right<String, int>>());
        expect((result as Right).value, equals(42));
      });

      test('should return right value in getOrElse', () {
        final result = right.getOrElse(() => 0);
        expect(result, equals(42));
      });

      test('should return right value in getOrThrow', () {
        final result = right.getOrThrow();
        expect(result, equals(42));
      });

      test('should support equality', () {
        const right1 = Right<String, int>(42);
        const right2 = Right<String, int>(42);
        const right3 = Right<String, int>(24);

        expect(right1, equals(right2));
        expect(right1, isNot(equals(right3)));
      });
    });
  });
}