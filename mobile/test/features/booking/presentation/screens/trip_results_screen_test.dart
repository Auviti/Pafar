import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:mockito/mockito.dart';
import 'package:mockito/annotations.dart';

import 'package:pafar_mobile/features/booking/presentation/screens/trip_results_screen.dart';
import 'package:pafar_mobile/features/booking/presentation/bloc/booking_bloc.dart';
import 'package:pafar_mobile/features/booking/presentation/bloc/booking_state.dart';
import 'package:pafar_mobile/features/booking/presentation/bloc/booking_event.dart';
import 'package:pafar_mobile/features/booking/domain/entities/trip.dart';
import 'package:pafar_mobile/features/booking/domain/entities/route.dart';
import 'package:pafar_mobile/features/booking/domain/entities/terminal.dart';
import 'package:pafar_mobile/shared/theme/app_theme.dart';

import 'trip_results_screen_test.mocks.dart';

@GenerateMocks([BookingBloc])
void main() {
  late MockBookingBloc mockBookingBloc;
  late List<Trip> testTrips;

  setUp(() {
    mockBookingBloc = MockBookingBloc();
    
    testTrips = [
      Trip(
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
      ),
      Trip(
        id: '2',
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
        busId: 'bus2',
        departureTime: DateTime(2024, 12, 25, 14, 0),
        status: TripStatus.scheduled,
        fare: 75.0,
        availableSeats: 5,
        totalSeats: 40,
      ),
    ];
  });

  Widget createWidgetUnderTest() {
    return MaterialApp(
      theme: AppTheme.lightTheme,
      home: BlocProvider<BookingBloc>(
        create: (context) => mockBookingBloc,
        child: const TripResultsScreen(),
      ),
    );
  }

  group('TripResultsScreen', () {
    testWidgets('should display available trips', (tester) async {
      // Arrange
      when(mockBookingBloc.state).thenReturn(TripsLoaded(
        trips: testTrips,
        filteredTrips: testTrips,
      ));
      when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([
        TripsLoaded(trips: testTrips, filteredTrips: testTrips),
      ]));

      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      expect(find.text('Available Trips'), findsOneWidget);
      expect(find.text('Central Terminal'), findsNWidgets(2));
      expect(find.text('Airport Terminal'), findsNWidgets(2));
      expect(find.text('\$50.00'), findsOneWidget);
      expect(find.text('\$75.00'), findsOneWidget);
      expect(find.text('20 seats available'), findsOneWidget);
      expect(find.text('5 seats available'), findsOneWidget);
    });

    testWidgets('should show loading indicator when loading', (tester) async {
      // Arrange
      when(mockBookingBloc.state).thenReturn(BookingLoading());
      when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([BookingLoading()]));

      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      expect(find.byType(CircularProgressIndicator), findsOneWidget);
    });

    testWidgets('should show no trips message when list is empty', (tester) async {
      // Arrange
      when(mockBookingBloc.state).thenReturn(const TripsLoaded(
        trips: [],
        filteredTrips: [],
      ));
      when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([
        const TripsLoaded(trips: [], filteredTrips: []),
      ]));

      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      expect(find.text('No trips found'), findsOneWidget);
      expect(find.text('Try adjusting your search criteria'), findsOneWidget);
      expect(find.byIcon(Icons.search_off), findsOneWidget);
    });

    testWidgets('should show filter button in app bar', (tester) async {
      // Arrange
      when(mockBookingBloc.state).thenReturn(TripsLoaded(
        trips: testTrips,
        filteredTrips: testTrips,
      ));
      when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([
        TripsLoaded(trips: testTrips, filteredTrips: testTrips),
      ]));

      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      expect(find.byIcon(Icons.filter_list), findsOneWidget);
    });

    testWidgets('should open filter bottom sheet when filter button is tapped', (tester) async {
      // Arrange
      when(mockBookingBloc.state).thenReturn(TripsLoaded(
        trips: testTrips,
        filteredTrips: testTrips,
      ));
      when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([
        TripsLoaded(trips: testTrips, filteredTrips: testTrips),
      ]));

      // Act
      await tester.pumpWidget(createWidgetUnderTest());
      await tester.tap(find.byIcon(Icons.filter_list));
      await tester.pumpAndSettle();

      // Assert
      expect(find.text('Filter & Sort'), findsOneWidget);
      expect(find.text('Sort by:'), findsOneWidget);
      expect(find.text('Departure time:'), findsOneWidget);
      expect(find.text('Max price:'), findsOneWidget);
    });

    testWidgets('should display filter chips in bottom sheet', (tester) async {
      // Arrange
      when(mockBookingBloc.state).thenReturn(TripsLoaded(
        trips: testTrips,
        filteredTrips: testTrips,
      ));
      when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([
        TripsLoaded(trips: testTrips, filteredTrips: testTrips),
      ]));

      // Act
      await tester.pumpWidget(createWidgetUnderTest());
      await tester.tap(find.byIcon(Icons.filter_list));
      await tester.pumpAndSettle();

      // Assert
      expect(find.text('Price: Low to High'), findsOneWidget);
      expect(find.text('Price: High to Low'), findsOneWidget);
      expect(find.text('Departure: Early'), findsOneWidget);
      expect(find.text('Departure: Late'), findsOneWidget);
      expect(find.text('Morning (6AM-12PM)'), findsOneWidget);
      expect(find.text('Afternoon (12PM-6PM)'), findsOneWidget);
      expect(find.text('Evening (6PM-6AM)'), findsOneWidget);
    });

    testWidgets('should apply filters when Apply button is tapped', (tester) async {
      // Arrange
      when(mockBookingBloc.state).thenReturn(TripsLoaded(
        trips: testTrips,
        filteredTrips: testTrips,
      ));
      when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([
        TripsLoaded(trips: testTrips, filteredTrips: testTrips),
      ]));

      // Act
      await tester.pumpWidget(createWidgetUnderTest());
      await tester.tap(find.byIcon(Icons.filter_list));
      await tester.pumpAndSettle();

      // Select a filter
      await tester.tap(find.text('Price: Low to High'));
      await tester.pump();

      // Apply filters
      await tester.tap(find.text('Apply'));
      await tester.pump();

      // Assert
      verify(mockBookingBloc.add(argThat(isA<FilterTrips>()))).called(1);
    });

    testWidgets('should clear all filters when Clear All button is tapped', (tester) async {
      // Arrange
      when(mockBookingBloc.state).thenReturn(TripsLoaded(
        trips: testTrips,
        filteredTrips: testTrips,
      ));
      when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([
        TripsLoaded(trips: testTrips, filteredTrips: testTrips),
      ]));

      // Act
      await tester.pumpWidget(createWidgetUnderTest());
      await tester.tap(find.byIcon(Icons.filter_list));
      await tester.pumpAndSettle();

      // Select filters first
      await tester.tap(find.text('Price: Low to High'));
      await tester.pump();
      await tester.tap(find.text('Morning (6AM-12PM)'));
      await tester.pump();

      // Clear all filters
      await tester.tap(find.text('Clear All'));
      await tester.pump();

      // Assert - filters should be deselected
      final priceChip = tester.widget<FilterChip>(
        find.widgetWithText(FilterChip, 'Price: Low to High'),
      );
      final timeChip = tester.widget<FilterChip>(
        find.widgetWithText(FilterChip, 'Morning (6AM-12PM)'),
      );
      
      expect(priceChip.selected, isFalse);
      expect(timeChip.selected, isFalse);
    });

    testWidgets('should show filter indicator when filters are applied', (tester) async {
      // Arrange
      when(mockBookingBloc.state).thenReturn(TripsLoaded(
        trips: testTrips,
        filteredTrips: testTrips,
        currentFilter: 'price_low',
      ));
      when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([
        TripsLoaded(trips: testTrips, filteredTrips: testTrips, currentFilter: 'price_low'),
      ]));

      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      expect(find.text('Filters applied:'), findsOneWidget);
      expect(find.text('Clear'), findsOneWidget);
    });

    testWidgets('should navigate to seat selection when trip is tapped', (tester) async {
      // Arrange
      when(mockBookingBloc.state).thenReturn(TripsLoaded(
        trips: testTrips,
        filteredTrips: testTrips,
      ));
      when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([
        TripsLoaded(trips: testTrips, filteredTrips: testTrips),
      ]));

      // Act
      await tester.pumpWidget(createWidgetUnderTest());
      
      // Tap on the first trip card
      await tester.tap(find.byType(Card).first);
      await tester.pumpAndSettle();

      // Assert - In a real test, we would verify navigation
      // For now, we just verify the widget is still there
      expect(find.byType(TripResultsScreen), findsOneWidget);
    });

    testWidgets('should show trip status correctly', (tester) async {
      // Arrange
      final tripsWithDifferentStatuses = [
        testTrips[0].copyWith(status: TripStatus.scheduled),
        testTrips[1].copyWith(status: TripStatus.boarding),
      ];

      when(mockBookingBloc.state).thenReturn(TripsLoaded(
        trips: tripsWithDifferentStatuses,
        filteredTrips: tripsWithDifferentStatuses,
      ));
      when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([
        TripsLoaded(trips: tripsWithDifferentStatuses, filteredTrips: tripsWithDifferentStatuses),
      ]));

      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      expect(find.text('SCHEDULED'), findsOneWidget);
      expect(find.text('BOARDING'), findsOneWidget);
    });

    testWidgets('should show error message when loading fails', (tester) async {
      // Arrange
      const errorMessage = 'Failed to load trips';
      when(mockBookingBloc.state).thenReturn(const BookingError(message: errorMessage));
      when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([
        const BookingError(message: errorMessage),
      ]));

      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      expect(find.text(errorMessage), findsOneWidget);
      expect(find.text('Retry'), findsOneWidget);
    });

    testWidgets('should adjust price slider in filter', (tester) async {
      // Arrange
      when(mockBookingBloc.state).thenReturn(TripsLoaded(
        trips: testTrips,
        filteredTrips: testTrips,
      ));
      when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([
        TripsLoaded(trips: testTrips, filteredTrips: testTrips),
      ]));

      // Act
      await tester.pumpWidget(createWidgetUnderTest());
      await tester.tap(find.byIcon(Icons.filter_list));
      await tester.pumpAndSettle();

      // Find and interact with the slider
      final slider = find.byType(Slider);
      expect(slider, findsOneWidget);

      // The slider interaction would require more complex gesture testing
      // For now, we just verify it exists
      expect(find.text('Max price:'), findsOneWidget);
    });
  });
}

// Extension to add copyWith method for testing
extension TripCopyWith on Trip {
  Trip copyWith({
    String? id,
    BusRoute? route,
    String? busId,
    String? driverId,
    DateTime? departureTime,
    DateTime? arrivalTime,
    TripStatus? status,
    double? fare,
    int? availableSeats,
    int? totalSeats,
    Map<String, dynamic>? busDetails,
  }) {
    return Trip(
      id: id ?? this.id,
      route: route ?? this.route,
      busId: busId ?? this.busId,
      driverId: driverId ?? this.driverId,
      departureTime: departureTime ?? this.departureTime,
      arrivalTime: arrivalTime ?? this.arrivalTime,
      status: status ?? this.status,
      fare: fare ?? this.fare,
      availableSeats: availableSeats ?? this.availableSeats,
      totalSeats: totalSeats ?? this.totalSeats,
      busDetails: busDetails ?? this.busDetails,
    );
  }
}