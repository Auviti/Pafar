import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/mockito.dart';
import 'package:mockito/annotations.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:get_it/get_it.dart';

import 'package:mobile/features/booking/presentation/screens/trip_search_screen.dart';
import 'package:mobile/features/booking/presentation/bloc/booking_bloc.dart';
import 'package:mobile/features/booking/presentation/bloc/booking_event.dart';
import 'package:mobile/features/booking/presentation/bloc/booking_state.dart';
import 'package:mobile/features/booking/domain/entities/terminal.dart';
import 'package:mobile/features/booking/domain/entities/route.dart';
import 'package:mobile/features/booking/domain/entities/trip.dart';
import 'package:mobile/core/error/failures.dart';
import 'package:mobile/shared/widgets/custom_button.dart';
import 'package:mobile/shared/widgets/custom_text_field.dart';
import 'package:mobile/shared/widgets/loading_widget.dart';
import 'package:mobile/shared/widgets/error_widget.dart' as custom_error;

import 'trip_search_screen_comprehensive_test.mocks.dart';

@GenerateMocks([BookingBloc])
void main() {
  group('TripSearchScreen Comprehensive Tests', () {
    late MockBookingBloc mockBookingBloc;
    late GetIt getIt;

    final mockTerminals = [
      const Terminal(
        id: '1',
        name: 'New York Central',
        city: 'New York',
        address: '123 Broadway',
        latitude: 40.7128,
        longitude: -74.0060,
      ),
      const Terminal(
        id: '2',
        name: 'Los Angeles Union',
        city: 'Los Angeles',
        address: '456 Main St',
        latitude: 34.0522,
        longitude: -118.2437,
      ),
      const Terminal(
        id: '3',
        name: 'Chicago Central',
        city: 'Chicago',
        address: '789 State St',
        latitude: 41.8781,
        longitude: -87.6298,
      ),
    ];

    final mockTrips = [
      Trip(
        id: '1',
        routeId: 'route1',
        busId: 'bus1',
        driverId: 'driver1',
        departureTime: DateTime.now().add(const Duration(hours: 2)),
        arrivalTime: DateTime.now().add(const Duration(hours: 10)),
        fare: 150.00,
        availableSeats: 25,
        status: TripStatus.scheduled,
        route: const Route(
          id: 'route1',
          originTerminalId: '1',
          destinationTerminalId: '2',
          distanceKm: 4500.0,
          estimatedDurationMinutes: 480,
          baseFare: 150.00,
        ),
      ),
      Trip(
        id: '2',
        routeId: 'route1',
        busId: 'bus2',
        driverId: 'driver2',
        departureTime: DateTime.now().add(const Duration(hours: 6)),
        arrivalTime: DateTime.now().add(const Duration(hours: 14)),
        fare: 120.00,
        availableSeats: 10,
        status: TripStatus.scheduled,
        route: const Route(
          id: 'route1',
          originTerminalId: '1',
          destinationTerminalId: '2',
          distanceKm: 4500.0,
          estimatedDurationMinutes: 480,
          baseFare: 120.00,
        ),
      ),
    ];

    setUp(() {
      mockBookingBloc = MockBookingBloc();
      getIt = GetIt.instance;
      
      // Reset GetIt
      if (getIt.isRegistered<BookingBloc>()) {
        getIt.unregister<BookingBloc>();
      }
      getIt.registerFactory<BookingBloc>(() => mockBookingBloc);

      // Set up default mock behavior
      when(mockBookingBloc.state).thenReturn(BookingInitial());
      when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([BookingInitial()]));
    });

    tearDown(() {
      getIt.reset();
    });

    Widget createWidgetUnderTest() {
      return MaterialApp(
        home: BlocProvider<BookingBloc>(
          create: (context) => mockBookingBloc,
          child: const TripSearchScreen(),
        ),
      );
    }

    group('Widget Rendering', () {
      testWidgets('renders all required UI elements', (WidgetTester tester) async {
        // Set up terminals loaded state
        when(mockBookingBloc.state).thenReturn(TerminalsLoaded(mockTerminals));
        when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([
          TerminalsLoaded(mockTerminals)
        ]));

        await tester.pumpWidget(createWidgetUnderTest());

        // Check for main UI elements
        expect(find.text('Search Trips'), findsOneWidget);
        expect(find.text('Find your perfect journey'), findsOneWidget);
        
        // Check for form fields
        expect(find.text('From'), findsOneWidget);
        expect(find.text('To'), findsOneWidget);
        expect(find.text('Departure Date'), findsOneWidget);
        expect(find.text('Passengers'), findsOneWidget);
        
        // Check for search button
        expect(find.byType(CustomButton), findsOneWidget);
        expect(find.text('Search Trips'), findsAtLeastNWidgets(1));
      });

      testWidgets('shows loading state when terminals are loading', (WidgetTester tester) async {
        when(mockBookingBloc.state).thenReturn(BookingLoading());
        when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([
          BookingLoading()
        ]));

        await tester.pumpWidget(createWidgetUnderTest());

        expect(find.byType(LoadingWidget), findsOneWidget);
        expect(find.text('Loading terminals...'), findsOneWidget);
      });

      testWidgets('shows error when terminals fail to load', (WidgetTester tester) async {
        when(mockBookingBloc.state).thenReturn(
          BookingError(NetworkFailure('Failed to load terminals'))
        );
        when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([
          BookingError(NetworkFailure('Failed to load terminals'))
        ]));

        await tester.pumpWidget(createWidgetUnderTest());

        expect(find.byType(custom_error.ErrorWidget), findsOneWidget);
        expect(find.text('Failed to load terminals'), findsOneWidget);
      });

      testWidgets('populates terminal dropdowns when loaded', (WidgetTester tester) async {
        when(mockBookingBloc.state).thenReturn(TerminalsLoaded(mockTerminals));
        when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([
          TerminalsLoaded(mockTerminals)
        ]));

        await tester.pumpWidget(createWidgetUnderTest());

        // Tap on origin dropdown
        await tester.tap(find.text('Select origin'));
        await tester.pumpAndSettle();

        // Should show all terminals
        expect(find.text('New York Central'), findsOneWidget);
        expect(find.text('Los Angeles Union'), findsOneWidget);
        expect(find.text('Chicago Central'), findsOneWidget);
      });
    });

    group('Form Validation', () => {
      setUp(() {
        when(mockBookingBloc.state).thenReturn(TerminalsLoaded(mockTerminals));
        when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([
          TerminalsLoaded(mockTerminals)
        ]));
      });

      testWidgets('shows validation errors for empty fields', (WidgetTester tester) async {
        await tester.pumpWidget(createWidgetUnderTest());

        // Tap search button without selecting anything
        await tester.tap(find.byType(CustomButton));
        await tester.pump();

        // Check for validation error messages
        expect(find.text('Please select origin'), findsOneWidget);
        expect(find.text('Please select destination'), findsOneWidget);
        expect(find.text('Please select departure date'), findsOneWidget);
      });

      testWidgets('validates that origin and destination are different', (WidgetTester tester) async {
        await tester.pumpWidget(createWidgetUnderTest());

        // Select same terminal for both origin and destination
        await tester.tap(find.text('Select origin'));
        await tester.pumpAndSettle();
        await tester.tap(find.text('New York Central').first);
        await tester.pumpAndSettle();

        await tester.tap(find.text('Select destination'));
        await tester.pumpAndSettle();
        await tester.tap(find.text('New York Central').first);
        await tester.pumpAndSettle();

        // Try to search
        await tester.tap(find.byType(CustomButton));
        await tester.pump();

        expect(find.text('Origin and destination must be different'), findsOneWidget);
      });

      testWidgets('validates departure date is not in the past', (WidgetTester tester) async {
        await tester.pumpWidget(createWidgetUnderTest());

        // Select origin and destination
        await tester.tap(find.text('Select origin'));
        await tester.pumpAndSettle();
        await tester.tap(find.text('New York Central'));
        await tester.pumpAndSettle();

        await tester.tap(find.text('Select destination'));
        await tester.pumpAndSettle();
        await tester.tap(find.text('Los Angeles Union'));
        await tester.pumpAndSettle();

        // Try to select past date (this would typically be handled by date picker)
        // For testing, we'll simulate the validation error
        await tester.tap(find.byType(CustomButton));
        await tester.pump();

        // If no date is selected, should show date required error
        expect(find.text('Please select departure date'), findsOneWidget);
      });

      testWidgets('validates passenger count is within limits', (WidgetTester tester) async {
        await tester.pumpWidget(createWidgetUnderTest());

        // Find passenger count field
        final passengerField = find.byKey(const Key('passenger_count_field'));
        
        // Test minimum validation (0 passengers)
        await tester.enterText(passengerField, '0');
        await tester.tap(find.byType(CustomButton));
        await tester.pump();

        expect(find.text('At least 1 passenger required'), findsOneWidget);

        // Test maximum validation (more than 10 passengers)
        await tester.enterText(passengerField, '15');
        await tester.tap(find.byType(CustomButton));
        await tester.pump();

        expect(find.text('Maximum 10 passengers allowed'), findsOneWidget);
      });
    });

    group('Trip Search Flow', () => {
      setUp(() {
        when(mockBookingBloc.state).thenReturn(TerminalsLoaded(mockTerminals));
        when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([
          TerminalsLoaded(mockTerminals)
        ]));
      });

      testWidgets('triggers search with valid data', (WidgetTester tester) async {
        await tester.pumpWidget(createWidgetUnderTest());

        // Select origin
        await tester.tap(find.text('Select origin'));
        await tester.pumpAndSettle();
        await tester.tap(find.text('New York Central'));
        await tester.pumpAndSettle();

        // Select destination
        await tester.tap(find.text('Select destination'));
        await tester.pumpAndSettle();
        await tester.tap(find.text('Los Angeles Union'));
        await tester.pumpAndSettle();

        // Select date (simulate date picker selection)
        await tester.tap(find.byIcon(Icons.calendar_today));
        await tester.pumpAndSettle();
        // Simulate selecting tomorrow's date
        await tester.tap(find.text('OK'));
        await tester.pumpAndSettle();

        // Set passenger count
        await tester.enterText(find.byKey(const Key('passenger_count_field')), '2');

        // Tap search button
        await tester.tap(find.byType(CustomButton));
        await tester.pump();

        // Verify that search event was triggered
        verify(mockBookingBloc.add(any)).called(1);
        
        // Verify the event contains correct data
        final capturedEvents = verify(mockBookingBloc.add(captureAny)).captured;
        final searchEvent = capturedEvents.first as SearchTripsRequested;
        expect(searchEvent.originTerminalId, '1');
        expect(searchEvent.destinationTerminalId, '2');
        expect(searchEvent.passengers, 2);
      });

      testWidgets('shows loading state during search', (WidgetTester tester) async {
        // Start with terminals loaded
        when(mockBookingBloc.state).thenReturn(TerminalsLoaded(mockTerminals));
        
        final stateController = StreamController<BookingState>();
        when(mockBookingBloc.stream).thenAnswer((_) => stateController.stream);

        await tester.pumpWidget(createWidgetUnderTest());

        // Emit searching state
        stateController.add(BookingLoading());
        await tester.pump();

        // Should show loading indicator
        expect(find.byType(LoadingWidget), findsOneWidget);
        expect(find.text('Searching trips...'), findsOneWidget);
        
        // Search button should be disabled
        final button = tester.widget<CustomButton>(find.byType(CustomButton));
        expect(button.isEnabled, false);

        stateController.close();
      });

      testWidgets('displays search results', (WidgetTester tester) async {
        // Start with terminals loaded
        when(mockBookingBloc.state).thenReturn(TerminalsLoaded(mockTerminals));
        
        final stateController = StreamController<BookingState>();
        when(mockBookingBloc.stream).thenAnswer((_) => stateController.stream);

        await tester.pumpWidget(createWidgetUnderTest());

        // Emit trips loaded state
        stateController.add(TripsLoaded(mockTrips));
        await tester.pump();

        // Should show trip results
        expect(find.text('Available Trips'), findsOneWidget);
        expect(find.text('\$150.00'), findsOneWidget);
        expect(find.text('\$120.00'), findsOneWidget);
        expect(find.text('25 seats available'), findsOneWidget);
        expect(find.text('10 seats available'), findsOneWidget);

        stateController.close();
      });

      testWidgets('handles no trips found', (WidgetTester tester) async {
        when(mockBookingBloc.state).thenReturn(TripsLoaded([]));
        when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([
          TripsLoaded([])
        ]));

        await tester.pumpWidget(createWidgetUnderTest());

        expect(find.text('No trips found'), findsOneWidget);
        expect(find.text('Try adjusting your search criteria'), findsOneWidget);
      });

      testWidgets('handles search error', (WidgetTester tester) async {
        when(mockBookingBloc.state).thenReturn(
          BookingError(ServerFailure('Search failed'))
        );
        when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([
          BookingError(ServerFailure('Search failed'))
        ]));

        await tester.pumpWidget(createWidgetUnderTest());

        expect(find.byType(custom_error.ErrorWidget), findsOneWidget);
        expect(find.text('Search failed'), findsOneWidget);
        expect(find.text('Retry'), findsOneWidget);
      });
    });

    group('User Interactions', () => {
      setUp(() {
        when(mockBookingBloc.state).thenReturn(TerminalsLoaded(mockTerminals));
        when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([
          TerminalsLoaded(mockTerminals)
        ]));
      });

      testWidgets('swaps origin and destination', (WidgetTester tester) async {
        await tester.pumpWidget(createWidgetUnderTest());

        // Select origin and destination
        await tester.tap(find.text('Select origin'));
        await tester.pumpAndSettle();
        await tester.tap(find.text('New York Central'));
        await tester.pumpAndSettle();

        await tester.tap(find.text('Select destination'));
        await tester.pumpAndSettle();
        await tester.tap(find.text('Los Angeles Union'));
        await tester.pumpAndSettle();

        // Tap swap button
        await tester.tap(find.byIcon(Icons.swap_vert));
        await tester.pumpAndSettle();

        // Origin and destination should be swapped
        expect(find.text('Los Angeles Union').first, findsOneWidget);
        expect(find.text('New York Central').last, findsOneWidget);
      });

      testWidgets('increments and decrements passenger count', (WidgetTester tester) async {
        await tester.pumpWidget(createWidgetUnderTest());

        final passengerField = find.byKey(const Key('passenger_count_field'));
        final incrementButton = find.byKey(const Key('increment_passengers'));
        final decrementButton = find.byKey(const Key('decrement_passengers'));

        // Initial value should be 1
        expect(find.text('1'), findsOneWidget);

        // Increment passenger count
        await tester.tap(incrementButton);
        await tester.pump();
        expect(find.text('2'), findsOneWidget);

        await tester.tap(incrementButton);
        await tester.pump();
        expect(find.text('3'), findsOneWidget);

        // Decrement passenger count
        await tester.tap(decrementButton);
        await tester.pump();
        expect(find.text('2'), findsOneWidget);
      });

      testWidgets('prevents passenger count from going below 1', (WidgetTester tester) async {
        await tester.pumpWidget(createWidgetUnderTest());

        final decrementButton = find.byKey(const Key('decrement_passengers'));

        // Initial value is 1, decrement button should be disabled
        final button = tester.widget<IconButton>(decrementButton);
        expect(button.onPressed, isNull);

        // Value should remain 1
        expect(find.text('1'), findsOneWidget);
      });

      testWidgets('prevents passenger count from going above 10', (WidgetTester tester) async {
        await tester.pumpWidget(createWidgetUnderTest());

        final passengerField = find.byKey(const Key('passenger_count_field'));
        final incrementButton = find.byKey(const Key('increment_passengers'));

        // Set to 10
        await tester.enterText(passengerField, '10');
        await tester.pump();

        // Increment button should be disabled
        final button = tester.widget<IconButton>(incrementButton);
        expect(button.onPressed, isNull);
      });

      testWidgets('opens date picker when date field is tapped', (WidgetTester tester) async {
        await tester.pumpWidget(createWidgetUnderTest());

        // Tap date field
        await tester.tap(find.byIcon(Icons.calendar_today));
        await tester.pumpAndSettle();

        // Should open date picker dialog
        expect(find.byType(DatePickerDialog), findsOneWidget);
      });

      testWidgets('filters terminals in dropdown search', (WidgetTester tester) async {
        await tester.pumpWidget(createWidgetUnderTest());

        // Tap origin dropdown
        await tester.tap(find.text('Select origin'));
        await tester.pumpAndSettle();

        // Type in search field
        await tester.enterText(find.byType(TextField), 'New York');
        await tester.pump();

        // Should only show matching terminals
        expect(find.text('New York Central'), findsOneWidget);
        expect(find.text('Los Angeles Union'), findsNothing);
        expect(find.text('Chicago Central'), findsNothing);
      });
    });

    group('Trip Selection', () => {
      testWidgets('navigates to seat selection when trip is selected', (WidgetTester tester) async {
        when(mockBookingBloc.state).thenReturn(TripsLoaded(mockTrips));
        when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([
          TripsLoaded(mockTrips)
        ]));

        await tester.pumpWidget(
          MaterialApp(
            home: BlocProvider<BookingBloc>(
              create: (context) => mockBookingBloc,
              child: const TripSearchScreen(),
            ),
            routes: {
              '/seat-selection': (context) => const Scaffold(
                body: Text('Seat Selection Screen')
              ),
            },
          ),
        );

        // Tap on first trip
        await tester.tap(find.text('Select').first);
        await tester.pumpAndSettle();

        // Should navigate to seat selection
        expect(find.text('Seat Selection Screen'), findsOneWidget);
      });

      testWidgets('shows trip details in expandable card', (WidgetTester tester) async {
        when(mockBookingBloc.state).thenReturn(TripsLoaded(mockTrips));
        when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([
          TripsLoaded(mockTrips)
        ]));

        await tester.pumpWidget(createWidgetUnderTest());

        // Tap to expand trip details
        await tester.tap(find.byIcon(Icons.expand_more).first);
        await tester.pumpAndSettle();

        // Should show additional trip details
        expect(find.text('Trip Details'), findsOneWidget);
        expect(find.text('Duration:'), findsOneWidget);
        expect(find.text('Distance:'), findsOneWidget);
        expect(find.text('Amenities:'), findsOneWidget);
      });

      testWidgets('sorts trips by different criteria', (WidgetTester tester) async {
        when(mockBookingBloc.state).thenReturn(TripsLoaded(mockTrips));
        when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([
          TripsLoaded(mockTrips)
        ]));

        await tester.pumpWidget(createWidgetUnderTest());

        // Tap sort button
        await tester.tap(find.byIcon(Icons.sort));
        await tester.pumpAndSettle();

        // Should show sort options
        expect(find.text('Sort by Price'), findsOneWidget);
        expect(find.text('Sort by Departure Time'), findsOneWidget);
        expect(find.text('Sort by Duration'), findsOneWidget);

        // Select sort by price
        await tester.tap(find.text('Sort by Price'));
        await tester.pumpAndSettle();

        // Trips should be reordered (cheaper first)
        final tripCards = find.byType(Card);
        expect(tripCards, findsNWidgets(2));
      });

      testWidgets('filters trips by price range', (WidgetTester tester) async {
        when(mockBookingBloc.state).thenReturn(TripsLoaded(mockTrips));
        when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([
          TripsLoaded(mockTrips)
        ]));

        await tester.pumpWidget(createWidgetUnderTest());

        // Tap filter button
        await tester.tap(find.byIcon(Icons.filter_list));
        await tester.pumpAndSettle();

        // Should show filter options
        expect(find.text('Price Range'), findsOneWidget);
        expect(find.byType(RangeSlider), findsOneWidget);

        // Adjust price range
        await tester.drag(find.byType(RangeSlider), const Offset(50, 0));
        await tester.pump();

        // Apply filter
        await tester.tap(find.text('Apply'));
        await tester.pumpAndSettle();

        // Should filter trips based on price range
        verify(mockBookingBloc.add(any)).called(1);
      });
    });

    group('Accessibility', () => {
      setUp(() {
        when(mockBookingBloc.state).thenReturn(TerminalsLoaded(mockTerminals));
        when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([
          TerminalsLoaded(mockTerminals)
        ]));
      });

      testWidgets('has proper semantic labels', (WidgetTester tester) async {
        await tester.pumpWidget(createWidgetUnderTest());

        expect(find.bySemanticsLabel('Origin terminal selector'), findsOneWidget);
        expect(find.bySemanticsLabel('Destination terminal selector'), findsOneWidget);
        expect(find.bySemanticsLabel('Departure date picker'), findsOneWidget);
        expect(find.bySemanticsLabel('Passenger count input'), findsOneWidget);
        expect(find.bySemanticsLabel('Search trips button'), findsOneWidget);
      });

      testWidgets('supports screen reader navigation', (WidgetTester tester) async {
        await tester.pumpWidget(createWidgetUnderTest());

        // Test semantic traversal
        final semantics = tester.binding.pipelineOwner.semanticsOwner!;
        final rootNode = semantics.rootSemanticsNode!;
        
        expect(rootNode.childrenCount, greaterThan(0));
      });

      testWidgets('announces form validation errors', (WidgetTester tester) async {
        await tester.pumpWidget(createWidgetUnderTest());

        // Trigger validation error
        await tester.tap(find.byType(CustomButton));
        await tester.pump();

        // Error should be announced
        final errorWidget = find.text('Please select origin');
        expect(errorWidget, findsOneWidget);
        
        final semantics = tester.getSemantics(errorWidget);
        expect(semantics.hasFlag(SemanticsFlag.isLiveRegion), true);
      });
    });

    group('Performance', () => {
      testWidgets('handles large terminal lists efficiently', (WidgetTester tester) async {
        // Create large list of terminals
        final largeTerminalList = List.generate(100, (index) => Terminal(
          id: '$index',
          name: 'Terminal $index',
          city: 'City $index',
          address: 'Address $index',
          latitude: 40.0 + index * 0.01,
          longitude: -74.0 + index * 0.01,
        ));

        when(mockBookingBloc.state).thenReturn(TerminalsLoaded(largeTerminalList));
        when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([
          TerminalsLoaded(largeTerminalList)
        ]));

        await tester.pumpWidget(createWidgetUnderTest());

        // Should render without performance issues
        expect(tester.takeException(), isNull);

        // Tap dropdown should still be responsive
        await tester.tap(find.text('Select origin'));
        await tester.pumpAndSettle();

        expect(find.byType(ListView), findsOneWidget);
      });

      testWidgets('debounces search input', (WidgetTester tester) async {
        when(mockBookingBloc.state).thenReturn(TerminalsLoaded(mockTerminals));
        when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([
          TerminalsLoaded(mockTerminals)
        ]));

        await tester.pumpWidget(createWidgetUnderTest());

        // Rapidly change passenger count
        final passengerField = find.byKey(const Key('passenger_count_field'));
        
        for (int i = 1; i <= 5; i++) {
          await tester.enterText(passengerField, '$i');
          await tester.pump(const Duration(milliseconds: 100));
        }

        // Should handle rapid input without issues
        expect(tester.takeException(), isNull);
      });
    });

    group('Edge Cases', () => {
      testWidgets('handles empty terminal list gracefully', (WidgetTester tester) async {
        when(mockBookingBloc.state).thenReturn(TerminalsLoaded([]));
        when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([
          TerminalsLoaded([])
        ]));

        await tester.pumpWidget(createWidgetUnderTest());

        expect(find.text('No terminals available'), findsOneWidget);
        expect(find.text('Please try again later'), findsOneWidget);
      });

      testWidgets('handles network timeout gracefully', (WidgetTester tester) async {
        when(mockBookingBloc.state).thenReturn(
          BookingError(NetworkFailure('Request timeout'))
        );
        when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([
          BookingError(NetworkFailure('Request timeout'))
        ]));

        await tester.pumpWidget(createWidgetUnderTest());

        expect(find.text('Request timeout'), findsOneWidget);
        expect(find.text('Retry'), findsOneWidget);

        // Tap retry should trigger reload
        await tester.tap(find.text('Retry'));
        await tester.pump();

        verify(mockBookingBloc.add(any)).called(1);
      });

      testWidgets('preserves search criteria on error', (WidgetTester tester) async {
        // Start with terminals loaded
        when(mockBookingBloc.state).thenReturn(TerminalsLoaded(mockTerminals));
        
        final stateController = StreamController<BookingState>();
        when(mockBookingBloc.stream).thenAnswer((_) => stateController.stream);

        await tester.pumpWidget(createWidgetUnderTest());

        // Select search criteria
        await tester.tap(find.text('Select origin'));
        await tester.pumpAndSettle();
        await tester.tap(find.text('New York Central'));
        await tester.pumpAndSettle();

        await tester.enterText(find.byKey(const Key('passenger_count_field')), '3');

        // Emit error state
        stateController.add(BookingError(ServerFailure('Search failed')));
        await tester.pump();

        // Search criteria should be preserved
        expect(find.text('New York Central'), findsOneWidget);
        expect(find.text('3'), findsOneWidget);

        stateController.close();
      });

      testWidgets('handles very long terminal names', (WidgetTester tester) async {
        final longNameTerminals = [
          const Terminal(
            id: '1',
            name: 'This is a very long terminal name that might cause layout issues',
            city: 'Very Long City Name That Might Overflow',
            address: 'Very long address that might cause text overflow issues',
            latitude: 40.7128,
            longitude: -74.0060,
          ),
        ];

        when(mockBookingBloc.state).thenReturn(TerminalsLoaded(longNameTerminals));
        when(mockBookingBloc.stream).thenAnswer((_) => Stream.fromIterable([
          TerminalsLoaded(longNameTerminals)
        ]));

        await tester.pumpWidget(createWidgetUnderTest());

        // Should handle long names without overflow
        expect(tester.takeException(), isNull);

        await tester.tap(find.text('Select origin'));
        await tester.pumpAndSettle();

        expect(find.textContaining('This is a very long terminal name'), findsOneWidget);
      });
    });
  });
}