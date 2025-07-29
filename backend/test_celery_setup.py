#!/usr/bin/env python3
"""
Test script to verify Celery setup and task functionality.
"""
import asyncio
from app.core.celery_app import celery_app
from app.tasks.email_tasks import send_booking_confirmation_email
from app.tasks.sms_tasks import send_trip_departure_sms
from app.tasks.push_notification_tasks import send_booking_confirmation_push
from app.tasks.cleanup_tasks import cleanup_expired_reservations
from app.utils.task_monitoring import task_monitor, health_checker


def test_celery_configuration():
    """Test Celery configuration."""
    print("=== Testing Celery Configuration ===")
    print(f"Celery app name: {celery_app.main}")
    print(f"Broker URL: {celery_app.conf.broker_url}")
    print(f"Result backend: {celery_app.conf.result_backend}")
    print(f"Task routes: {celery_app.conf.task_routes}")
    print(f"Beat schedule: {list(celery_app.conf.beat_schedule.keys())}")
    print("✅ Celery configuration loaded successfully\n")


def test_task_registration():
    """Test that tasks are properly registered."""
    print("=== Testing Task Registration ===")
    
    # Get registered tasks
    registered_tasks = list(celery_app.tasks.keys())
    
    expected_tasks = [
        'app.tasks.email_tasks.send_booking_confirmation_email',
        'app.tasks.email_tasks.send_booking_cancellation_email',
        'app.tasks.email_tasks.send_payment_receipt_email',
        'app.tasks.sms_tasks.send_trip_departure_sms',
        'app.tasks.sms_tasks.send_trip_delay_sms',
        'app.tasks.sms_tasks.send_booking_confirmation_sms',
        'app.tasks.sms_tasks.send_otp_sms',
        'app.tasks.push_notification_tasks.send_booking_confirmation_push',
        'app.tasks.push_notification_tasks.send_trip_status_push',
        'app.tasks.cleanup_tasks.cleanup_expired_reservations',
        'app.tasks.cleanup_tasks.cleanup_old_trip_locations',
    ]
    
    print(f"Total registered tasks: {len(registered_tasks)}")
    
    for task_name in expected_tasks:
        if task_name in registered_tasks:
            print(f"✅ {task_name}")
        else:
            print(f"❌ {task_name} - NOT FOUND")
    
    print()


def test_task_creation():
    """Test creating task instances without executing them."""
    print("=== Testing Task Creation ===")
    
    try:
        # Test email task
        booking_data = {
            "booking_reference": "TEST123",
            "origin": "Test City A",
            "destination": "Test City B",
            "departure_time": "2024-01-15 10:00:00",
            "arrival_time": "2024-01-15 14:00:00",
            "seats": [1, 2],
            "total_amount": "100.00",
            "bus_info": "Test Bus #1"
        }
        
        # Create task signature (don't execute)
        email_task = send_booking_confirmation_email.s(
            "test@example.com",
            "Test User",
            booking_data
        )
        print(f"✅ Email task signature created: {email_task}")
        
        # Test SMS task
        trip_data = {
            "booking_reference": "TEST123",
            "origin": "Test City A",
            "destination": "Test City B",
            "departure_time": "2024-01-15 10:00:00",
            "seats": [1, 2]
        }
        
        sms_task = send_trip_departure_sms.s(
            "+1234567890",
            "Test User",
            trip_data
        )
        print(f"✅ SMS task signature created: {sms_task}")
        
        # Test push notification task
        push_task = send_booking_confirmation_push.s(
            ["test_token_1", "test_token_2"],
            "Test User",
            booking_data
        )
        print(f"✅ Push notification task signature created: {push_task}")
        
        # Test cleanup task
        cleanup_task = cleanup_expired_reservations.s()
        print(f"✅ Cleanup task signature created: {cleanup_task}")
        
        print("✅ All task signatures created successfully\n")
        
    except Exception as e:
        print(f"❌ Error creating task signatures: {e}\n")


async def test_monitoring_utilities():
    """Test task monitoring utilities."""
    print("=== Testing Monitoring Utilities ===")
    
    try:
        # Test task monitor
        await task_monitor.log_task_start("test_task_123", "test_task", (), {})
        print("✅ Task monitor log_task_start works")
        
        task_status = await task_monitor.get_task_status("test_task_123")
        if task_status:
            print("✅ Task monitor get_task_status works")
        else:
            print("⚠️ Task monitor get_task_status returned None (Redis might not be running)")
        
        # Test health checker
        worker_health = await health_checker.check_worker_health()
        print(f"✅ Worker health check: {worker_health['message']}")
        
        queue_health = await health_checker.check_queue_health()
        print(f"✅ Queue health check: {queue_health['message']}")
        
        failure_rate = await health_checker.check_task_failure_rate()
        print(f"✅ Failure rate check: {failure_rate['message']}")
        
        print("✅ All monitoring utilities work\n")
        
    except Exception as e:
        print(f"❌ Error testing monitoring utilities: {e}\n")


def test_beat_schedule():
    """Test Celery Beat schedule configuration."""
    print("=== Testing Celery Beat Schedule ===")
    
    beat_schedule = celery_app.conf.beat_schedule
    
    for task_name, config in beat_schedule.items():
        print(f"✅ {task_name}:")
        print(f"   Task: {config['task']}")
        print(f"   Schedule: {config['schedule']} seconds")
    
    print()


def main():
    """Run all tests."""
    print("🚀 Testing Celery Setup for Pafar Transport Management Platform\n")
    
    test_celery_configuration()
    test_task_registration()
    test_task_creation()
    test_beat_schedule()
    
    # Run async tests
    asyncio.run(test_monitoring_utilities())
    
    print("🎉 Celery setup testing completed!")
    print("\nTo start the Celery worker, run:")
    print("celery -A app.core.celery_app worker --loglevel=info")
    print("\nTo start the Celery beat scheduler, run:")
    print("celery -A app.core.celery_app beat --loglevel=info")
    print("\nTo monitor tasks, run:")
    print("celery -A app.core.celery_app flower")


if __name__ == "__main__":
    main()