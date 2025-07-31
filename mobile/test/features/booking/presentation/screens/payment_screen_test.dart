import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:mockito/mockito.dart';
import 'package:mockito/annotations.dart';

import 'package:pafar_mobile/features/booking/presentation/screens/payment_screen.dart';
import 'package:pafar_mobile/features/booking/presentation/bloc/booking_bloc.dart';
import 'package:pafar_mobile/features/booking/presentation/bloc/booking_state.dart';
import 'package:pafar_mobile/features/booking/presentation/bloc/booking_event.dart';
import 'package:pafar_mobile/features/booking/domain/entities/trip.dart';
import 'package:pafar_mobile/features/booking/domain/entities/route.dart';
import 'package:pafar_mobile/features/booking/domain/entities/terminal.dart';
import 'package:pafar_mobile/features/booking/domain/entities/booking.dart';
import 'package:pafar_mobile/shared/theme/app_theme.dart';

import 'payment_screen_test.mocks.dart';

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
      departureTime: DateTime.now().add(const Duration(hours: 2)),
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
        child: PaymentScreen(
          trip: testTrip,
          booking: testBooking,
        ),
      ),
    );
  }

  group('PaymentScreen', () {
    testWidgets('should display payment summary', (tester) async {
      // Arrange
      when(mockBookingBloc.state).thenReturn(BookingInitial());
      when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([BookingInitial()]));

      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      expect(find.text('Payment'), findsOneWidget);
      expect(find.text('Payment Summary'), findsOneWidget);
      expect(find.text('BK123456'), findsOneWidget);
      expect(find.text('New York → Los Angeles'), findsOneWidget);
      expect(find.text('1, 2'), findsOneWidget);
      expect(find.text('\$100.00'), findsOneWidget);
    });

    testWidgets('should display payment method options', (tester) async {
      // Arrange
      when(mockBookingBloc.state).thenReturn(BookingInitial());
      when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([BookingInitial()]));

      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      expect(find.text('Payment Method'), findsOneWidget);
      expect(find.text('Credit/Debit Card'), findsOneWidget);
      expect(find.text('Mobile Money'), findsOneWidget);
    });

    testWidgets('should show card form when card payment is selected', (tester) async {
      // Arrange
      when(mockBookingBloc.state).thenReturn(BookingInitial());
      when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([BookingInitial()]));

      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      expect(find.text('Card Details'), findsOneWidget);
      expect(find.text('Cardholder Name'), findsOneWidget);
      expect(find.text('Card Number'), findsOneWidget);
      expect(find.text('Expiry Date'), findsOneWidget);
      expect(find.text('CVV'), findsOneWidget);
    });

    testWidgets('should show mobile money form when mobile money is selected', (tester) async {
      // Arrange
      when(mockBookingBloc.state).thenReturn(BookingInitial());
      when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([BookingInitial()]));

      // Act
      await tester.pumpWidget(createWidgetUnderTest());
      
      // Select mobile money
      await tester.tap(find.text('Mobile Money'));
      await tester.pump();

      // Assert
      expect(find.text('Mobile Money'), findsNWidgets(2)); // Radio button and section title
      expect(find.text('Phone Number'), findsOneWidget);
      expect(find.text('You will receive a prompt on your phone to complete the payment.'), findsOneWidget);
    });

    testWidgets('should validate card form fields', (tester) async {
      // Arrange
      when(mockBookingBloc.state).thenReturn(BookingInitial());
      when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([BookingInitial()]));

      // Act
      await tester.pumpWidget(createWidgetUnderTest());
      
      // Try to submit without filling fields
      await tester.tap(find.text('Pay \$100.00'));
      await tester.pump();

      // Assert
      expect(find.text('Please enter cardholder name'), findsOneWidget);
      expect(find.text('Please enter a valid card number'), findsOneWidget);
      expect(find.text('Enter MM/YY'), findsOneWidget);
      expect(find.text('Enter CVV'), findsOneWidget);
    });

    testWidgets('should format card number input', (tester) async {
      // Arrange
      when(mockBookingBloc.state).thenReturn(BookingInitial());
      when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([BookingInitial()]));

      // Act
      await tester.pumpWidget(createWidgetUnderTest());
      
      // Enter card number
      await tester.enterText(find.byType(TextFormField).at(1), '4242424242424242');
      await tester.pump();

      // Assert
      final cardNumberField = tester.widget<TextFormField>(find.byType(TextFormField).at(1));
      expect(cardNumberField.controller?.text, '4242 4242 4242 4242');
    });

    testWidgets('should format expiry date input', (tester) async {
      // Arrange
      when(mockBookingBloc.state).thenReturn(BookingInitial());
      when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([BookingInitial()]));

      // Act
      await tester.pumpWidget(createWidgetUnderTest());
      
      // Enter expiry date
      await tester.enterText(find.byType(TextFormField).at(2), '1225');
      await tester.pump();

      // Assert
      final expiryField = tester.widget<TextFormField>(find.byType(TextFormField).at(2));
      expect(expiryField.controller?.text, '12/25');
    });

    testWidgets('should validate expired card', (tester) async {
      // Arrange
      when(mockBookingBloc.state).thenReturn(BookingInitial());
      when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([BookingInitial()]));

      // Act
      await tester.pumpWidget(createWidgetUnderTest());
      
      // Enter expired date
      await tester.enterText(find.byType(TextFormField).at(2), '01/20');
      await tester.tap(find.text('Pay \$100.00'));
      await tester.pump();

      // Assert
      expect(find.text('Card expired'), findsOneWidget);
    });

    testWidgets('should validate card number with Luhn algorithm', (tester) async {
      // Arrange
      when(mockBookingBloc.state).thenReturn(BookingInitial());
      when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([BookingInitial()]));

      // Act
      await tester.pumpWidget(createWidgetUnderTest());
      
      // Enter invalid card number
      await tester.enterText(find.byType(TextFormField).at(1), '1234567890123456');
      await tester.tap(find.text('Pay \$100.00'));
      await tester.pump();

      // Assert
      expect(find.text('Invalid card number'), findsOneWidget);
    });

    testWidgets('should show processing state when payment is being processed', (tester) async {
      // Arrange
      when(mockBookingBloc.state).thenReturn(PaymentProcessing('1'));
      when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([PaymentProcessing('1')]));

      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      expect(find.text('Processing your payment...'), findsOneWidget);
      expect(find.text('Please do not close this screen'), findsOneWidget);
      expect(find.byType(CircularProgressIndicator), findsOneWidget);
    });

    testWidgets('should process payment when form is valid', (tester) async {
      // Arrange
      when(mockBookingBloc.state).thenReturn(BookingInitial());
      when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([BookingInitial()]));

      // Act
      await tester.pumpWidget(createWidgetUnderTest());
      
      // Fill valid form data
      await tester.enterText(find.byType(TextFormField).at(0), 'John Doe');
      await tester.enterText(find.byType(TextFormField).at(1), '4242424242424242');
      await tester.enterText(find.byType(TextFormField).at(2), '12/25');
      await tester.enterText(find.byType(TextFormField).at(3), '123');
      
      await tester.tap(find.text('Pay \$100.00'));
      await tester.pump();

      // Assert
      verify(mockBookingBloc.add(argThat(isA<ProcessPayment>()))).called(1);
    });

    testWidgets('should show security notice', (tester) async {
      // Arrange
      when(mockBookingBloc.state).thenReturn(BookingInitial());
      when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([BookingInitial()]));

      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      expect(find.text('Your payment information is encrypted and secure'), findsOneWidget);
      expect(find.byIcon(Icons.security), findsOneWidget);
    });

    testWidgets('should show terms and conditions', (tester) async {
      // Arrange
      when(mockBookingBloc.state).thenReturn(BookingInitial());
      when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([BookingInitial()]));

      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      expect(find.text('By proceeding with payment, you agree to our Terms of Service and Privacy Policy.'), findsOneWidget);
    });

    testWidgets('should show save card checkbox', (tester) async {
      // Arrange
      when(mockBookingBloc.state).thenReturn(BookingInitial());
      when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([BookingInitial()]));

      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      expect(find.text('Save card for future payments'), findsOneWidget);
      expect(find.byType(Checkbox), findsOneWidget);
    });

    testWidgets('should toggle save card checkbox', (tester) async {
      // Arrange
      when(mockBookingBloc.state).thenReturn(BookingInitial());
      when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([BookingInitial()]));

      // Act
      await tester.pumpWidget(createWidgetUnderTest());
      
      // Tap checkbox
      await tester.tap(find.byType(Checkbox));
      await tester.pump();

      // Assert
      final checkbox = tester.widget<Checkbox>(find.byType(Checkbox));
      expect(checkbox.value, isTrue);
    });

    testWidgets('should show error message when payment fails', (tester) async {
      // Arrange
      const errorMessage = 'Payment failed';
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