import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:mockito/mockito.dart';
import 'package:mockito/annotations.dart';

import 'package:pafar_mobile/features/booking/presentation/screens/trip_search_screen.dart';
import 'package:pafar_mobile/features/booking/presentation/bloc/booking_bloc.dart';
import 'package:pafar_mobile/features/booking/presentation/bloc/booking_state.dart';
import 'package:pafar_mobile/features/booking/presentation/bloc/booking_event.dart';
import 'package:pafar_mobile/features/booking/domain/entities/terminal.dart';
import 'package:pafar_mobile/shared/theme/app_theme.dart';

import 'trip_search_screen_test.mocks.dart';

@GenerateMocks([BookingBloc])
void main() {
  late MockBookingBloc mockBookingBloc;

  setUp(() {
    mockBookingBloc = MockBookingBloc();
  });

  Widget createWidgetUnderTest() {
    return MaterialApp(
      theme: AppTheme.lightTheme,
      home: BlocProvider<BookingBloc>(
        create: (context) => mockBookingBloc,
        child: const TripSearchScreen(),
      ),
    );
  }

  group('TripSearchScreen', () {
    testWidgets('should display trip search form', (tester) async {
      // Arrange
      when(mockBookingBloc.state).thenReturn(BookingInitial());
      when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([BookingInitial()]));

      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      expect(find.text('Search Trips'), findsOneWidget);
      expect(find.text('From'), findsOneWidget);
      expect(find.text('To'), findsOneWidget);
      expect(find.text('Departure Date'), findsOneWidget);
      expect(find.text('Passengers'), findsOneWidget);
      expect(find.text('Search Trips'), findsNWidgets(2)); // AppBar title and button
    });

    testWidgets('should display terminals when loaded', (tester) async {
      // Arrange
      final terminals = [
        const Terminal(
          id: '1',
          name: 'Central Terminal',
          city: 'New York',
          isActive: true,
        ),
        const Terminal(
          id: '2',
          name: 'Airport Terminal',
          city: 'Los Angeles',
          isActive: true,
        ),
      ];

      when(mockBookingBloc.state).thenReturn(TerminalsLoaded(terminals));
      when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([
        BookingInitial(),
        TerminalsLoaded(terminals),
      ]));

      // Act
      await tester.pumpWidget(createWidgetUnderTest());
      await tester.pump();

      // Type in origin field to trigger dropdown
      await tester.enterText(find.byType(TextFormField).first, 'Central');
      await tester.pump();

      // Assert
      expect(find.text('Central Terminal'), findsOneWidget);
    });

    testWidgets('should validate form fields', (tester) async {
      // Arrange
      when(mockBookingBloc.state).thenReturn(BookingInitial());
      when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([BookingInitial()]));

      // Act
      await tester.pumpWidget(createWidgetUnderTest());
      
      // Try to submit without selecting terminals
      await tester.tap(find.text('Search Trips').last);
      await tester.pump();

      // Assert
      expect(find.text('Please select departure terminal'), findsOneWidget);
      expect(find.text('Please select destination terminal'), findsOneWidget);
    });

    testWidgets('should swap terminals when swap button is tapped', (tester) async {
      // Arrange
      final terminals = [
        const Terminal(
          id: '1',
          name: 'Central Terminal',
          city: 'New York',
          isActive: true,
        ),
        const Terminal(
          id: '2',
          name: 'Airport Terminal',
          city: 'Los Angeles',
          isActive: true,
        ),
      ];

      when(mockBookingBloc.state).thenReturn(TerminalsLoaded(terminals));
      when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([
        TerminalsLoaded(terminals),
      ]));

      // Act
      await tester.pumpWidget(createWidgetUnderTest());
      await tester.pump();

      // Select origin terminal
      await tester.enterText(find.byType(TextFormField).first, 'Central');
      await tester.pump();
      await tester.tap(find.text('Central Terminal'));
      await tester.pump();

      // Select destination terminal
      await tester.enterText(find.byType(TextFormField).at(1), 'Airport');
      await tester.pump();
      await tester.tap(find.text('Airport Terminal'));
      await tester.pump();

      // Tap swap button
      await tester.tap(find.byIcon(Icons.swap_vert));
      await tester.pump();

      // Assert - the text fields should have swapped values
      final originField = tester.widget<TextFormField>(find.byType(TextFormField).first);
      final destinationField = tester.widget<TextFormField>(find.byType(TextFormField).at(1));
      
      expect(originField.controller?.text, contains('Airport Terminal'));
      expect(destinationField.controller?.text, contains('Central Terminal'));
    });

    testWidgets('should show date picker when date field is tapped', (tester) async {
      // Arrange
      when(mockBookingBloc.state).thenReturn(BookingInitial());
      when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([BookingInitial()]));

      // Act
      await tester.pumpWidget(createWidgetUnderTest());
      await tester.tap(find.text('Departure Date'));
      await tester.pumpAndSettle();

      // Assert
      expect(find.byType(DatePickerDialog), findsOneWidget);
    });

    testWidgets('should validate passenger count', (tester) async {
      // Arrange
      when(mockBookingBloc.state).thenReturn(BookingInitial());
      when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([BookingInitial()]));

      // Act
      await tester.pumpWidget(createWidgetUnderTest());
      
      // Enter invalid passenger count
      final passengerField = find.byType(TextFormField).last;
      await tester.enterText(passengerField, '15');
      await tester.tap(find.text('Search Trips').last);
      await tester.pump();

      // Assert
      expect(find.text('Enter 1-10 passengers'), findsOneWidget);
    });

    testWidgets('should dispatch SearchTrips event when form is valid', (tester) async {
      // Arrange
      final terminals = [
        const Terminal(
          id: '1',
          name: 'Central Terminal',
          city: 'New York',
          isActive: true,
        ),
        const Terminal(
          id: '2',
          name: 'Airport Terminal',
          city: 'Los Angeles',
          isActive: true,
        ),
      ];

      when(mockBookingBloc.state).thenReturn(TerminalsLoaded(terminals));
      when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([
        TerminalsLoaded(terminals),
      ]));

      // Act
      await tester.pumpWidget(createWidgetUnderTest());
      await tester.pump();

      // Select terminals
      await tester.enterText(find.byType(TextFormField).first, 'Central');
      await tester.pump();
      await tester.tap(find.text('Central Terminal'));
      await tester.pump();

      await tester.enterText(find.byType(TextFormField).at(1), 'Airport');
      await tester.pump();
      await tester.tap(find.text('Airport Terminal'));
      await tester.pump();

      // Submit form
      await tester.tap(find.text('Search Trips').last);
      await tester.pump();

      // Assert
      verify(mockBookingBloc.add(any)).called(greaterThan(0));
    });

    testWidgets('should show loading indicator when searching', (tester) async {
      // Arrange
      when(mockBookingBloc.state).thenReturn(BookingLoading());
      when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([BookingLoading()]));

      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      expect(find.byType(CircularProgressIndicator), findsOneWidget);
    });

    testWidgets('should show error message when search fails', (tester) async {
      // Arrange
      const errorMessage = 'Failed to search trips';
      when(mockBookingBloc.state).thenReturn(const BookingError(message: errorMessage));
      when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([
        const BookingError(message: errorMessage),
      ]));

      // Act
      await tester.pumpWidget(createWidgetUnderTest());
      await tester.pump();

      // Assert
      expect(find.text(errorMessage), findsOneWidget);
    });
  });
}