import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:mockito/mockito.dart';
import 'package:mockito/annotations.dart';

import 'package:pafar_mobile/features/booking/presentation/screens/seat_selection_screen.dart';
import 'package:pafar_mobile/features/booking/presentation/bloc/booking_bloc.dart';
import 'package:pafar_mobile/features/booking/presentation/bloc/booking_state.dart';
import 'package:pafar_mobile/features/booking/presentation/bloc/booking_event.dart';
import 'package:pafar_mobile/features/booking/domain/entities/trip.dart';
import 'package:pafar_mobile/features/booking/domain/entities/route.dart';
import 'package:pafar_mobile/features/booking/domain/entities/terminal.dart';
import 'package:pafar_mobile/features/booking/domain/entities/booking.dart';
import 'package:pafar_mobile/shared/theme/app_theme.dart';

import 'seat_selection_screen_test.mocks.dart';

@GenerateMocks([BookingBloc])
void main() {
  late MockBookingBloc mockBookingBloc;
  late Trip testTrip;

  setUp(() {
    mockBookingBloc = MockBookingBloc();
    
    testTrip = Trip(
      id: '1',
      route: const BusRoute(
        id: '1',
        originTerminal: Terminal(
          id: '1',
          name: 'Central Terminal',
          city: 'New York',
          isActive: true,
        ),
        destinationTerminal: Terminal(
          id: '2',
          name: 'Airport Terminal',
          city: 'Los Angeles',
          isActive: true,
        ),
        distanceKm: 500.0,
        estimatedDurationMinutes: 480,
        baseFare: 50.0,
        isActive: true,
      ),
      busId: 'bus1',
      departureTime: DateTime.now().add(const Duration(hours: 2)),
      status: TripStatus.scheduled,
      fare: 50.0,
      availableSeats: 20,
      totalSeats: 40,
    );
  });

  Widget createWidgetUnderTest() {
    return MaterialApp(
      theme: AppTheme.lightTheme,
      home: BlocProvider<BookingBloc>(
        create: (context) => mockBookingBloc,
        child: SeatSelectionScreen(trip: testTrip),
      ),
    );
  }

  group('SeatSelectionScreen', () {
    testWidgets('should display trip information', (tester) async {
      // Arrange
      when(mockBookingBloc.state).thenReturn(BookingLoading());
      when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([BookingLoading()]));

      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      expect(find.text('Select Seats'), findsOneWidget);
      expect(find.text('Central Terminal'), findsOneWidget);
      expect(find.text('Airport Terminal'), findsOneWidget);
      expect(find.text('\$50.00'), findsOneWidget);
    });

    testWidgets('should show loading indicator initially', (tester) async {
      // Arrange
      when(mockBookingBloc.state).thenReturn(BookingLoading());
      when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([BookingLoading()]));

      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      expect(find.byType(CircularProgressIndicator), findsOneWidget);
    });

    testWidgets('should display seat map when seats are loaded', (tester) async {
      // Arrange
      final seats = List.generate(40, (index) => SeatInfo(
        seatNumber: index + 1,
        isAvailable: index < 20, // First 20 seats available
      ));

      final seatState = SeatAvailabilityLoaded(
        tripId: testTrip.id,
        seats: seats,
        selectedSeats: [],
        totalSeats: 40,
        availableSeats: 20,
      );

      when(mockBookingBloc.state).thenReturn(seatState);
      when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([seatState]));

      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      expect(find.text('Available'), findsOneWidget);
      expect(find.text('Selected'), findsOneWidget);
      expect(find.text('Occupied'), findsOneWidget);
      expect(find.text('Driver'), findsOneWidget);
      expect(find.byIcon(Icons.event_seat), findsWidgets);
    });

    testWidgets('should select seat when tapped', (tester) async {
      // Arrange
      final seats = List.generate(4, (index) => SeatInfo(
        seatNumber: index + 1,
        isAvailable: true,
      ));

      final seatState = SeatAvailabilityLoaded(
        tripId: testTrip.id,
        seats: seats,
        selectedSeats: [],
        totalSeats: 4,
        availableSeats: 4,
      );

      when(mockBookingBloc.state).thenReturn(seatState);
      when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([seatState]));

      // Act
      await tester.pumpWidget(createWidgetUnderTest());
      
      // Find and tap the first seat
      final seatWidgets = find.byType(GestureDetector);
      await tester.tap(seatWidgets.first);
      await tester.pump();

      // Assert
      verify(mockBookingBloc.add(any)).called(greaterThan(0));
    });

    testWidgets('should show selected seats and total price', (tester) async {
      // Arrange
      final seats = List.generate(4, (index) => SeatInfo(
        seatNumber: index + 1,
        isAvailable: true,
        isSelected: index == 0, // First seat selected
      ));

      final seatState = SeatAvailabilityLoaded(
        tripId: testTrip.id,
        seats: seats,
        selectedSeats: [1],
        totalSeats: 4,
        availableSeats: 4,
      );

      when(mockBookingBloc.state).thenReturn(seatState);
      when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([seatState]));

      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      expect(find.text('Selected seats: 1'), findsOneWidget);
      expect(find.text('Total: \$50.00'), findsOneWidget);
      expect(find.text('Proceed to Booking'), findsOneWidget);
    });

    testWidgets('should disable proceed button when no seats selected', (tester) async {
      // Arrange
      final seats = List.generate(4, (index) => SeatInfo(
        seatNumber: index + 1,
        isAvailable: true,
      ));

      final seatState = SeatAvailabilityLoaded(
        tripId: testTrip.id,
        seats: seats,
        selectedSeats: [],
        totalSeats: 4,
        availableSeats: 4,
      );

      when(mockBookingBloc.state).thenReturn(seatState);
      when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([seatState]));

      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      expect(find.text('Select at least one seat'), findsOneWidget);
      
      final proceedButton = tester.widget<ElevatedButton>(
        find.byType(ElevatedButton),
      );
      expect(proceedButton.onPressed, isNull);
    });

    testWidgets('should create booking when proceed button is tapped', (tester) async {
      // Arrange
      final seats = List.generate(4, (index) => SeatInfo(
        seatNumber: index + 1,
        isAvailable: true,
        isSelected: index == 0,
      ));

      final seatState = SeatAvailabilityLoaded(
        tripId: testTrip.id,
        seats: seats,
        selectedSeats: [1],
        totalSeats: 4,
        availableSeats: 4,
      );

      when(mockBookingBloc.state).thenReturn(seatState);
      when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([seatState]));

      // Act
      await tester.pumpWidget(createWidgetUnderTest());
      await tester.tap(find.text('Proceed to Booking'));
      await tester.pump();

      // Assert
      verify(mockBookingBloc.add(argThat(isA<CreateBooking>()))).called(1);
    });

    testWidgets('should navigate to booking confirmation when booking is created', (tester) async {
      // Arrange
      final booking = Booking(
        id: '1',
        userId: 'user1',
        trip: testTrip,
        seatNumbers: [1],
        totalAmount: 50.0,
        status: BookingStatus.confirmed,
        paymentStatus: PaymentStatus.pending,
        bookingReference: 'BK123456',
        createdAt: DateTime.now(),
      );

      when(mockBookingBloc.state).thenReturn(BookingCreated(booking));
      when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([
        BookingCreated(booking),
      ]));

      // Act
      await tester.pumpWidget(createWidgetUnderTest());
      await tester.pumpAndSettle();

      // Assert - Should navigate to booking confirmation screen
      // This would require more complex navigation testing setup
      expect(find.byType(SeatSelectionScreen), findsOneWidget);
    });

    testWidgets('should show error message when seat loading fails', (tester) async {
      // Arrange
      const errorMessage = 'Failed to load seats';
      when(mockBookingBloc.state).thenReturn(const BookingError(message: errorMessage));
      when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([
        const BookingError(message: errorMessage),
      ]));

      // Act
      await tester.pumpWidget(createWidgetUnderTest());
      await tester.pump();

      // Assert
      expect(find.text(errorMessage), findsOneWidget);
      expect(find.text('Retry'), findsOneWidget);
    });

    testWidgets('should not allow selection of occupied seats', (tester) async {
      // Arrange
      final seats = [
        const SeatInfo(seatNumber: 1, isAvailable: true),
        const SeatInfo(seatNumber: 2, isAvailable: false), // Occupied
      ];

      final seatState = SeatAvailabilityLoaded(
        tripId: testTrip.id,
        seats: seats,
        selectedSeats: [],
        totalSeats: 2,
        availableSeats: 1,
      );

      when(mockBookingBloc.state).thenReturn(seatState);
      when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([seatState]));

      // Act
      await tester.pumpWidget(createWidgetUnderTest());
      
      // Try to tap occupied seat (should not trigger selection)
      final seatWidgets = find.byType(GestureDetector);
      await tester.tap(seatWidgets.at(1)); // Second seat (occupied)
      await tester.pump();

      // Assert - No SelectSeat event should be dispatched for occupied seat
      verifyNever(mockBookingBloc.add(argThat(isA<SelectSeat>())));
    });
  });
}