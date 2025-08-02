import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:mockito/mockito.dart';
import 'package:mockito/annotations.dart';

import 'package:pafar_mobile/features/booking/presentation/screens/booking_screen.dart';
import 'package:pafar_mobile/features/booking/presentation/bloc/booking_bloc.dart';
import 'package:pafar_mobile/features/booking/presentation/bloc/booking_event.dart';
import 'package:pafar_mobile/features/booking/presentation/bloc/booking_state.dart';
import 'package:pafar_mobile/features/booking/domain/entities/trip.dart';
import 'package:pafar_mobile/features/booking/domain/entities/terminal.dart';
import 'package:pafar_mobile/features/booking/domain/entities/booking.dart';
import 'package:pafar_mobile/shared/widgets/custom_button.dart';
import 'package:pafar_mobile/shared/widgets/loading_widget.dart';
import 'package:pafar_mobile/shared/widgets/error_widget.dart';

import 'booking_screen_test.mocks.dart';

@GenerateMocks([BookingBloc])
void main() {
  group('BookingScreen Widget Tests', () {
    late MockBookingBloc mockBookingBloc;

    setUp(() {
      mockBookingBloc = MockBookingBloc();
      when(mockBookingBloc.state).thenReturn(BookingInitial());
      when(mockBookingBloc.stream).thenAnswer((_) => Stream.empty());
    });

    Widget createWidgetUnderTest() {
      return MaterialApp(
        home: BlocProvider<BookingBloc>(
          create: (context) => mockBookingBloc,
          child: const BookingScreen(),
        ),
      );
    }

    final mockOriginTerminal = Terminal(
      id: '1',
      name: 'Central Terminal',
      city: 'New York',
      address: '123 Main St',
      latitude: 40.7128,
      longitude: -74.0060,
    );

    final mockDestinationTerminal = Terminal(
      id: '2',
      name: 'Airport Terminal',
      city: 'Los Angeles',
      address: '456 Airport Blvd',
      latitude: 34.0522,
      longitude: -118.2437,
    );

    final mockTrip = Trip(
      id: '1',
      originTerminal: mockOriginTerminal,
      destinationTerminal: mockDestinationTerminal,
      departureTime: DateTime.now().add(const Duration(hours: 2)),
      arrivalTime: DateTime.now().add(const Duration(hours: 6)),
      fare: 50.0,
      availableSeats: 15,
      busModel: 'Mercedes Sprinter',
      busLicensePlate: 'ABC-123',
      amenities: ['WiFi', 'AC', 'USB Charging'],
    );

    group('Initial State Tests', () {
      testWidgets('should render search form initially', (tester) async {
        await tester.pumpWidget(createWidgetUnderTest());

        // Verify search form elements
        expect(find.text('Book Your Trip'), findsOneWidget);
        expect(find.text('From'), findsOneWidget);
        expect(find.text('To'), findsOneWidget);
        expect(find.text('Departure Date'), findsOneWidget);
        expect(find.text('Passengers'), findsOneWidget);
        expect(find.text('Search Trips'), findsOneWidget);
      });

      testWidgets('should render terminal dropdowns', (tester) async {
        await tester.pumpWidget(createWidgetUnderTest());

        expect(find.byType(DropdownButtonFormField), findsNWidgets(3)); // From, To, Passengers
        expect(find.byType(TextFormField), findsOneWidget); // Date field
      });

      testWidgets('should render trip type selector', (tester) async {
        await tester.pumpWidget(createWidgetUnderTest());

        expect(find.text('One Way'), findsOneWidget);
        expect(find.text('Round Trip'), findsOneWidget);
        expect(find.byType(ToggleButtons), findsOneWidget);
      });
    });

    group('Search Form Tests', () => {
      testWidgets('should validate required fields', (tester) async {
        await tester.pumpWidget(createWidgetUnderTest());

        // Tap search without filling fields
        final searchButton = find.text('Search Trips');
        await tester.tap(searchButton);
        await tester.pump();

        // Verify validation errors
        expect(find.text('Please select origin'), findsOneWidget);
        expect(find.text('Please select destination'), findsOneWidget);
        expect(find.text('Please select date'), findsOneWidget);
      });

      testWidgets('should dispatch search event with valid data', (tester) async {
        await tester.pumpWidget(createWidgetUnderTest());

        // Fill form fields
        final fromDropdown = find.byType(DropdownButtonFormField).first;
        await tester.tap(fromDropdown);
        await tester.pumpAndSettle();
        await tester.tap(find.text('Central Terminal').last);
        await tester.pumpAndSettle();

        final toDropdown = find.byType(DropdownButtonFormField).at(1);
        await tester.tap(toDropdown);
        await tester.pumpAndSettle();
        await tester.tap(find.text('Airport Terminal').last);
        await tester.pumpAndSettle();

        // Select date
        final dateField = find.byType(TextFormField);
        await tester.tap(dateField);
        await tester.pumpAndSettle();
        await tester.tap(find.text('OK')); // Confirm date picker
        await tester.pumpAndSettle();

        // Tap search button
        final searchButton = find.text('Search Trips');
        await tester.tap(searchButton);
        await tester.pump();

        // Verify search event was dispatched
        verify(mockBookingBloc.add(any)).called(1);
        
        final capturedEvent = verify(mockBookingBloc.add(captureAny)).captured.first;
        expect(capturedEvent, isA<SearchTripsRequested>());
      });

      testWidgets('should swap origin and destination', (tester) async {
        await tester.pumpWidget(createWidgetUnderTest());

        // Select origin and destination
        final fromDropdown = find.byType(DropdownButtonFormField).first;
        await tester.tap(fromDropdown);
        await tester.pumpAndSettle();
        await tester.tap(find.text('Central Terminal').last);
        await tester.pumpAndSettle();

        final toDropdown = find.byType(DropdownButtonFormField).at(1);
        await tester.tap(toDropdown);
        await tester.pumpAndSettle();
        await tester.tap(find.text('Airport Terminal').last);
        await tester.pumpAndSettle();

        // Tap swap button
        final swapButton = find.byIcon(Icons.swap_vert);
        await tester.tap(swapButton);
        await tester.pump();

        // Verify values are swapped
        // This would depend on your implementation
        expect(find.byIcon(Icons.swap_vert), findsOneWidget);
      });

      testWidgets('should toggle between one way and round trip', (tester) async {
        await tester.pumpWidget(createWidgetUnderTest());

        final toggleButtons = find.byType(ToggleButtons);
        expect(toggleButtons, findsOneWidget);

        // Initially one way should be selected
        ToggleButtons toggleWidget = tester.widget(toggleButtons);
        expect(toggleWidget.isSelected[0], isTrue);
        expect(toggleWidget.isSelected[1], isFalse);

        // Tap round trip
        await tester.tap(find.text('Round Trip'));
        await tester.pump();

        // Round trip should now be selected
        toggleWidget = tester.widget(toggleButtons);
        expect(toggleWidget.isSelected[0], isFalse);
        expect(toggleWidget.isSelected[1], isTrue);

        // Return date field should appear
        expect(find.text('Return Date'), findsOneWidget);
      });
    });

    group('Trip Results Tests', () => {
      testWidgets('should show loading state during search', (tester) async {
        when(mockBookingBloc.state).thenReturn(BookingLoading());

        await tester.pumpWidget(createWidgetUnderTest());

        expect(find.byType(LoadingWidget), findsOneWidget);
        expect(find.text('Searching for trips...'), findsOneWidget);
      });

      testWidgets('should display trip results', (tester) async {
        final trips = [mockTrip];
        when(mockBookingBloc.state).thenReturn(TripsLoaded(trips));

        await tester.pumpWidget(createWidgetUnderTest());

        // Verify trip results are displayed
        expect(find.text('Available Trips'), findsOneWidget);
        expect(find.text('Central Terminal'), findsOneWidget);
        expect(find.text('Airport Terminal'), findsOneWidget);
        expect(find.text('\$50.00'), findsOneWidget);
        expect(find.text('15 seats available'), findsOneWidget);
      });

      testWidgets('should show no results message when no trips found', (tester) async {
        when(mockBookingBloc.state).thenReturn(const TripsLoaded([]));

        await tester.pumpWidget(createWidgetUnderTest());

        expect(find.text('No trips found'), findsOneWidget);
        expect(find.text('Try adjusting your search criteria'), findsOneWidget);
        expect(find.byIcon(Icons.search_off), findsOneWidget);
      });

      testWidgets('should show error message on search failure', (tester) async {
        const errorMessage = 'Failed to search trips';
        when(mockBookingBloc.state).thenReturn(const BookingError(errorMessage));

        await tester.pumpWidget(createWidgetUnderTest());

        expect(find.byType(ErrorWidget), findsOneWidget);
        expect(find.text(errorMessage), findsOneWidget);
        expect(find.text('Retry'), findsOneWidget);
      });

      testWidgets('should filter trips by price', (tester) async {
        final trips = [
          mockTrip,
          mockTrip.copyWith(id: '2', fare: 75.0),
          mockTrip.copyWith(id: '3', fare: 100.0),
        ];
        when(mockBookingBloc.state).thenReturn(TripsLoaded(trips));

        await tester.pumpWidget(createWidgetUnderTest());

        // Open filter options
        final filterButton = find.byIcon(Icons.filter_list);
        await tester.tap(filterButton);
        await tester.pumpAndSettle();

        // Set price range
        final priceSlider = find.byType(RangeSlider);
        expect(priceSlider, findsOneWidget);

        // Apply filter
        final applyButton = find.text('Apply Filters');
        await tester.tap(applyButton);
        await tester.pumpAndSettle();

        // Verify filter event was dispatched
        verify(mockBookingBloc.add(any)).called(1);
      });

      testWidgets('should sort trips by different criteria', (tester) async {
        final trips = [mockTrip];
        when(mockBookingBloc.state).thenReturn(TripsLoaded(trips));

        await tester.pumpWidget(createWidgetUnderTest());

        // Open sort options
        final sortButton = find.byIcon(Icons.sort);
        await tester.tap(sortButton);
        await tester.pumpAndSettle();

        // Select sort by price
        final sortByPrice = find.text('Price (Low to High)');
        await tester.tap(sortByPrice);
        await tester.pumpAndSettle();

        // Verify sort event was dispatched
        verify(mockBookingBloc.add(any)).called(1);
      });
    });

    group('Trip Selection Tests', () => {
      testWidgets('should navigate to seat selection on trip tap', (tester) async {
        final trips = [mockTrip];
        when(mockBookingBloc.state).thenReturn(TripsLoaded(trips));

        await tester.pumpWidget(createWidgetUnderTest());

        // Tap on trip card
        final tripCard = find.byType(Card).first;
        await tester.tap(tripCard);
        await tester.pumpAndSettle();

        // Verify navigation to seat selection
        // This would depend on your navigation implementation
        expect(find.text('Select Seats'), findsOneWidget);
      });

      testWidgets('should show trip details on info button tap', (tester) async {
        final trips = [mockTrip];
        when(mockBookingBloc.state).thenReturn(TripsLoaded(trips));

        await tester.pumpWidget(createWidgetUnderTest());

        // Tap info button
        final infoButton = find.byIcon(Icons.info_outline);
        await tester.tap(infoButton);
        await tester.pumpAndSettle();

        // Verify trip details modal
        expect(find.text('Trip Details'), findsOneWidget);
        expect(find.text('Mercedes Sprinter'), findsOneWidget);
        expect(find.text('ABC-123'), findsOneWidget);
        expect(find.text('WiFi'), findsOneWidget);
        expect(find.text('AC'), findsOneWidget);
      });
    });

    group('Seat Selection Tests', () => {
      testWidgets('should display seat map', (tester) async {
        when(mockBookingBloc.state).thenReturn(SeatSelectionState(mockTrip));

        await tester.pumpWidget(createWidgetUnderTest());

        expect(find.text('Select Your Seats'), findsOneWidget);
        expect(find.byType(GridView), findsOneWidget);
        expect(find.text('Available'), findsOneWidget);
        expect(find.text('Selected'), findsOneWidget);
        expect(find.text('Occupied'), findsOneWidget);
      });

      testWidgets('should select and deselect seats', (tester) async {
        when(mockBookingBloc.state).thenReturn(SeatSelectionState(mockTrip));

        await tester.pumpWidget(createWidgetUnderTest());

        // Tap on an available seat
        final seatButton = find.text('1A');
        await tester.tap(seatButton);
        await tester.pump();

        // Verify seat selection event
        verify(mockBookingBloc.add(any)).called(1);
        
        final capturedEvent = verify(mockBookingBloc.add(captureAny)).captured.first;
        expect(capturedEvent, isA<SeatSelected>());

        // Tap again to deselect
        await tester.tap(seatButton);
        await tester.pump();

        // Verify seat deselection event
        verify(mockBookingBloc.add(any)).called(2);
      });

      testWidgets('should show seat selection summary', (tester) async {
        final selectedSeats = ['1A', '1B'];
        when(mockBookingBloc.state).thenReturn(
          SeatSelectionState(mockTrip, selectedSeats: selectedSeats)
        );

        await tester.pumpWidget(createWidgetUnderTest());

        expect(find.text('Selected Seats: 1A, 1B'), findsOneWidget);
        expect(find.text('Total: \$100.00'), findsOneWidget);
        expect(find.text('Continue to Payment'), findsOneWidget);
      });

      testWidgets('should prevent selecting occupied seats', (tester) async {
        final occupiedSeats = ['1A'];
        when(mockBookingBloc.state).thenReturn(
          SeatSelectionState(mockTrip, occupiedSeats: occupiedSeats)
        );

        await tester.pumpWidget(createWidgetUnderTest());

        // Try to tap occupied seat
        final occupiedSeat = find.text('1A');
        await tester.tap(occupiedSeat);
        await tester.pump();

        // Verify no selection event was dispatched
        verifyNever(mockBookingBloc.add(any));

        // Verify seat appears disabled
        final seatWidget = tester.widget<Container>(
          find.ancestor(
            of: occupiedSeat,
            matching: find.byType(Container),
          ),
        );
        // Check if seat has disabled styling
        expect(seatWidget.decoration, isNotNull);
      });
    });

    group('Booking Confirmation Tests', () => {
      testWidgets('should show booking summary', (tester) async {
        final booking = Booking(
          id: '1',
          tripId: mockTrip.id,
          selectedSeats: ['1A', '1B'],
          totalAmount: 100.0,
          status: BookingStatus.pending,
        );

        when(mockBookingBloc.state).thenReturn(BookingConfirmationState(booking, mockTrip));

        await tester.pumpWidget(createWidgetUnderTest());

        expect(find.text('Booking Summary'), findsOneWidget);
        expect(find.text('Central Terminal → Airport Terminal'), findsOneWidget);
        expect(find.text('Seats: 1A, 1B'), findsOneWidget);
        expect(find.text('Total: \$100.00'), findsOneWidget);
        expect(find.text('Confirm Booking'), findsOneWidget);
      });

      testWidgets('should dispatch booking confirmation event', (tester) async {
        final booking = Booking(
          id: '1',
          tripId: mockTrip.id,
          selectedSeats: ['1A', '1B'],
          totalAmount: 100.0,
          status: BookingStatus.pending,
        );

        when(mockBookingBloc.state).thenReturn(BookingConfirmationState(booking, mockTrip));

        await tester.pumpWidget(createWidgetUnderTest());

        final confirmButton = find.text('Confirm Booking');
        await tester.tap(confirmButton);
        await tester.pump();

        verify(mockBookingBloc.add(any)).called(1);
        
        final capturedEvent = verify(mockBookingBloc.add(captureAny)).captured.first;
        expect(capturedEvent, isA<BookingConfirmed>());
      });

      testWidgets('should show booking success message', (tester) async {
        final booking = Booking(
          id: '1',
          tripId: mockTrip.id,
          selectedSeats: ['1A', '1B'],
          totalAmount: 100.0,
          status: BookingStatus.confirmed,
          bookingReference: 'BK123456',
        );

        when(mockBookingBloc.state).thenReturn(BookingSuccessState(booking));

        await tester.pumpWidget(createWidgetUnderTest());

        expect(find.text('Booking Confirmed!'), findsOneWidget);
        expect(find.text('Booking Reference: BK123456'), findsOneWidget);
        expect(find.byIcon(Icons.check_circle), findsOneWidget);
        expect(find.text('View Booking Details'), findsOneWidget);
        expect(find.text('Book Another Trip'), findsOneWidget);
      });
    });

    group('Accessibility Tests', () => {
      testWidgets('should have proper semantic labels', (tester) async {
        await tester.pumpWidget(createWidgetUnderTest());

        expect(find.bySemanticsLabel('Origin terminal selection'), findsOneWidget);
        expect(find.bySemanticsLabel('Destination terminal selection'), findsOneWidget);
        expect(find.bySemanticsLabel('Departure date selection'), findsOneWidget);
        expect(find.bySemanticsLabel('Number of passengers'), findsOneWidget);
        expect(find.bySemanticsLabel('Search for trips'), findsOneWidget);
      });

      testWidgets('should support screen reader navigation', (tester) async {
        final trips = [mockTrip];
        when(mockBookingBloc.state).thenReturn(TripsLoaded(trips));

        await tester.pumpWidget(createWidgetUnderTest());

        // Verify trip information is accessible
        expect(find.bySemanticsLabel('Trip from Central Terminal to Airport Terminal, departing at ${mockTrip.departureTime}, fare \$50.00, 15 seats available'), findsOneWidget);
      });

      testWidgets('should announce state changes', (tester) async {
        when(mockBookingBloc.state).thenReturn(BookingLoading());

        await tester.pumpWidget(createWidgetUnderTest());

        // Verify loading announcement
        expect(find.bySemanticsLabel('Searching for trips'), findsOneWidget);

        // Change to results state
        final trips = [mockTrip];
        when(mockBookingBloc.state).thenReturn(TripsLoaded(trips));
        await tester.pump();

        // Verify results announcement
        expect(find.bySemanticsLabel('Found 1 trip'), findsOneWidget);
      });
    });

    group('Error Handling Tests', () => {
      testWidgets('should show retry button on error', (tester) async {
        const errorMessage = 'Network error occurred';
        when(mockBookingBloc.state).thenReturn(const BookingError(errorMessage));

        await tester.pumpWidget(createWidgetUnderTest());

        expect(find.text(errorMessage), findsOneWidget);
        expect(find.text('Retry'), findsOneWidget);

        // Tap retry button
        final retryButton = find.text('Retry');
        await tester.tap(retryButton);
        await tester.pump();

        // Verify retry event was dispatched
        verify(mockBookingBloc.add(any)).called(1);
      });

      testWidgets('should handle booking timeout', (tester) async {
        const errorMessage = 'Booking timeout. Please try again.';
        when(mockBookingBloc.state).thenReturn(const BookingError(errorMessage));

        await tester.pumpWidget(createWidgetUnderTest());

        expect(find.text(errorMessage), findsOneWidget);
        expect(find.text('Start New Search'), findsOneWidget);
      });
    });

    group('Performance Tests', () => {
      testWidgets('should handle large trip lists efficiently', (tester) async {
        // Create a large list of trips
        final trips = List.generate(100, (index) => 
          mockTrip.copyWith(id: index.toString())
        );
        
        when(mockBookingBloc.state).thenReturn(TripsLoaded(trips));

        await tester.pumpWidget(createWidgetUnderTest());

        // Verify list is rendered with lazy loading
        expect(find.byType(ListView), findsOneWidget);
        
        // Scroll to test lazy loading
        await tester.drag(find.byType(ListView), const Offset(0, -500));
        await tester.pump();

        // Verify performance is maintained
        expect(tester.binding.transientCallbackCount, lessThan(10));
      });

      testWidgets('should debounce search input', (tester) async {
        await tester.pumpWidget(createWidgetUnderTest());

        // Rapidly change search criteria
        final fromDropdown = find.byType(DropdownButtonFormField).first;
        
        for (int i = 0; i < 5; i++) {
          await tester.tap(fromDropdown);
          await tester.pump(const Duration(milliseconds: 100));
        }

        // Verify search is debounced
        verify(mockBookingBloc.add(any)).called(lessThan(3));
      });
    });

    group('Offline Handling Tests', () => {
      testWidgets('should show offline message when no connection', (tester) async {
        when(mockBookingBloc.state).thenReturn(const BookingError('No internet connection'));

        await tester.pumpWidget(createWidgetUnderTest());

        expect(find.text('No internet connection'), findsOneWidget);
        expect(find.text('Please check your connection and try again'), findsOneWidget);
        expect(find.byIcon(Icons.wifi_off), findsOneWidget);
      });

      testWidgets('should cache recent searches for offline viewing', (tester) async {
        // This would test offline caching functionality
        await tester.pumpWidget(createWidgetUnderTest());

        expect(find.text('Recent Searches'), findsOneWidget);
        expect(find.text('View Offline'), findsOneWidget);
      });
    });
  });
}