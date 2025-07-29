"""
Celery application configuration for background task processing.
"""
from celery import Celery
from .config import settings

# Create Celery instance
celery_app = Celery(
    "pafar_tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.email_tasks",
        "app.tasks.sms_tasks", 
        "app.tasks.push_notification_tasks",
        "app.tasks.cleanup_tasks"
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task routing
    task_routes={
        "app.tasks.email_tasks.*": {"queue": "email"},
        "app.tasks.sms_tasks.*": {"queue": "sms"},
        "app.tasks.push_notification_tasks.*": {"queue": "notifications"},
        "app.tasks.cleanup_tasks.*": {"queue": "cleanup"},
    },
    
    # Task serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    
    # Task execution
    task_always_eager=False,
    task_eager_propagates=True,
    task_ignore_result=False,
    
    # Task retry configuration
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Worker configuration
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    
    # Result backend settings
    result_expires=3600,  # 1 hour
    result_backend_transport_options={
        "master_name": "mymaster",
        "visibility_timeout": 3600,
    },
    
    # Timezone
    timezone="UTC",
    enable_utc=True,
    
    # Beat schedule for periodic tasks
    beat_schedule={
        "cleanup-expired-reservations": {
            "task": "app.tasks.cleanup_tasks.cleanup_expired_reservations",
            "schedule": 300.0,  # Every 5 minutes
        },
        "cleanup-old-locations": {
            "task": "app.tasks.cleanup_tasks.cleanup_old_trip_locations",
            "schedule": 3600.0,  # Every hour
        },
        "cleanup-old-notifications": {
            "task": "app.tasks.cleanup_tasks.cleanup_old_notifications",
            "schedule": 86400.0,  # Every day
        },
    },
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
    
    # Error handling
    task_soft_time_limit=300,  # 5 minutes
    task_time_limit=600,       # 10 minutes
)

# Task base class with error handling
class BaseTask(celery_app.Task):
    """Base task class with error handling and logging."""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure."""
        print(f"Task {task_id} failed: {exc}")
        # Here you could send alerts, log to monitoring system, etc.
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Handle task retry."""
        print(f"Task {task_id} retrying: {exc}")
    
    def on_success(self, retval, task_id, args, kwargs):
        """Handle task success."""
        print(f"Task {task_id} succeeded")

# Set the base task class
celery_app.Task = BaseTask