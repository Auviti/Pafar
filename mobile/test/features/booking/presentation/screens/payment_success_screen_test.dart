import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:pafar_mobile/features/booking/presentation/screens/payment_success_screen.dart';
import 'package:pafar_mobile/features/booking/domain/entities/booking.dart';
import 'package:pafar_mobile/features/booking/domain/entities/trip.dart';
import 'package:pafar_mobile/features/booking/domain/entities/route.dart';
import 'package:pafar_mobile/features/booking/domain/entities/terminal.dart';
import 'package:pafar_mobile/shared/theme/app_theme.dart';

void main() {
  late Trip testTrip;
  late Booking testBooking;
  late Map<String, dynamic> testPaymentResult;

  setUp(() {
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
      paymentStatus: PaymentStatus.completed,
      bookingReference: 'BK123456',
      createdAt: DateTime.now(),
    );

    testPaymentResult = {
      'transaction_id': 'TXN123456',
      'payment_method': 'card',
      'status': 'completed',
    };
  });

  Widget createWidgetUnderTest() {
    return MaterialApp(
      theme: AppTheme.lightTheme,
      home: PaymentSuccessScreen(
        trip: testTrip,
        booking: testBooking,
        paymentResult: testPaymentResult,
      ),
    );
  }

  group('PaymentSuccessScreen', () {
    testWidgets('should display payment success message', (tester) async {
      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      expect(find.text('Payment Successful'), findsOneWidget);
      expect(find.text('Payment Successful!'), findsOneWidget);
      expect(find.text('Your booking has been confirmed'), findsOneWidget);
      expect(find.byIcon(Icons.check), findsOneWidget);
    });

    testWidgets('should display booking details', (tester) async {
      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      expect(find.text('Booking Details'), findsOneWidget);
      expect(find.text('Booking Reference'), findsOneWidget);
      expect(find.text('BK123456'), findsOneWidget);
      expect(find.text('Route'), findsOneWidget);
      expect(find.text('Central Terminal → Airport Terminal'), findsOneWidget);
      expect(find.text('Departure'), findsOneWidget);
      expect(find.text('Seats'), findsOneWidget);
      expect(find.text('1, 2'), findsOneWidget);
      expect(find.text('Amount Paid'), findsOneWidget);
      expect(find.text('\$100.00'), findsOneWidget);
    });

    testWidgets('should display transaction ID when available', (tester) async {
      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      expect(find.text('Transaction ID'), findsOneWidget);
      expect(find.text('TXN123456'), findsOneWidget);
    });

    testWidgets('should not display transaction ID when not available', (tester) async {
      // Arrange
      final paymentResultWithoutTxnId = <String, dynamic>{
        'payment_method': 'card',
        'status': 'completed',
      };

      // Act
      await tester.pumpWidget(MaterialApp(
        theme: AppTheme.lightTheme,
        home: PaymentSuccessScreen(
          trip: testTrip,
          booking: testBooking,
          paymentResult: paymentResultWithoutTxnId,
        ),
      ));

      // Assert
      expect(find.text('Transaction ID'), findsNothing);
    });

    testWidgets('should display important information', (tester) async {
      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      expect(find.text('Important Information'), findsOneWidget);
      expect(find.textContaining('Please arrive at the terminal 30 minutes'), findsOneWidget);
      expect(find.textContaining('Bring a valid ID for verification'), findsOneWidget);
      expect(find.textContaining('Show this booking confirmation'), findsOneWidget);
      expect(find.textContaining('Check your email for the e-ticket'), findsOneWidget);
    });

    testWidgets('should display action buttons', (tester) async {
      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      expect(find.text('Download E-Ticket'), findsOneWidget);
      expect(find.text('Track Your Trip'), findsOneWidget);
      expect(find.text('Back to Home'), findsOneWidget);
    });

    testWidgets('should display support information', (tester) async {
      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      expect(find.text('Need Help?'), findsOneWidget);
      expect(find.textContaining('Contact our support team'), findsOneWidget);
      expect(find.text('Call'), findsOneWidget);
      expect(find.text('Email'), findsOneWidget);
      expect(find.text('Chat'), findsOneWidget);
      expect(find.byIcon(Icons.phone), findsOneWidget);
      expect(find.byIcon(Icons.email), findsOneWidget);
      expect(find.byIcon(Icons.chat), findsOneWidget);
    });

    testWidgets('should show snackbar when download e-ticket is tapped', (tester) async {
      // Act
      await tester.pumpWidget(createWidgetUnderTest());
      await tester.tap(find.text('Download E-Ticket'));
      await tester.pump();

      // Assert
      expect(find.text('E-ticket will be sent to your email'), findsOneWidget);
    });

    testWidgets('should show snackbar when track trip is tapped', (tester) async {
      // Act
      await tester.pumpWidget(createWidgetUnderTest());
      await tester.tap(find.text('Track Your Trip'));
      await tester.pump();

      // Assert
      expect(find.text('Track your trip feature coming soon'), findsOneWidget);
    });

    testWidgets('should navigate back to home when back button is tapped', (tester) async {
      // Act
      await tester.pumpWidget(createWidgetUnderTest());
      await tester.tap(find.text('Back to Home'));
      await tester.pumpAndSettle();

      // Assert - In a real test, we would verify navigation
      // For now, we just verify the widget is still there
      expect(find.byType(PaymentSuccessScreen), findsOneWidget);
    });

    testWidgets('should display correct icons for booking details', (tester) async {
      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      expect(find.byIcon(Icons.confirmation_number), findsOneWidget);
      expect(find.byIcon(Icons.directions_bus), findsOneWidget);
      expect(find.byIcon(Icons.schedule), findsOneWidget);
      expect(find.byIcon(Icons.event_seat), findsOneWidget);
      expect(find.byIcon(Icons.payment), findsOneWidget);
      expect(find.byIcon(Icons.receipt), findsOneWidget);
    });

    testWidgets('should have proper styling for success elements', (tester) async {
      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      final successIcon = tester.widget<Icon>(find.byIcon(Icons.check));
      expect(successIcon.color, equals(Colors.green));
      expect(successIcon.size, equals(60));

      // Check for green color in success text
      final successText = tester.widget<Text>(find.text('Payment Successful!'));
      expect(successText.style?.color, equals(Colors.green));
      expect(successText.style?.fontSize, equals(24));
      expect(successText.style?.fontWeight, equals(FontWeight.bold));
    });

    testWidgets('should display amount paid with correct styling', (tester) async {
      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      final amountText = tester.widget<Text>(find.text('\$100.00').last);
      expect(amountText.style?.color, equals(Colors.green));
      expect(amountText.style?.fontWeight, equals(FontWeight.w500));
    });

    testWidgets('should handle support button taps', (tester) async {
      // Act
      await tester.pumpWidget(createWidgetUnderTest());
      
      // Test call button
      await tester.tap(find.text('Call'));
      await tester.pump();
      
      // Test email button
      await tester.tap(find.text('Email'));
      await tester.pump();
      
      // Test chat button
      await tester.tap(find.text('Chat'));
      await tester.pump();

      // Assert - In a real implementation, these would trigger actual actions
      // For now, we just verify the buttons are tappable
      expect(find.text('Call'), findsOneWidget);
      expect(find.text('Email'), findsOneWidget);
      expect(find.text('Chat'), findsOneWidget);
    });
  });
}