import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:mockito/mockito.dart';
import 'package:mockito/annotations.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';

import 'package:pafar_mobile/features/tracking/presentation/screens/trip_tracking_screen.dart';
import 'package:pafar_mobile/features/tracking/presentation/bloc/tracking_bloc.dart';
import 'package:pafar_mobile/features/tracking/presentation/bloc/tracking_state.dart';
import 'package:pafar_mobile/features/tracking/presentation/bloc/tracking_event.dart';
import 'package:pafar_mobile/features/tracking/domain/entities/trip_tracking.dart';
import 'package:pafar_mobile/features/tracking/domain/entities/trip_location.dart';
import 'package:pafar_mobile/features/tracking/domain/entities/trip_status.dart';

import 'trip_tracking_screen_test.mocks.dart';

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
        child: const TripTrackingScreen(bookingId: 'test-booking-id'),
      ),
    );
  }

  group('TripTrackingScreen', () {
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
      const errorMessage = 'Failed to load tracking data';
      when(mockTrackingBloc.state).thenReturn(const TrackingError(message: errorMessage));
      when(mockTrackingBloc.stream).thenAnswer((_) => const Stream.empty());

      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      expect(find.text(errorMessage), findsOneWidget);
      expect(find.text('Try Again'), findsOneWidget);
    });

    testWidgets('should display trip tracking data when loaded', (tester) async {
      // Arrange
      final tripTracking = TripTracking(
        tripId: 'trip-123',
        bookingId: 'booking-123',
        status: TripStatus(
          tripId: 'trip-123',
          status: TripStatusType.inTransit,
          timestamp: testDate,
        ),
        routeName: 'Lagos - Abuja',
        originTerminal: 'Lagos Terminal',
        destinationTerminal: 'Abuja Terminal',
        estimatedArrival: testDate.add(const Duration(hours: 2)),
      );

      when(mockTrackingBloc.state).thenReturn(
        TrackingLoaded(tripTracking: tripTracking),
      );
      when(mockTrackingBloc.stream).thenAnswer((_) => const Stream.empty());

      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      expect(find.text('Lagos - Abuja'), findsOneWidget);
      expect(find.text('Lagos Terminal'), findsOneWidget);
      expect(find.text('Abuja Terminal'), findsOneWidget);
      expect(find.text('In Transit'), findsOneWidget);
    });

    testWidgets('should display Google Map when tracking data is loaded', (tester) async {
      // Arrange
      final tripLocation = TripLocation(
        tripId: 'trip-123',
        latitude: 6.5244,
        longitude: 3.3792,
        timestamp: testDate,
      );

      final tripTracking = TripTracking(
        tripId: 'trip-123',
        bookingId: 'booking-123',
        currentLocation: tripLocation,
        status: TripStatus(
          tripId: 'trip-123',
          status: TripStatusType.inTransit,
          timestamp: testDate,
        ),
        routeName: 'Lagos - Abuja',
        originTerminal: 'Lagos Terminal',
        destinationTerminal: 'Abuja Terminal',
      );

      when(mockTrackingBloc.state).thenReturn(
        TrackingLoaded(
          tripTracking: tripTracking,
          currentLocation: tripLocation,
        ),
      );
      when(mockTrackingBloc.stream).thenAnswer((_) => const Stream.empty());

      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      expect(find.byType(GoogleMap), findsOneWidget);
    });

    testWidgets('should add LoadTripTracking event on init', (tester) async {
      // Arrange
      when(mockTrackingBloc.state).thenReturn(const TrackingInitial());
      when(mockTrackingBloc.stream).thenAnswer((_) => const Stream.empty());

      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      verify(mockTrackingBloc.add(const LoadTripTracking(bookingId: 'test-booking-id')))
          .called(1);
      verify(mockTrackingBloc.add(const CheckLocationPermission())).called(1);
    });

    testWidgets('should show refresh button in app bar', (tester) async {
      // Arrange
      when(mockTrackingBloc.state).thenReturn(const TrackingInitial());
      when(mockTrackingBloc.stream).thenAnswer((_) => const Stream.empty());

      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      expect(find.byIcon(Icons.refresh), findsOneWidget);
    });

    testWidgets('should refresh data when refresh button is tapped', (tester) async {
      // Arrange
      when(mockTrackingBloc.state).thenReturn(const TrackingInitial());
      when(mockTrackingBloc.stream).thenAnswer((_) => const Stream.empty());

      // Act
      await tester.pumpWidget(createWidgetUnderTest());
      await tester.tap(find.byIcon(Icons.refresh));

      // Assert
      verify(mockTrackingBloc.add(const LoadTripTracking(bookingId: 'test-booking-id')))
          .called(2); // Once on init, once on refresh
    });

    testWidgets('should display status bar with correct status', (tester) async {
      // Arrange
      final tripTracking = TripTracking(
        tripId: 'trip-123',
        bookingId: 'booking-123',
        status: TripStatus(
          tripId: 'trip-123',
          status: TripStatusType.boarding,
          message: 'Passengers are boarding',
          timestamp: testDate,
        ),
        routeName: 'Lagos - Abuja',
        originTerminal: 'Lagos Terminal',
        destinationTerminal: 'Abuja Terminal',
      );

      when(mockTrackingBloc.state).thenReturn(
        TrackingLoaded(tripTracking: tripTracking),
      );
      when(mockTrackingBloc.stream).thenAnswer((_) => const Stream.empty());

      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      expect(find.text('Boarding'), findsOneWidget);
      expect(find.text('Passengers are boarding'), findsOneWidget);
      expect(find.byIcon(Icons.directions_bus), findsOneWidget);
    });
  });
}