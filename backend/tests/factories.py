"""
Test data factories for creating test objects.
"""
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional
from app.models.user import User, UserRole
from app.models.fleet import Terminal, Route, Bus, Trip, TripStatus
from app.models.booking import Booking, BookingStatus, PaymentStatus
from app.models.payment import Payment, PaymentMethod, PaymentStatus as PaymentStatusEnum
from app.models.tracking import TripLocation


class UserFactory:
    """Factory for creating User objects."""
    
    @staticmethod
    def create(
        email: str = "test@example.com",
        password_hash: str = "hashed_password",
        first_name: str = "John",
        last_name: str = "Doe",
        role: UserRole = UserRole.PASSENGER,
        phone: Optional[str] = None,
        is_verified: bool = True,
        is_active: bool = True
    ) -> User:
        return User(
            id=uuid.uuid4(),
            email=email,
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name,
            role=role,
            phone=phone,
            is_verified=is_verified,
            is_active=is_active,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    @staticmethod
    def create_driver(
        email: str = "driver@example.com",
        first_name: str = "Jane",
        last_name: str = "Driver"
    ) -> User:
        return UserFactory.create(
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=UserRole.DRIVER
        )
    
    @staticmethod
    def create_admin(
        email: str = "admin@example.com",
        first_name: str = "Admin",
        last_name: str = "User"
    ) -> User:
        return UserFactory.create(
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=UserRole.ADMIN
        )


class TerminalFactory:
    """Factory for creating Terminal objects."""
    
    @staticmethod
    def create(
        name: str = "Test Terminal",
        city: str = "Test City",
        address: str = "123 Test St",
        latitude: Decimal = Decimal("40.7128"),
        longitude: Decimal = Decimal("-74.0060"),
        is_active: bool = True
    ) -> Terminal:
        return Terminal(
            id=uuid.uuid4(),
            name=name,
            city=city,
            address=address,
            latitude=latitude,
            longitude=longitude,
            is_active=is_active,
            created_at=datetime.utcnow()
        )
    
    @staticmethod
    def create_pair() -> tuple[Terminal, Terminal]:
        """Create a pair of terminals for routes."""
        origin = TerminalFactory.create(
            name="Origin Terminal",
            city="Origin City",
            latitude=Decimal("40.0000"),
            longitude=Decimal("-74.0000")
        )
        destination = TerminalFactory.create(
            name="Destination Terminal",
            city="Destination City",
            latitude=Decimal("41.0000"),
            longitude=Decimal("-75.0000")
        )
        return origin, destination


class RouteFactory:
    """Factory for creating Route objects."""
    
    @staticmethod
    def create(
        origin_terminal_id: Optional[uuid.UUID] = None,
        destination_terminal_id: Optional[uuid.UUID] = None,
        distance_km: Decimal = Decimal("100.0"),
        estimated_duration_minutes: int = 120,
        base_fare: Decimal = Decimal("25.00"),
        is_active: bool = True
    ) -> Route:
        return Route(
            id=uuid.uuid4(),
            origin_terminal_id=origin_terminal_id or uuid.uuid4(),
            destination_terminal_id=destination_terminal_id or uuid.uuid4(),
            distance_km=distance_km,
            estimated_duration_minutes=estimated_duration_minutes,
            base_fare=base_fare,
            is_active=is_active,
            created_at=datetime.utcnow()
        )


class BusFactory:
    """Factory for creating Bus objects."""
    
    @staticmethod
    def create(
        license_plate: str = "TEST-123",
        model: str = "Test Bus Model",
        capacity: int = 50,
        amenities: Optional[dict] = None,
        is_active: bool = True
    ) -> Bus:
        if amenities is None:
            amenities = {"wifi": True, "ac": True, "charging_ports": True}
        
        return Bus(
            id=uuid.uuid4(),
            license_plate=license_plate,
            model=model,
            capacity=capacity,
            amenities=amenities,
            is_active=is_active,
            created_at=datetime.utcnow()
        )


class TripFactory:
    """Factory for creating Trip objects."""
    
    @staticmethod
    def create(
        route_id: Optional[uuid.UUID] = None,
        bus_id: Optional[uuid.UUID] = None,
        driver_id: Optional[uuid.UUID] = None,
        departure_time: Optional[datetime] = None,
        arrival_time: Optional[datetime] = None,
        status: TripStatus = TripStatus.SCHEDULED,
        fare: Decimal = Decimal("30.00"),
        available_seats: int = 50
    ) -> Trip:
        if departure_time is None:
            departure_time = datetime.utcnow() + timedelta(hours=2)
        
        return Trip(
            id=uuid.uuid4(),
            route_id=route_id or uuid.uuid4(),
            bus_id=bus_id or uuid.uuid4(),
            driver_id=driver_id or uuid.uuid4(),
            departure_time=departure_time,
            arrival_time=arrival_time,
            status=status,
            fare=fare,
            available_seats=available_seats,
            created_at=datetime.utcnow()
        )


class BookingFactory:
    """Factory for creating Booking objects."""
    
    @staticmethod
    def create(
        user_id: Optional[uuid.UUID] = None,
        trip_id: Optional[uuid.UUID] = None,
        seat_numbers: Optional[list[int]] = None,
        total_amount: Decimal = Decimal("30.00"),
        status: BookingStatus = BookingStatus.PENDING,
        payment_status: PaymentStatus = PaymentStatus.PENDING,
        booking_reference: str = "BK123456"
    ) -> Booking:
        if seat_numbers is None:
            seat_numbers = [1]
        
        return Booking(
            id=uuid.uuid4(),
            user_id=user_id or uuid.uuid4(),
            trip_id=trip_id or uuid.uuid4(),
            seat_numbers=seat_numbers,
            total_amount=total_amount,
            status=status,
            payment_status=payment_status,
            booking_reference=booking_reference,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )


class PaymentFactory:
    """Factory for creating Payment objects."""
    
    @staticmethod
    def create(
        booking_id: Optional[uuid.UUID] = None,
        amount: Decimal = Decimal("30.00"),
        currency: str = "USD",
        payment_method: PaymentMethod = PaymentMethod.CARD,
        payment_gateway: str = "stripe",
        gateway_transaction_id: str = "txn_123456",
        status: PaymentStatusEnum = PaymentStatusEnum.PENDING
    ) -> Payment:
        return Payment(
            id=uuid.uuid4(),
            booking_id=booking_id or uuid.uuid4(),
            amount=amount,
            currency=currency,
            payment_method=payment_method,
            payment_gateway=payment_gateway,
            gateway_transaction_id=gateway_transaction_id,
            status=status,
            created_at=datetime.utcnow()
        )


class TripLocationFactory:
    """Factory for creating TripLocation objects."""
    
    @staticmethod
    def create(
        trip_id: Optional[uuid.UUID] = None,
        latitude: Decimal = Decimal("40.7128"),
        longitude: Decimal = Decimal("-74.0060"),
        speed: Optional[Decimal] = Decimal("65.0"),
        heading: Optional[Decimal] = Decimal("180.0"),
        recorded_at: Optional[datetime] = None
    ) -> TripLocation:
        if recorded_at is None:
            recorded_at = datetime.utcnow()
        
        return TripLocation(
            id=uuid.uuid4(),
            trip_id=trip_id or uuid.uuid4(),
            latitude=latitude,
            longitude=longitude,
            speed=speed,
            heading=heading,
            recorded_at=recorded_at
        )


class TestDataBuilder:
    """Builder for creating complete test scenarios."""
    
    @staticmethod
    def create_complete_booking_scenario():
        """Create a complete booking scenario with all related objects."""
        # Create terminals
        origin, destination = TerminalFactory.create_pair()
        
        # Create route
        route = RouteFactory.create(
            origin_terminal_id=origin.id,
            destination_terminal_id=destination.id
        )
        
        # Create bus and driver
        bus = BusFactory.create()
        driver = UserFactory.create_driver()
        
        # Create trip
        trip = TripFactory.create(
            route_id=route.id,
            bus_id=bus.id,
            driver_id=driver.id
        )
        
        # Create passenger
        passenger = UserFactory.create()
        
        # Create booking
        booking = BookingFactory.create(
            user_id=passenger.id,
            trip_id=trip.id
        )
        
        # Create payment
        payment = PaymentFactory.create(booking_id=booking.id)
        
        return {
            'origin': origin,
            'destination': destination,
            'route': route,
            'bus': bus,
            'driver': driver,
            'trip': trip,
            'passenger': passenger,
            'booking': booking,
            'payment': payment
        }
    
    @staticmethod
    def create_trip_with_tracking():
        """Create a trip with location tracking data."""
        scenario = TestDataBuilder.create_complete_booking_scenario()
        
        # Add location tracking
        locations = [
            TripLocationFactory.create(
                trip_id=scenario['trip'].id,
                latitude=Decimal("40.7128"),
                longitude=Decimal("-74.0060"),
                recorded_at=datetime.utcnow() - timedelta(minutes=30)
            ),
            TripLocationFactory.create(
                trip_id=scenario['trip'].id,
                latitude=Decimal("40.7500"),
                longitude=Decimal("-74.0200"),
                recorded_at=datetime.utcnow() - timedelta(minutes=15)
            ),
            TripLocationFactory.create(
                trip_id=scenario['trip'].id,
                latitude=Decimal("40.7800"),
                longitude=Decimal("-74.0400"),
                recorded_at=datetime.utcnow()
            )
        ]
        
        scenario['locations'] = locations
        return scenario


class ReviewFactory:
    """Factory for creating Review objects."""
    
    @staticmethod
    def create(
        booking_id: Optional[uuid.UUID] = None,
        user_id: Optional[uuid.UUID] = None,
        driver_id: Optional[uuid.UUID] = None,
        rating: int = 5,
        comment: str = "Great service!",
        is_moderated: bool = False
    ):
        from app.models.review import Review
        
        return Review(
            id=uuid.uuid4(),
            booking_id=booking_id or uuid.uuid4(),
            user_id=user_id or uuid.uuid4(),
            driver_id=driver_id or uuid.uuid4(),
            rating=rating,
            comment=comment,
            is_moderated=is_moderated,
            created_at=datetime.utcnow()
        )


class PerformanceTestDataBuilder:
    """Builder for creating performance test data."""
    
    @staticmethod
    def create_large_dataset(num_users=1000, num_trips=500, num_bookings=2000):
        """Create large dataset for performance testing."""
        users = []
        trips = []
        bookings = []
        
        # Create users
        for i in range(num_users):
            user = UserFactory.create(
                email=f"user{i}@example.com",
                first_name=f"User{i}",
                last_name="Test"
            )
            users.append(user)
        
        # Create trips
        for i in range(num_trips):
            trip = TripFactory.create(
                departure_time=datetime.utcnow() + timedelta(hours=i),
                fare=Decimal(str(50 + (i % 100)))
            )
            trips.append(trip)
        
        # Create bookings
        for i in range(num_bookings):
            user = users[i % len(users)]
            trip = trips[i % len(trips)]
            booking = BookingFactory.create(
                user_id=user.id,
                trip_id=trip.id,
                booking_reference=f"BK{i:06d}"
            )
            bookings.append(booking)
        
        return {
            'users': users,
            'trips': trips,
            'bookings': bookings
        }
    
    @staticmethod
    def create_concurrent_booking_scenario(num_users=10, target_seats=[1, 2, 3]):
        """Create scenario for testing concurrent booking attempts."""
        trip = TripFactory.create(available_seats=len(target_seats))
        users = [
            UserFactory.create(email=f"concurrent_user_{i}@example.com")
            for i in range(num_users)
        ]
        
        return {
            'trip': trip,
            'users': users,
            'target_seats': target_seats
        }


class ErrorScenarioFactory:
    """Factory for creating error test scenarios."""
    
    @staticmethod
    def create_payment_failure_scenario():
        """Create scenario for payment failure testing."""
        user = UserFactory.create()
        trip = TripFactory.create()
        booking = BookingFactory.create(
            user_id=user.id,
            trip_id=trip.id,
            status=BookingStatus.PENDING,
            payment_status=PaymentStatus.PENDING
        )
        
        return {
            'user': user,
            'trip': trip,
            'booking': booking,
            'payment_errors': [
                'card_declined',
                'insufficient_funds',
                'expired_card',
                'network_error'
            ]
        }
    
    @staticmethod
    def create_network_interruption_scenario():
        """Create scenario for network interruption testing."""
        return {
            'interruption_points': [
                'during_search',
                'during_booking',
                'during_payment',
                'during_confirmation'
            ],
            'recovery_strategies': [
                'retry_immediately',
                'retry_with_backoff',
                'cache_and_retry',
                'user_initiated_retry'
            ]
        }


class SecurityTestDataBuilder:
    """Builder for creating security test scenarios."""
    
    @staticmethod
    def create_injection_test_data():
        """Create data for SQL injection and XSS testing."""
        return {
            'sql_injection_payloads': [
                "'; DROP TABLE users; --",
                "' OR '1'='1",
                "'; UPDATE users SET role='admin' WHERE id=1; --",
                "' UNION SELECT * FROM users --"
            ],
            'xss_payloads': [
                "<script>alert('XSS')</script>",
                "javascript:alert('XSS')",
                "<img src=x onerror=alert('XSS')>",
                "';alert('XSS');//"
            ],
            'path_traversal_payloads': [
                "../../../etc/passwd",
                "..\\..\\..\\windows\\system32\\config\\sam",
                "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd"
            ]
        }
    
    @staticmethod
    def create_authentication_bypass_scenarios():
        """Create scenarios for authentication bypass testing."""
        return {
            'invalid_tokens': [
                'invalid_jwt_token',
                'expired_jwt_token',
                'malformed_jwt_token',
                'none_algorithm_jwt'
            ],
            'privilege_escalation_attempts': [
                {'user_role': 'passenger', 'attempted_action': 'admin_dashboard'},
                {'user_role': 'driver', 'attempted_action': 'user_management'},
                {'user_role': 'passenger', 'attempted_action': 'fleet_management'}
            ]
        }


class LoadTestDataBuilder:
    """Builder for creating load test scenarios."""
    
    @staticmethod
    def create_high_traffic_scenario(concurrent_users=100, requests_per_second=50):
        """Create high traffic load test scenario."""
        return {
            'concurrent_users': concurrent_users,
            'requests_per_second': requests_per_second,
            'test_duration_seconds': 300,  # 5 minutes
            'endpoints_to_test': [
                {'endpoint': '/api/v1/bookings/trips/search', 'weight': 40},
                {'endpoint': '/api/v1/bookings/', 'weight': 20},
                {'endpoint': '/api/v1/auth/login', 'weight': 15},
                {'endpoint': '/api/v1/tracking/trips/{trip_id}/location', 'weight': 15},
                {'endpoint': '/api/v1/payments/create-intent', 'weight': 10}
            ],
            'expected_response_times': {
                'p50': 200,  # 50th percentile in ms
                'p95': 500,  # 95th percentile in ms
                'p99': 1000  # 99th percentile in ms
            },
            'max_error_rate': 0.01  # 1% error rate
        }
    
    @staticmethod
    def create_stress_test_scenario():
        """Create stress test scenario to find breaking point."""
        return {
            'ramp_up_pattern': [
                {'users': 10, 'duration': 60},
                {'users': 50, 'duration': 120},
                {'users': 100, 'duration': 180},
                {'users': 200, 'duration': 240},
                {'users': 500, 'duration': 300}
            ],
            'breaking_point_indicators': [
                'response_time_over_5s',
                'error_rate_over_5_percent',
                'database_connection_exhaustion',
                'memory_usage_over_90_percent'
            ]
        }


class IntegrationTestDataBuilder:
    """Builder for creating integration test scenarios."""
    
    @staticmethod
    def create_third_party_service_scenarios():
        """Create scenarios for third-party service integration testing."""
        return {
            'payment_gateway_scenarios': {
                'stripe_success': {
                    'payment_intent_id': 'pi_success_123',
                    'status': 'succeeded',
                    'amount': 5000,
                    'currency': 'usd'
                },
                'stripe_failure': {
                    'payment_intent_id': 'pi_failure_123',
                    'status': 'failed',
                    'error': 'card_declined'
                },
                'stripe_timeout': {
                    'payment_intent_id': 'pi_timeout_123',
                    'error': 'network_timeout'
                }
            },
            'maps_api_scenarios': {
                'geocoding_success': {
                    'address': '123 Main St, New York, NY',
                    'latitude': 40.7128,
                    'longitude': -74.0060
                },
                'geocoding_failure': {
                    'address': 'Invalid Address',
                    'error': 'ZERO_RESULTS'
                },
                'directions_success': {
                    'origin': (40.7128, -74.0060),
                    'destination': (34.0522, -118.2437),
                    'distance': 4500000,  # meters
                    'duration': 172800   # seconds
                }
            },
            'notification_service_scenarios': {
                'email_success': {
                    'to': 'test@example.com',
                    'subject': 'Booking Confirmation',
                    'message_id': 'msg_success_123'
                },
                'sms_success': {
                    'to': '+1234567890',
                    'message': 'Your trip starts in 30 minutes',
                    'message_id': 'sms_success_123'
                },
                'push_notification_success': {
                    'device_token': 'device_token_123',
                    'title': 'Trip Update',
                    'body': 'Your bus is approaching',
                    'message_id': 'push_success_123'
                }
            }
        }


class AccessibilityTestDataBuilder:
    """Builder for creating accessibility test scenarios."""
    
    @staticmethod
    def create_screen_reader_scenarios():
        """Create scenarios for screen reader testing."""
        return {
            'aria_label_tests': [
                {'element': 'search_form', 'expected_label': 'Trip search form'},
                {'element': 'seat_map', 'expected_label': 'Seat selection map'},
                {'element': 'payment_form', 'expected_label': 'Payment information form'}
            ],
            'keyboard_navigation_tests': [
                {'page': 'booking', 'tab_order': ['origin_select', 'destination_select', 'date_input', 'search_button']},
                {'page': 'seat_selection', 'tab_order': ['seat_1', 'seat_2', 'continue_button']},
                {'page': 'payment', 'tab_order': ['card_number', 'expiry', 'cvc', 'pay_button']}
            ],
            'color_contrast_tests': [
                {'element': 'primary_button', 'min_contrast_ratio': 4.5},
                {'element': 'error_message', 'min_contrast_ratio': 4.5},
                {'element': 'form_label', 'min_contrast_ratio': 4.5}
            ]
        }


class MobileTestDataBuilder:
    """Builder for creating mobile-specific test scenarios."""
    
    @staticmethod
    def create_responsive_design_scenarios():
        """Create scenarios for responsive design testing."""
        return {
            'viewport_sizes': [
                {'name': 'mobile_portrait', 'width': 375, 'height': 667},
                {'name': 'mobile_landscape', 'width': 667, 'height': 375},
                {'name': 'tablet_portrait', 'width': 768, 'height': 1024},
                {'name': 'tablet_landscape', 'width': 1024, 'height': 768},
                {'name': 'desktop', 'width': 1920, 'height': 1080}
            ],
            'touch_target_tests': [
                {'element': 'seat_button', 'min_size': 44},  # 44px minimum
                {'element': 'navigation_button', 'min_size': 44},
                {'element': 'form_input', 'min_size': 44}
            ],
            'gesture_tests': [
                {'action': 'swipe_left', 'expected': 'navigate_back'},
                {'action': 'pinch_zoom', 'expected': 'zoom_map'},
                {'action': 'double_tap', 'expected': 'select_seat'}
            ]
        }
    
    @staticmethod
    def create_offline_scenarios():
        """Create scenarios for offline functionality testing."""
        return {
            'offline_capabilities': [
                'view_cached_bookings',
                'view_trip_history',
                'access_saved_payment_methods'
            ],
            'sync_scenarios': [
                {'action': 'book_trip_offline', 'sync_behavior': 'queue_for_sync'},
                {'action': 'update_profile_offline', 'sync_behavior': 'queue_for_sync'},
                {'action': 'cancel_booking_offline', 'sync_behavior': 'show_error'}
            ],
            'network_recovery_tests': [
                'reconnect_after_wifi_loss',
                'switch_from_wifi_to_cellular',
                'handle_slow_network_conditions'
            ]
        }


# Export all factories and builders for easy import
__all__ = [
    'UserFactory',
    'TerminalFactory', 
    'RouteFactory',
    'BusFactory',
    'TripFactory',
    'BookingFactory',
    'PaymentFactory',
    'TripLocationFactory',
    'ReviewFactory',
    'TestDataBuilder',
    'PerformanceTestDataBuilder',
    'ErrorScenarioFactory',
    'SecurityTestDataBuilder',
    'LoadTestDataBuilder',
    'IntegrationTestDataBuilder',
    'AccessibilityTestDataBuilder',
    'MobileTestDataBuilder'
]