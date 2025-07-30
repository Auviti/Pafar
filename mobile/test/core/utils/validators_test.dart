import 'package:flutter_test/flutter_test.dart';
import 'package:pafar_mobile/core/utils/validators.dart';

void main() {
  group('Validators', () {
    group('email', () {
      test('should return null for valid email', () {
        expect(Validators.email('test@example.com'), isNull);
        expect(Validators.email('user.name@domain.co.uk'), isNull);
        expect(Validators.email('test123@test-domain.com'), isNull);
      });

      test('should return error for invalid email', () {
        expect(Validators.email('invalid-email'), isNotNull);
        expect(Validators.email('test@'), isNotNull);
        expect(Validators.email('@domain.com'), isNotNull);
        expect(Validators.email('test.domain.com'), isNotNull);
      });

      test('should return error for empty email', () {
        expect(Validators.email(''), isNotNull);
        expect(Validators.email(null), isNotNull);
      });
    });

    group('password', () {
      test('should return null for valid password', () {
        expect(Validators.password('Password123'), isNull);
        expect(Validators.password('MySecure1Pass'), isNull);
      });

      test('should return error for short password', () {
        expect(Validators.password('Pass1'), isNotNull);
        expect(Validators.password('1234567'), isNotNull);
      });

      test('should return error for password without uppercase', () {
        expect(Validators.password('password123'), isNotNull);
      });

      test('should return error for password without lowercase', () {
        expect(Validators.password('PASSWORD123'), isNotNull);
      });

      test('should return error for password without number', () {
        expect(Validators.password('Password'), isNotNull);
      });

      test('should return error for empty password', () {
        expect(Validators.password(''), isNotNull);
        expect(Validators.password(null), isNotNull);
      });
    });

    group('confirmPassword', () {
      test('should return null when passwords match', () {
        expect(Validators.confirmPassword('Password123', 'Password123'), isNull);
      });

      test('should return error when passwords do not match', () {
        expect(Validators.confirmPassword('Password123', 'Different123'), isNotNull);
      });

      test('should return error for empty confirmation', () {
        expect(Validators.confirmPassword('', 'Password123'), isNotNull);
        expect(Validators.confirmPassword(null, 'Password123'), isNotNull);
      });
    });

    group('phone', () {
      test('should return null for valid phone numbers', () {
        expect(Validators.phone('1234567890'), isNull);
        expect(Validators.phone('+1 (555) 123-4567'), isNull);
        expect(Validators.phone('555.123.4567'), isNull);
      });

      test('should return error for short phone numbers', () {
        expect(Validators.phone('123456789'), isNotNull);
        expect(Validators.phone('12345'), isNotNull);
      });

      test('should return error for empty phone', () {
        expect(Validators.phone(''), isNotNull);
        expect(Validators.phone(null), isNotNull);
      });
    });

    group('required', () {
      test('should return null for non-empty values', () {
        expect(Validators.required('test'), isNull);
        expect(Validators.required('  test  '), isNull);
      });

      test('should return error for empty values', () {
        expect(Validators.required(''), isNotNull);
        expect(Validators.required('   '), isNotNull);
        expect(Validators.required(null), isNotNull);
      });

      test('should use custom field name in error message', () {
        final error = Validators.required('', 'Username');
        expect(error, contains('Username'));
      });
    });

    group('minLength', () {
      test('should return null for values meeting minimum length', () {
        expect(Validators.minLength('test', 4), isNull);
        expect(Validators.minLength('testing', 4), isNull);
      });

      test('should return error for values below minimum length', () {
        expect(Validators.minLength('abc', 4), isNotNull);
        expect(Validators.minLength('', 1), isNotNull);
      });

      test('should return error for null values', () {
        expect(Validators.minLength(null, 4), isNotNull);
      });
    });

    group('maxLength', () {
      test('should return null for values within maximum length', () {
        expect(Validators.maxLength('test', 10), isNull);
        expect(Validators.maxLength('', 10), isNull);
        expect(Validators.maxLength(null, 10), isNull);
      });

      test('should return error for values exceeding maximum length', () {
        expect(Validators.maxLength('this is too long', 10), isNotNull);
      });
    });

    group('numeric', () {
      test('should return null for valid numbers', () {
        expect(Validators.numeric('123'), isNull);
        expect(Validators.numeric('123.45'), isNull);
        expect(Validators.numeric('-123'), isNull);
        expect(Validators.numeric('0'), isNull);
      });

      test('should return error for non-numeric values', () {
        expect(Validators.numeric('abc'), isNotNull);
        expect(Validators.numeric('12a3'), isNotNull);
        expect(Validators.numeric(''), isNotNull);
        expect(Validators.numeric(null), isNotNull);
      });
    });

    group('positiveNumber', () {
      test('should return null for positive numbers', () {
        expect(Validators.positiveNumber('123'), isNull);
        expect(Validators.positiveNumber('123.45'), isNull);
        expect(Validators.positiveNumber('0.1'), isNull);
      });

      test('should return error for zero or negative numbers', () {
        expect(Validators.positiveNumber('0'), isNotNull);
        expect(Validators.positiveNumber('-123'), isNotNull);
        expect(Validators.positiveNumber('-0.1'), isNotNull);
      });

      test('should return error for non-numeric values', () {
        expect(Validators.positiveNumber('abc'), isNotNull);
        expect(Validators.positiveNumber(''), isNotNull);
        expect(Validators.positiveNumber(null), isNotNull);
      });
    });

    group('combine', () {
      test('should return null when all validators pass', () {
        final result = Validators.combine([
          () => Validators.required('test'),
          () => Validators.minLength('test', 3),
          () => Validators.maxLength('test', 10),
        ]);
        expect(result, isNull);
      });

      test('should return first error when validators fail', () {
        final result = Validators.combine([
          () => Validators.required(''),
          () => Validators.minLength('', 3),
        ]);
        expect(result, isNotNull);
        expect(result, contains('required'));
      });
    });
  });
}