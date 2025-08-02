import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:mockito/mockito.dart';
import 'package:mockito/annotations.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:get_it/get_it.dart';

import 'package:pafar_mobile/main.dart' as app;
import 'package:pafar_mobile/core/di/injection_container.dart';
import 'package:pafar_mobile/features/auth/domain/repositories/auth_repository.dart';
import 'package:pafar_mobile/features/booking/domain/repositories/booking_repository.dart';
import 'package:pafar_mobile/features/tracking/domain/repositories/tracking_repository.dart';
import 'package:pafar_mobile/features/auth/domain/entities/user.dart';
import 'package:pafar_mobile/features/booking/domain/entities/trip.dart';
import 'package:pafar_mobile/features/booking/domain/entities/booking.dart';
import 'package:pafar_mobile/features/booking/domain/entities/terminal.dart';
import 'package:pafar_mobile/core/utils/either.dart';
import 'package:pafar_mobile/core/error/failures.dart';

import 'complete_app_integration_test.mocks.dart';

@GenerateMocks([
  AuthRepository,
  BookingRepository,
  TrackingRepository,
])
void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  group('Complete Mobile App Integration Tests', () {
    late MockAuthRepository mockAuthRepository;
    late MockBookingRepository mockBookingRepository;
    late MockTrackingRepository mockTrackingRepository;

    setUpAll(() async {
      // Initialize dependency injection
      await initializeDependencies();
      
      // Setup mocks
      mockAuthRepository = MockAuthRepository();
      mockBookingRepository = MockBookingRepository();
      mockTrackingRepository = MockTrackingRepository();
      
      // Register mocks
      GetIt.instance.registerSingleton<AuthRepository>(mockAuthRepository);
      GetIt.instance.registerSingleton<BookingRepository>(mockBookingRepository);
      GetIt.instance.registerSingleton<TrackingRepository>(mockTrackingRepository);
    });

    tearDownAll(() async {
      await GetIt.instance.reset();
    });

    group('Complete User Journey Tests', () {
      testWidgets('Complete booking flow from registration to payment', (tester) async {
        // Setup mock responses
        final mockUser = User(
          id: '1',
          email: 'test@example.com',
          firstName: 'Test',
          lastName: 'User',
          role: UserRole.passenger,
          isVerified: true,
          isActive: true,
          createdAt: DateTime.now(),
        );

        final mockTerminals = [
          Terminal(
            id: '1',
            name: 'Central Terminal',
            city: 'New York',
            address: '123 Main St',
            latitude: 40.7128,
            longitude: -74.0060,
            isActive: true,
          ),
          Terminal(
            id: '2',
            name: 'Airport Terminal',
            city: 'Los Angeles',
            address: '456 Airport Blvd',
            latitude: 34.0522,
            longitude: -118.2437,
            isActive: true,
          ),
        ];

        final mockTrip = Trip(
          id: '1',
          route: Route(
            id: '1',
            originTerminal: mockTerminals[0],
            destinationTerminal: mockTerminals[1],
            distanceKm: 250.0,
            estimatedDurationMinutes: 300,
            baseFare: 50.0,
            isActive: true,
          ),
          busId: 'bus-1',
          departureTime: DateTime.now().add(const Duration(hours: 2)),
          arrivalTime: DateTime.now().add(const Duration(hours: 6)),
          status: TripStatus.scheduled,
          fare: 50.0,
          totalSeats: 40,
          availableSeats: 38,
        );

        final mockBooking = Booking(
          id: '1',
          userId: mockUser.id,
          trip: mockTrip,
          seatNumbers: [1, 2],
          totalAmount: 100.0,
          status: BookingStatus.confirmed,
          paymentStatus: PaymentStatus.completed,
          bookingReference: 'BK123456',
          createdAt: DateTime.now(),
        );

        // Mock repository responses
        when(mockAuthRepository.register(any))
            .thenAnswer((_) async => Right(mockUser));
        
        when(mockAuthRepository.login(any, any))
            .thenAnswer((_) async => Right(mockUser));
        
        when(mockBookingRepository.getTerminals())
            .thenAnswer((_) async => Right(mockTerminals));
        
        when(mockBookingRepository.searchTrips(any))
            .thenAnswer((_) async => Right([mockTrip]));
        
        when(mockBookingRepository.createBooking(any))
            .thenAnswer((_) async => Right(mockBooking));
        
        when(mockBookingRepository.processPayment(any))
            .thenAnswer((_) async => Right(mockBooking));

        // Start the app
        await app.main();
        await tester.pumpAndSettle();

        // Step 1: Navigate to registration
        expect(find.text('Welcome to Pafar'), findsOneWidget);
        await tester.tap(find.text('Sign Up'));
        await tester.pumpAndSettle();

        // Step 2: Fill registration form
        await tester.enterText(find.byKey(const Key('firstName_field')), 'Test');
        await tester.enterText(find.byKey(const Key('lastName_field')), 'User');
        await tester.enterText(find.byKey(const Key('email_field')), 'test@example.com');
        await tester.enterText(find.byKey(const Key('password_field')), 'password123');
        await tester.enterText(find.byKey(const Key('confirmPassword_field')), 'password123');
        
        await tester.tap(find.byKey(const Key('register_button')));
        await tester.pumpAndSettle();

        // Verify registration success
        expect(find.text('Registration Successful'), findsOneWidget);
        
        // Step 3: Navigate to login
        await tester.tap(find.text('Continue to Login'));
        await tester.pumpAndSettle();

        // Step 4: Login
        await tester.enterText(find.byKey(const Key('email_field')), 'test@example.com');
        await tester.enterText(find.byKey(const Key('password_field')), 'password123');
        await tester.tap(find.byKey(const Key('login_button')));
        await tester.pumpAndSettle();

        // Verify login success and navigation to home
        expect(find.text('Welcome, Test!'), findsOneWidget);
        expect(find.byKey(const Key('home_screen')), findsOneWidget);

        // Step 5: Navigate to booking
        await tester.tap(find.byKey(const Key('book_trip_button')));
        await tester.pumpAndSettle();

        // Step 6: Fill trip search form
        await tester.tap(find.byKey(const Key('origin_dropdown')));
        await tester.pumpAndSettle();
        await tester.tap(find.text('Central Terminal'));
        await tester.pumpAndSettle();

        await tester.tap(find.byKey(const Key('destination_dropdown')));
        await tester.pumpAndSettle();
        await tester.tap(find.text('Airport Terminal'));
        await tester.pumpAndSettle();

        // Select departure date
        await tester.tap(find.byKey(const Key('departure_date_field')));
        await tester.pumpAndSettle();
        await tester.tap(find.text('OK')); // Confirm date picker
        await tester.pumpAndSettle();

        // Search for trips
        await tester.tap(find.byKey(const Key('search_button')));
        await tester.pumpAndSettle();

        // Step 7: Verify search results
        expect(find.text('Available Trips'), findsOneWidget);
        expect(find.text('Central Terminal → Airport Terminal'), findsOneWidget);
        expect(find.text('\$50.00'), findsOneWidget);

        // Step 8: Select trip
        await tester.tap(find.byKey(const Key('trip_card_1')));
        await tester.pumpAndSettle();

        // Step 9: Select seats
        expect(find.text('Select Your Seats'), findsOneWidget);
        await tester.tap(find.byKey(const Key('seat_1')));
        await tester.tap(find.byKey(const Key('seat_2')));
        await tester.pumpAndSettle();

        // Verify seat selection
        expect(find.text('Selected Seats: 1, 2'), findsOneWidget);
        expect(find.text('Total: \$100.00'), findsOneWidget);

        // Continue to payment
        await tester.tap(find.byKey(const Key('continue_payment_button')));
        await tester.pumpAndSettle();

        // Step 10: Payment
        expect(find.text('Payment'), findsOneWidget);
        
        // Fill payment details
        await tester.enterText(find.byKey(const Key('card_number_field')), '4242424242424242');
        await tester.enterText(find.byKey(const Key('expiry_field')), '12/25');
        await tester.enterText(find.byKey(const Key('cvc_field')), '123');
        await tester.enterText(find.byKey(const Key('cardholder_name_field')), 'Test User');

        await tester.tap(find.byKey(const Key('pay_button')));
        await tester.pumpAndSettle();

        // Step 11: Verify booking success
        expect(find.text('Booking Confirmed!'), findsOneWidget);
        expect(find.text('BK123456'), findsOneWidget);
        expect(find.byKey(const Key('booking_success_screen')), findsOneWidget);

        // Verify repository calls
        verify(mockAuthRepository.register(any)).called(1);
        verify(mockAuthRepository.login(any, any)).called(1);
        verify(mockBookingRepository.searchTrips(any)).called(1);
        verify(mockBookingRepository.createBooking(any)).called(1);
        verify(mockBookingRepository.processPayment(any)).called(1);
      });

      testWidgets('Real-time trip tracking integration', (tester) async {
        // Setup authenticated user
        final mockUser = User(
          id: '1',
          email: 'tracking@example.com',
          firstName: 'Tracking',
          lastName: 'User',
          role: UserRole.passenger,
          isVerified: true,
          isActive: true,
          createdAt: DateTime.now(),
        );

        final mockBooking = Booking(
          id: '1',
          userId: mockUser.id,
          trip: Trip(
            id: '1',
            route: Route(
              id: '1',
              originTerminal: Terminal(
                id: '1',
                name: 'Central Terminal',
                city: 'New York',
                address: '123 Main St',
                latitude: 40.7128,
                longitude: -74.0060,
                isActive: true,
              ),
              destinationTerminal: Terminal(
                id: '2',
                name: 'Airport Terminal',
                city: 'Los Angeles',
                address: '456 Airport Blvd',
                latitude: 34.0522,
                longitude: -118.2437,
                isActive: true,
              ),
              distanceKm: 250.0,
              estimatedDurationMinutes: 300,
              baseFare: 50.0,
              isActive: true,
            ),
            busId: 'bus-1',
            departureTime: DateTime.now().add(const Duration(hours: 1)),
            arrivalTime: DateTime.now().add(const Duration(hours: 5)),
            status: TripStatus.inProgress,
            fare: 50.0,
            totalSeats: 40,
            availableSeats: 39,
          ),
          seatNumbers: [1],
          totalAmount: 50.0,
          status: BookingStatus.confirmed,
          paymentStatus: PaymentStatus.completed,
          bookingReference: 'BK789012',
          createdAt: DateTime.now(),
        );

        final mockLocation = TripLocation(
          tripId: '1',
          latitude: 40.7130,
          longitude: -74.0058,
          speed: 65.0,
          heading: 95.0,
          timestamp: DateTime.now(),
        );

        // Mock repository responses
        when(mockAuthRepository.getCurrentUser())
            .thenAnswer((_) async => Right(mockUser));
        
        when(mockBookingRepository.getUserBookings(any))
            .thenAnswer((_) async => Right([mockBooking]));
        
        when(mockTrackingRepository.getTripLocation(any))
            .thenAnswer((_) async => Right(mockLocation));
        
        when(mockTrackingRepository.subscribeToTripUpdates(any))
            .thenAnswer((_) => Stream.periodic(
              const Duration(seconds: 1),
              (count) => mockLocation.copyWith(
                latitude: mockLocation.latitude + (count * 0.001),
                longitude: mockLocation.longitude + (count * 0.001),
              ),
            ));

        // Start the app and navigate to tracking
        await app.main();
        await tester.pumpAndSettle();

        // Navigate to bookings
        await tester.tap(find.byKey(const Key('my_bookings_tab')));
        await tester.pumpAndSettle();

        // Verify booking is displayed
        expect(find.text('BK789012'), findsOneWidget);
        expect(find.text('In Progress'), findsOneWidget);

        // Tap on booking to view details
        await tester.tap(find.byKey(const Key('booking_card_1')));
        await tester.pumpAndSettle();

        // Navigate to tracking
        await tester.tap(find.byKey(const Key('track_trip_button')));
        await tester.pumpAndSettle();

        // Verify tracking screen
        expect(find.text('Trip Tracking'), findsOneWidget);
        expect(find.byKey(const Key('trip_map')), findsOneWidget);
        expect(find.text('Current Location'), findsOneWidget);

        // Wait for real-time updates
        await tester.pump(const Duration(seconds: 2));

        // Verify location updates are received
        verify(mockTrackingRepository.getTripLocation(any)).called(greaterThan(0));
        verify(mockTrackingRepository.subscribeToTripUpdates(any)).called(1);

        // Test ETA display
        expect(find.byKey(const Key('eta_display')), findsOneWidget);
        expect(find.textContaining('ETA:'), findsOneWidget);
      });

      testWidgets('Offline functionality and data synchronization', (tester) async {
        // Setup offline scenario
        when(mockBookingRepository.searchTrips(any))
            .thenAnswer((_) async => const Left(NetworkFailure('No internet connection')));
        
        when(mockBookingRepository.getCachedTrips())
            .thenAnswer((_) async => Right([
              Trip(
                id: 'cached-1',
                route: Route(
                  id: '1',
                  originTerminal: Terminal(
                    id: '1',
                    name: 'Cached Terminal',
                    city: 'Offline City',
                    address: '123 Cache St',
                    latitude: 40.0,
                    longitude: -74.0,
                    isActive: true,
                  ),
                  destinationTerminal: Terminal(
                    id: '2',
                    name: 'Cached Destination',
                    city: 'Offline Dest',
                    address: '456 Cache Ave',
                    latitude: 41.0,
                    longitude: -75.0,
                    isActive: true,
                  ),
                  distanceKm: 100.0,
                  estimatedDurationMinutes: 120,
                  baseFare: 30.0,
                  isActive: true,
                ),
                busId: 'cached-bus',
                departureTime: DateTime.now().add(const Duration(hours: 3)),
                arrivalTime: DateTime.now().add(const Duration(hours: 5)),
                status: TripStatus.scheduled,
                fare: 30.0,
                totalSeats: 30,
                availableSeats: 25,
              ),
            ]));

        await app.main();
        await tester.pumpAndSettle();

        // Navigate to booking
        await tester.tap(find.byKey(const Key('book_trip_button')));
        await tester.pumpAndSettle();

        // Attempt to search (will fail due to network)
        await tester.tap(find.byKey(const Key('search_button')));
        await tester.pumpAndSettle();

        // Verify offline message is shown
        expect(find.text('No internet connection'), findsOneWidget);
        expect(find.text('Showing cached results'), findsOneWidget);

        // Verify cached trips are displayed
        expect(find.text('Cached Terminal → Cached Destination'), findsOneWidget);
        expect(find.text('\$30.00'), findsOneWidget);

        // Test sync when connection is restored
        when(mockBookingRepository.searchTrips(any))
            .thenAnswer((_) async => Right([
              Trip(
                id: 'online-1',
                route: Route(
                  id: '2',
                  originTerminal: Terminal(
                    id: '3',
                    name: 'Online Terminal',
                    city: 'Connected City',
                    address: '789 Online St',
                    latitude: 42.0,
                    longitude: -76.0,
                    isActive: true,
                  ),
                  destinationTerminal: Terminal(
                    id: '4',
                    name: 'Online Destination',
                    city: 'Connected Dest',
                    address: '101 Online Ave',
                    latitude: 43.0,
                    longitude: -77.0,
                    isActive: true,
                  ),
                  distanceKm: 150.0,
                  estimatedDurationMinutes: 180,
                  baseFare: 40.0,
                  isActive: true,
                ),
                busId: 'online-bus',
                departureTime: DateTime.now().add(const Duration(hours: 4)),
                arrivalTime: DateTime.now().add(const Duration(hours: 7)),
                status: TripStatus.scheduled,
                fare: 40.0,
                totalSeats: 35,
                availableSeats: 30,
              ),
            ]));

        // Tap retry to sync
        await tester.tap(find.byKey(const Key('retry_button')));
        await tester.pumpAndSettle();

        // Verify online data is now displayed
        expect(find.text('Online Terminal → Online Destination'), findsOneWidget);
        expect(find.text('\$40.00'), findsOneWidget);
      });

      testWidgets('Push notification handling', (tester) async {
        // Setup notification scenario
        final mockUser = User(
          id: '1',
          email: 'notification@example.com',
          firstName: 'Notification',
          lastName: 'User',
          role: UserRole.passenger,
          isVerified: true,
          isActive: true,
          createdAt: DateTime.now(),
        );

        when(mockAuthRepository.getCurrentUser())
            .thenAnswer((_) async => Right(mockUser));

        await app.main();
        await tester.pumpAndSettle();

        // Simulate receiving a push notification
        await tester.binding.defaultBinaryMessenger.handlePlatformMessage(
          'plugins.flutter.io/firebase_messaging',
          null,
          (data) {},
        );

        // Verify notification is handled
        expect(find.byKey(const Key('notification_badge')), findsOneWidget);

        // Tap notification to view details
        await tester.tap(find.byKey(const Key('notification_icon')));
        await tester.pumpAndSettle();

        // Verify notification center opens
        expect(find.text('Notifications'), findsOneWidget);
        expect(find.byKey(const Key('notification_list')), findsOneWidget);
      });

      testWidgets('Error handling and recovery', (tester) async {
        // Test various error scenarios
        
        // Network error
        when(mockAuthRepository.login(any, any))
            .thenAnswer((_) async => const Left(NetworkFailure('Network error')));

        await app.main();
        await tester.pumpAndSettle();

        // Attempt login
        await tester.enterText(find.byKey(const Key('email_field')), 'error@example.com');
        await tester.enterText(find.byKey(const Key('password_field')), 'password123');
        await tester.tap(find.byKey(const Key('login_button')));
        await tester.pumpAndSettle();

        // Verify error is displayed
        expect(find.text('Network error'), findsOneWidget);
        expect(find.byKey(const Key('retry_button')), findsOneWidget);

        // Test retry functionality
        when(mockAuthRepository.login(any, any))
            .thenAnswer((_) async => Right(User(
              id: '1',
              email: 'error@example.com',
              firstName: 'Error',
              lastName: 'User',
              role: UserRole.passenger,
              isVerified: true,
              isActive: true,
              createdAt: DateTime.now(),
            )));

        await tester.tap(find.byKey(const Key('retry_button')));
        await tester.pumpAndSettle();

        // Verify successful retry
        expect(find.text('Welcome, Error!'), findsOneWidget);
      });

      testWidgets('Accessibility features', (tester) async {
        await app.main();
        await tester.pumpAndSettle();

        // Test semantic labels
        expect(find.bySemanticsLabel('Email input field'), findsOneWidget);
        expect(find.bySemanticsLabel('Password input field'), findsOneWidget);
        expect(find.bySemanticsLabel('Login button'), findsOneWidget);

        // Test screen reader announcements
        await tester.tap(find.byKey(const Key('login_button')));
        await tester.pumpAndSettle();

        // Verify accessibility announcements
        expect(find.bySemanticsLabel('Login failed. Please check your credentials.'), findsOneWidget);

        // Test high contrast mode
        await tester.binding.platformDispatcher.onPlatformBrightnessChanged?.call();
        await tester.pumpAndSettle();

        // Verify UI adapts to accessibility settings
        expect(find.byKey(const Key('high_contrast_theme')), findsOneWidget);
      });

      testWidgets('Performance under load', (tester) async {
        // Setup large dataset
        final largeTripsData = List.generate(100, (index) => Trip(
          id: 'trip-$index',
          route: Route(
            id: 'route-$index',
            originTerminal: Terminal(
              id: 'origin-$index',
              name: 'Origin $index',
              city: 'City $index',
              address: 'Address $index',
              latitude: 40.0 + index * 0.01,
              longitude: -74.0 + index * 0.01,
              isActive: true,
            ),
            destinationTerminal: Terminal(
              id: 'dest-$index',
              name: 'Destination $index',
              city: 'Dest City $index',
              address: 'Dest Address $index',
              latitude: 41.0 + index * 0.01,
              longitude: -75.0 + index * 0.01,
              isActive: true,
            ),
            distanceKm: 100.0 + index * 10,
            estimatedDurationMinutes: 120 + index * 5,
            baseFare: 30.0 + index * 2,
            isActive: true,
          ),
          busId: 'bus-$index',
          departureTime: DateTime.now().add(Duration(hours: index)),
          arrivalTime: DateTime.now().add(Duration(hours: index + 2)),
          status: TripStatus.scheduled,
          fare: 30.0 + index * 2,
          totalSeats: 40,
          availableSeats: 35,
        ));

        when(mockBookingRepository.searchTrips(any))
            .thenAnswer((_) async => Right(largeTripsData));

        await app.main();
        await tester.pumpAndSettle();

        // Navigate to booking and search
        await tester.tap(find.byKey(const Key('book_trip_button')));
        await tester.pumpAndSettle();

        final stopwatch = Stopwatch()..start();
        await tester.tap(find.byKey(const Key('search_button')));
        await tester.pumpAndSettle();
        stopwatch.stop();

        // Verify performance is acceptable
        expect(stopwatch.elapsedMilliseconds, lessThan(3000)); // Less than 3 seconds

        // Verify large list is rendered efficiently
        expect(find.byType(ListView), findsOneWidget);
        
        // Test scrolling performance
        final scrollStopwatch = Stopwatch()..start();
        await tester.drag(find.byType(ListView), const Offset(0, -1000));
        await tester.pumpAndSettle();
        scrollStopwatch.stop();

        expect(scrollStopwatch.elapsedMilliseconds, lessThan(1000)); // Smooth scrolling
      });
    });

    group('Cross-Platform Data Consistency Tests', () {
      testWidgets('Data synchronization between platforms', (tester) async {
        // Test that mobile app data stays consistent with backend
        final mockUser = User(
          id: '1',
          email: 'sync@example.com',
          firstName: 'Sync',
          lastName: 'User',
          role: UserRole.passenger,
          isVerified: true,
          isActive: true,
          createdAt: DateTime.now(),
        );

        final mockBooking = Booking(
          id: '1',
          userId: mockUser.id,
          trip: Trip(
            id: '1',
            route: Route(
              id: '1',
              originTerminal: Terminal(
                id: '1',
                name: 'Sync Terminal',
                city: 'Sync City',
                address: '123 Sync St',
                latitude: 40.0,
                longitude: -74.0,
                isActive: true,
              ),
              destinationTerminal: Terminal(
                id: '2',
                name: 'Sync Destination',
                city: 'Sync Dest',
                address: '456 Sync Ave',
                latitude: 41.0,
                longitude: -75.0,
                isActive: true,
              ),
              distanceKm: 100.0,
              estimatedDurationMinutes: 120,
              baseFare: 30.0,
              isActive: true,
            ),
            busId: 'sync-bus',
            departureTime: DateTime.now().add(const Duration(hours: 2)),
            arrivalTime: DateTime.now().add(const Duration(hours: 4)),
            status: TripStatus.scheduled,
            fare: 30.0,
            totalSeats: 30,
            availableSeats: 29,
          ),
          seatNumbers: [1],
          totalAmount: 30.0,
          status: BookingStatus.confirmed,
          paymentStatus: PaymentStatus.completed,
          bookingReference: 'SYNC123',
          createdAt: DateTime.now(),
        );

        when(mockAuthRepository.getCurrentUser())
            .thenAnswer((_) async => Right(mockUser));
        
        when(mockBookingRepository.getUserBookings(any))
            .thenAnswer((_) async => Right([mockBooking]));

        await app.main();
        await tester.pumpAndSettle();

        // Navigate to bookings
        await tester.tap(find.byKey(const Key('my_bookings_tab')));
        await tester.pumpAndSettle();

        // Verify booking data is displayed correctly
        expect(find.text('SYNC123'), findsOneWidget);
        expect(find.text('Confirmed'), findsOneWidget);
        expect(find.text('\$30.00'), findsOneWidget);

        // Simulate backend update (trip status change)
        final updatedBooking = mockBooking.copyWith(
          trip: mockBooking.trip.copyWith(status: TripStatus.delayed),
        );

        when(mockBookingRepository.getUserBookings(any))
            .thenAnswer((_) async => Right([updatedBooking]));

        // Refresh data
        await tester.drag(find.byType(RefreshIndicator), const Offset(0, 300));
        await tester.pumpAndSettle();

        // Verify updated status is reflected
        expect(find.text('Delayed'), findsOneWidget);
      });
    });
  });
}

// Extension methods for test data creation
extension TripCopyWith on Trip {
  Trip copyWith({
    String? id,
    Route? route,
    String? busId,
    DateTime? departureTime,
    DateTime? arrivalTime,
    TripStatus? status,
    double? fare,
    int? totalSeats,
    int? availableSeats,
  }) {
    return Trip(
      id: id ?? this.id,
      route: route ?? this.route,
      busId: busId ?? this.busId,
      departureTime: departureTime ?? this.departureTime,
      arrivalTime: arrivalTime ?? this.arrivalTime,
      status: status ?? this.status,
      fare: fare ?? this.fare,
      totalSeats: totalSeats ?? this.totalSeats,
      availableSeats: availableSeats ?? this.availableSeats,
    );
  }
}

extension BookingCopyWith on Booking {
  Booking copyWith({
    String? id,
    String? userId,
    Trip? trip,
    List<int>? seatNumbers,
    double? totalAmount,
    BookingStatus? status,
    PaymentStatus? paymentStatus,
    String? bookingReference,
    DateTime? createdAt,
  }) {
    return Booking(
      id: id ?? this.id,
      userId: userId ?? this.userId,
      trip: trip ?? this.trip,
      seatNumbers: seatNumbers ?? this.seatNumbers,
      totalAmount: totalAmount ?? this.totalAmount,
      status: status ?? this.status,
      paymentStatus: paymentStatus ?? this.paymentStatus,
      bookingReference: bookingReference ?? this.bookingReference,
      createdAt: createdAt ?? this.createdAt,
    );
  }
}

extension TripLocationCopyWith on TripLocation {
  TripLocation copyWith({
    String? tripId,
    double? latitude,
    double? longitude,
    double? speed,
    double? heading,
    DateTime? timestamp,
  }) {
    return TripLocation(
      tripId: tripId ?? this.tripId,
      latitude: latitude ?? this.latitude,
      longitude: longitude ?? this.longitude,
      speed: speed ?? this.speed,
      heading: heading ?? this.heading,
      timestamp: timestamp ?? this.timestamp,
    );
  }
}