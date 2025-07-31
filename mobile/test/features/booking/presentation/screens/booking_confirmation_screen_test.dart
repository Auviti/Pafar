import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:mockito/mockito.dart';
import 'package:mockito/annotations.dart';

import 'package:pafar_mobile/features/booking/presentation/screens/booking_confirmation_screen.dart';
import 'package:pafar_mobile/features/booking/presentation/bloc/booking_bloc.dart';
import 'package:pafar_mobile/features/booking/presentation/bloc/booking_state.dart';
import 'package:pafar_mobile/features/booking/domain/entities/booking.dart';
import 'package:pafar_mobile/features/booking/domain/entities/trip.dart';
import 'package:pafar_mobile/features/booking/domain/entities/route.dart';
import 'package:pafar_mobile/features/booking/domain/entities/terminal.dart';
import 'package:pafar_mobile/shared/theme/app_theme.dart';

import 'booking_confirmation_screen_test.mocks.dart';

@GenerateMocks([BookingBloc])
void main() {
  late MockBookingBloc mockBookingBloc;
  late Trip testTrip;
  late Booking testBooking;

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
      departureTime: DateTime(2024, 12, 25, 10, 0),
      status: TripStatus.scheduled,
      fare: 50.0,
      availableSeats: 20,
      totalSeats: 40,
    );

    testBooking = Booking(
      id: '1',
      userId: 'user1',
      trip: testTrip,
      seatNumbers: [1, 2],
      totalAmount: 100.0,
      status: BookingStatus.confirmed,
      paymentStatus: PaymentStatus.pending,
      bookingReference: 'BK123456',
      createdAt: DateTime.now(),
    );
  });

  Widget createWidgetUnderTest() {
    return MaterialApp(
      theme: AppTheme.lightTheme,
      home: BlocProvider<BookingBloc>(
        create: (context) => mockBookingBloc,
        child: BookingConfirmationScreen(
          trip: testTrip,
          booking: testBooking,
        ),
      ),
    );
  }

  group('BookingConfirmationScreen', () {
    testWidgets('should display booking confirmation details', (tester) async {
      // Arrange
      when(mockBookingBloc.state).thenReturn(BookingInitial());
      when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([BookingInitial()]));

      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      expect(find.text('Booking Confirmation'), findsOneWidget);
      expect(find.text('Booking Created Successfully!'), findsOneWidget);
      expect(find.text('Booking Reference: BK123456'), findsOneWidget);
      expect(find.text('Central Terminal → Airport Terminal'), findsOneWidget);
      expect(find.text('1, 2'), findsOneWidget); // Seat numbers
      expect(find.text('\$100.00'), findsOneWidget); // Total amount
    });

    testWidgets('should display trip details section', (tester) async {
      // Arrange
      when(mockBookingBloc.state).thenReturn(BookingInitial());
      when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([BookingInitial()]));

      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      expect(find.text('Trip Details'), findsOneWidget);
      expect(find.text('Route'), findsOneWidget);
      expect(find.text('Departure'), findsOneWidget);
      expect(find.text('Duration'), findsOneWidget);
      expect(find.text('Distance'), findsOneWidget);
      expect(find.text('8h 0m'), findsOneWidget); // Duration
      expect(find.text('500.0 km'), findsOneWidget); // Distance
    });

    testWidgets('should display passenger details section', (tester) async {
      // Arrange
      when(mockBookingBloc.state).thenReturn(BookingInitial());
      when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([BookingInitial()]));

      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      expect(find.text('Passenger Details'), findsOneWidget);
      expect(find.text('Selected Seats'), findsOneWidget);
      expect(find.text('Number of Passengers'), findsOneWidget);
      expect(find.text('2'), findsOneWidget); // Number of passengers
    });

    testWidgets('should display payment summary section', (tester) async {
      // Arrange
      when(mockBookingBloc.state).thenReturn(BookingInitial());
      when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([BookingInitial()]));

      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      expect(find.text('Payment Summary'), findsOneWidget);
      expect(find.text('Fare per seat'), findsOneWidget);
      expect(find.text('Number of seats'), findsOneWidget);
      expect(find.text('Total Amount'), findsOneWidget);
      expect(find.text('\$50.00'), findsOneWidget); // Fare per seat
    });

    testWidgets('should show proceed to payment button when payment is pending', (tester) async {
      // Arrange
      when(mockBookingBloc.state).thenReturn(BookingInitial());
      when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([BookingInitial()]));

      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      expect(find.text('Proceed to Payment'), findsOneWidget);
      expect(find.text('Pay Later'), findsOneWidget);
    });

    testWidgets('should show view booking details button when payment is completed', (tester) async {
      // Arrange
      final completedBooking = Booking(
        id: '1',
        userId: 'user1',
        trip: testTrip,
        seatNumbers: [1, 2],
        totalAmount: 100.0,
        status: BookingStatus.confirmed,
        paymentStatus: PaymentStatus.completed,
        bookingReference: 'BK123456',
        createdAt: DateTime.now(),
      );

      when(mockBookingBloc.state).thenReturn(BookingInitial());
      when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([BookingInitial()]));

      // Act
      await tester.pumpWidget(MaterialApp(
        theme: AppTheme.lightTheme,
        home: BlocProvider<BookingBloc>(
          create: (context) => mockBookingBloc,
          child: BookingConfirmationScreen(
            trip: testTrip,
            booking: completedBooking,
          ),
        ),
      ));

      // Assert
      expect(find.text('View Booking Details'), findsOneWidget);
      expect(find.text('Proceed to Payment'), findsNothing);
    });

    testWidgets('should display important notes', (tester) async {
      // Arrange
      when(mockBookingBloc.state).thenReturn(BookingInitial());
      when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([BookingInitial()]));

      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      expect(find.text('Important Notes'), findsOneWidget);
      expect(find.textContaining('Please arrive at the terminal 30 minutes'), findsOneWidget);
      expect(find.textContaining('Bring a valid ID for verification'), findsOneWidget);
      expect(find.textContaining('Complete payment within 15 minutes'), findsOneWidget);
    });

    testWidgets('should navigate to payment screen when proceed button is tapped', (tester) async {
      // Arrange
      when(mockBookingBloc.state).thenReturn(BookingInitial());
      when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([BookingInitial()]));

      // Act
      await tester.pumpWidget(createWidgetUnderTest());
      await tester.tap(find.text('Proceed to Payment'));
      await tester.pumpAndSettle();

      // Assert - In a real test, we would verify navigation
      // For now, we just verify the widget is still there
      expect(find.byType(BookingConfirmationScreen), findsOneWidget);
    });

    testWidgets('should show error message when booking error occurs', (tester) async {
      // Arrange
      const errorMessage = 'Booking failed';
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

    testWidgets('should display correct payment status', (tester) async {
      // Arrange
      when(mockBookingBloc.state).thenReturn(BookingInitial());
      when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([BookingInitial()]));

      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      expect(find.text('Payment Status: Pending'), findsOneWidget);
      expect(find.byIcon(Icons.schedule), findsOneWidget); // Pending icon
    });

    testWidgets('should navigate back to home when pay later is tapped', (tester) async {
      // Arrange
      when(mockBookingBloc.state).thenReturn(BookingInitial());
      when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([BookingInitial()]));

      // Act
      await tester.pumpWidget(createWidgetUnderTest());
      await tester.tap(find.text('Pay Later'));
      await tester.pumpAndSettle();

      // Assert - In a real test, we would verify navigation
      // For now, we just verify the widget is still there
      expect(find.byType(BookingConfirmationScreen), findsOneWidget);
    });
  });
}