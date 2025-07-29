import 'package:flutter_test/flutter_test.dart';
import 'package:bloc_test/bloc_test.dart';

import 'package:pafar_mobile/core/bloc/base_bloc.dart';

// Test implementation of BaseBloc
class TestEvent extends BaseEvent {
  final String data;
  
  const TestEvent(this.data);
  
  @override
  List<Object> get props => [data];
}

class TestState extends BaseState {
  final String value;
  
  const TestState(this.value);
  
  @override
  List<Object> get props => [value];
}

class TestBloc extends BaseBloc<TestEvent, TestState> {
  TestBloc() : super(const TestState('initial')) {
    on<TestEvent>((event, emit) {
      emit(TestState(event.data));
    });
  }
}

void main() {
  group('BaseBloc', () {
    late TestBloc testBloc;

    setUp(() {
      testBloc = TestBloc();
    });

    tearDown(() {
      testBloc.close();
    });

    test('initial state should be correct', () {
      expect(testBloc.state, equals(const TestState('initial')));
    });

    blocTest<TestBloc, TestState>(
      'should emit new state when event is added',
      build: () => testBloc,
      act: (bloc) => bloc.add(const TestEvent('test_data')),
      expect: () => [const TestState('test_data')],
    );

    blocTest<TestBloc, TestState>(
      'should emit multiple states for multiple events',
      build: () => testBloc,
      act: (bloc) {
        bloc.add(const TestEvent('first'));
        bloc.add(const TestEvent('second'));
      },
      expect: () => [
        const TestState('first'),
        const TestState('second'),
      ],
    );
  });

  group('BaseEvent', () {
    test('should support equality comparison', () {
      const event1 = TestEvent('test');
      const event2 = TestEvent('test');
      const event3 = TestEvent('different');

      expect(event1, equals(event2));
      expect(event1, isNot(equals(event3)));
    });
  });

  group('BaseState', () {
    test('should support equality comparison', () {
      const state1 = TestState('test');
      const state2 = TestState('test');
      const state3 = TestState('different');

      expect(state1, equals(state2));
      expect(state1, isNot(equals(state3)));
    });
  });
}