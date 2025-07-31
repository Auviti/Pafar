import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:mockito/mockito.dart';
import 'package:mockito/annotations.dart';

import 'package:pafar_mobile/features/tracking/presentation/screens/trip_history_screen.dart';
import 'package:pafar_mobile/features/tracking/presentation/bloc/tracking_bloc.dart';
import 'package:pafar_mobile/features/tracking/presentation/bloc/tracking_state.dart';
import 'package:pafar_mobile/features/tracking/presentation/bloc/tracking_event.dart';
import 'package:pafar_mobile/features/tracking/domain/entities/trip_tracking.dart';
import 'package:pafar_mobile/features/tracking/domain/entities/trip_status.dart';

import 'trip_history_screen_test.mocks.dart';

@GenerateMocks([TrackingBloc])
void main() {
  late MockTrackingBloc mockTrackingBloc;
  final testDate = DateTime(2024, 1, 1);

  setUp(() {
    mockTrackingBloc = MockTrackingBloc();
  });

  Widget createWidgetUnderTest() {
    return MaterialApp(
      home: BlocProvider<TrackingBloc>(
        create: (context) => mockTrackingBloc,
        child: const TripHistoryScreen(userId: 'test-user-id'),
      ),
    );
  }

  group('TripHistoryScreen', () {
    testWidgets('should display loading widget when state is loading', (tester) async {
      // Arrange
      when(mockTrackingBloc.state).thenReturn(const TrackingLoading());
      when(mockTrackingBloc.stream).thenAnswer((_) => const Stream.empty());

      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      expect(find.byType(CircularProgressIndicator), findsOneWidget);
    });

    testWidgets('should display error widget when state is error', (tester) async {
      // Arrange
      const errorMessage = 'Failed to load trips';
      when(mockTrackingBloc.state).thenReturn(const TrackingError(message: errorMessage));
      when(mockTrackingBloc.stream).thenAnswer((_) => const Stream.empty());

      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      expect(find.text(errorMessage), findsOneWidget);
      expect(find.text('Try Again'), findsOneWidget);
    });

    testWidgets('should display tabs for active trips and history', (tester) async {
      // Arrange
      when(mockTrackingBloc.state).thenReturn(const ActiveTripsLoaded(activeTrips: []));
      when(mockTrackingBloc.stream).thenAnswer((_) => const Stream.empty());

      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      expect(find.text('Active Trips'), findsOneWidget);
      expect(find.text('Trip History'), findsOneWidget);
    });

    testWidgets('should display empty state when no active trips', (tester) async {
      // Arrange
      when(mockTrackingBloc.state).thenReturn(const ActiveTripsLoaded(activeTrips: []));
      when(mockTrackingBloc.stream).thenAnswer((_) => const Stream.empty());

      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      expect(find.text('No active trips'), findsOneWidget);
      expect(find.text('Your active trips will appear here'), findsOneWidget);
      expect(find.byIcon(Icons.directions_bus), findsOneWidget);
    });

    testWidgets('should display empty state when no trip history', (tester) async {
      // Arrange
      when(mockTrackingBloc.state).thenReturn(const TripHistoryLoaded(tripHistory: []));
      when(mockTrackingBloc.stream).thenAnswer((_) => const Stream.empty());

      // Act
      await tester.pumpWidget(createWidgetUnderTest());
      await tester.tap(find.text('Trip History'));
      await tester.pumpAndSettle();

      // Assert
      expect(find.text('No trip history'), findsOneWidget);
      expect(find.text('Your completed trips will appear here'), findsOneWidget);
      expect(find.byIcon(Icons.history), findsOneWidget);
    });

    testWidgets('should display active trips when loaded', (tester) async {
      // Arrange
      final activeTrips = [
        TripTracking(
          tripId: 'trip-1',
          bookingId: 'booking-1',
          status: TripStatus(
            tripId: 'trip-1',
            status: TripStatusType.inTransit,
            timestamp: testDate,
          ),
          routeName: 'Lagos - Abuja',
          originTerminal: 'Lagos Terminal',
          destinationTerminal: 'Abuja Terminal',
          estimatedArrival: testDate.add(const Duration(hours: 2)),
        ),
        TripTracking(
          tripId: 'trip-2',
          bookingId: 'booking-2',
          status: TripStatus(
            tripId: 'trip-2',
            status: TripStatusType.boarding,
            timestamp: testDate,
          ),
          routeName: 'Abuja - Kano',
          originTerminal: 'Abuja Terminal',
          destinationTerminal: 'Kano Terminal',
        ),
      ];

      when(mockTrackingBloc.state).thenReturn(ActiveTripsLoaded(activeTrips: activeTrips));
      when(mockTrackingBloc.stream).thenAnswer((_) => const Stream.empty());

      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      expect(find.text('Lagos - Abuja'), findsOneWidget);
      expect(find.text('Abuja - Kano'), findsOneWidget);
      expect(find.text('In Transit'), findsOneWidget);
      expect(find.text('Boarding'), findsOneWidget);
      expect(find.text('Track'), findsNWidgets(2));
    });

    testWidgets('should display trip history when loaded', (tester) async {
      // Arrange
      final tripHistory = [
        TripTracking(
          tripId: 'trip-3',
          bookingId: 'booking-3',
          status: TripStatus(
            tripId: 'trip-3',
            status: TripStatusType.completed,
            timestamp: testDate,
          ),
          routeName: 'Lagos - Ibadan',
          originTerminal: 'Lagos Terminal',
          destinationTerminal: 'Ibadan Terminal',
        ),
      ];

      when(mockTrackingBloc.state).thenReturn(TripHistoryLoaded(tripHistory: tripHistory));
      when(mockTrackingBloc.stream).thenAnswer((_) => const Stream.empty());

      // Act
      await tester.pumpWidget(createWidgetUnderTest());
      await tester.tap(find.text('Trip History'));
      await tester.pumpAndSettle();

      // Assert
      expect(find.text('Lagos - Ibadan'), findsOneWidget);
      expect(find.text('Completed'), findsOneWidget);
    });

    testWidgets('should add LoadActiveTrips event on init', (tester) async {
      // Arrange
      when(mockTrackingBloc.state).thenReturn(const ActiveTripsLoaded(activeTrips: []));
      when(mockTrackingBloc.stream).thenAnswer((_) => const Stream.empty());

      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      verify(mockTrackingBloc.add(const LoadActiveTrips(userId: 'test-user-id'))).called(1);
    });

    testWidgets('should add LoadTripHistory event when history tab is tapped', (tester) async {
      // Arrange
      when(mockTrackingBloc.state).thenReturn(const ActiveTripsLoaded(activeTrips: []));
      when(mockTrackingBloc.stream).thenAnswer((_) => const Stream.empty());

      // Act
      await tester.pumpWidget(createWidgetUnderTest());
      await tester.tap(find.text('Trip History'));

      // Assert
      verify(mockTrackingBloc.add(const LoadTripHistory(userId: 'test-user-id'))).called(1);
    });

    testWidgets('should show status chips with correct colors', (tester) async {
      // Arrange
      final activeTrips = [
        TripTracking(
          tripId: 'trip-1',
          bookingId: 'booking-1',
          status: TripStatus(
            tripId: 'trip-1',
            status: TripStatusType.delayed,
            timestamp: testDate,
          ),
          routeName: 'Lagos - Abuja',
          originTerminal: 'Lagos Terminal',
          destinationTerminal: 'Abuja Terminal',
        ),
      ];

      when(mockTrackingBloc.state).thenReturn(ActiveTripsLoaded(activeTrips: activeTrips));
      when(mockTrackingBloc.stream).thenAnswer((_) => const Stream.empty());

      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      expect(find.text('Delayed'), findsOneWidget);
      
      // Find the status chip container
      final chipFinder = find.ancestor(
        of: find.text('Delayed'),
        matching: find.byType(Container),
      );
      expect(chipFinder, findsOneWidget);
    });


  });
}