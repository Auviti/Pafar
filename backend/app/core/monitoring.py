"""
Error monitoring and alerting system.
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from collections import defaultdict, deque
from dataclasses import dataclass, asdict

from .logging import get_logger

logger = get_logger("monitoring")


@dataclass
class ErrorEvent:
    """Error event data structure."""
    timestamp: datetime
    error_type: str
    error_message: str
    trace_id: str
    service: str
    endpoint: Optional[str] = None
    user_id: Optional[str] = None
    severity: str = "error"
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class AlertRule:
    """Alert rule configuration."""
    name: str
    condition: str  # "error_rate", "error_count", "specific_error"
    threshold: float
    time_window_minutes: int
    severity: str = "warning"
    enabled: bool = True
    metadata: Optional[Dict[str, Any]] = None


class ErrorMonitor:
    """Error monitoring and alerting system."""
    
    def __init__(self, max_events: int = 10000):
        self.max_events = max_events
        self.error_events: deque = deque(maxlen=max_events)
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.alert_rules: List[AlertRule] = []
        self.alert_callbacks: List[callable] = []
        self.last_cleanup = datetime.now()
    
    def add_alert_rule(self, rule: AlertRule):
        """Add an alert rule."""
        self.alert_rules.append(rule)
        logger.info(f"Added alert rule: {rule.name}")
    
    def add_alert_callback(self, callback: callable):
        """Add a callback function for alerts."""
        self.alert_callbacks.append(callback)
    
    async def record_error(
        self,
        error_type: str,
        error_message: str,
        trace_id: str,
        service: str,
        endpoint: Optional[str] = None,
        user_id: Optional[str] = None,
        severity: str = "error",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Record an error event."""
        event = ErrorEvent(
            timestamp=datetime.now(),
            error_type=error_type,
            error_message=error_message,
            trace_id=trace_id,
            service=service,
            endpoint=endpoint,
            user_id=user_id,
            severity=severity,
            metadata=metadata or {}
        )
        
        self.error_events.append(event)
        self.error_counts[error_type] += 1
        
        # Log the error
        logger.error(
            f"Error recorded: {error_type} - {error_message}",
            extra={
                "trace_id": trace_id,
                "service": service,
                "endpoint": endpoint,
                "user_id": user_id,
                "severity": severity,
                "metadata": metadata
            }
        )
        
        # Check alert rules
        await self._check_alert_rules(event)
        
        # Cleanup old events periodically
        await self._cleanup_old_events()
    
    async def _check_alert_rules(self, event: ErrorEvent):
        """Check if any alert rules are triggered."""
        for rule in self.alert_rules:
            if not rule.enabled:
                continue
            
            try:
                if await self._evaluate_rule(rule, event):
                    await self._trigger_alert(rule, event)
            except Exception as e:
                logger.error(f"Error evaluating alert rule {rule.name}: {str(e)}")
    
    async def _evaluate_rule(self, rule: AlertRule, event: ErrorEvent) -> bool:
        """Evaluate if an alert rule is triggered."""
        now = datetime.now()
        time_window = timedelta(minutes=rule.time_window_minutes)
        window_start = now - time_window
        
        if rule.condition == "error_rate":
            # Calculate error rate in the time window
            total_events = sum(1 for e in self.error_events if e.timestamp >= window_start)
            error_events = sum(1 for e in self.error_events 
                             if e.timestamp >= window_start and e.severity == "error")
            
            if total_events > 0:
                error_rate = error_events / total_events
                return error_rate > rule.threshold
        
        elif rule.condition == "error_count":
            # Count errors in the time window
            error_count = sum(1 for e in self.error_events 
                            if e.timestamp >= window_start and e.severity == "error")
            return error_count > rule.threshold
        
        elif rule.condition == "specific_error":
            # Check for specific error type
            target_error = rule.metadata.get("error_type") if rule.metadata else None
            if target_error and event.error_type == target_error:
                error_count = sum(1 for e in self.error_events 
                                if e.timestamp >= window_start and e.error_type == target_error)
                return error_count > rule.threshold
        
        return False
    
    async def _trigger_alert(self, rule: AlertRule, event: ErrorEvent):
        """Trigger an alert."""
        alert_data = {
            "rule_name": rule.name,
            "severity": rule.severity,
            "triggered_at": datetime.now().isoformat(),
            "triggering_event": event.to_dict(),
            "rule": asdict(rule)
        }
        
        logger.warning(
            f"Alert triggered: {rule.name}",
            extra={"alert_data": alert_data}
        )
        
        # Call alert callbacks
        for callback in self.alert_callbacks:
            try:
                await callback(alert_data)
            except Exception as e:
                logger.error(f"Error in alert callback: {str(e)}")
    
    async def _cleanup_old_events(self):
        """Clean up old events to prevent memory issues."""
        now = datetime.now()
        if now - self.last_cleanup > timedelta(hours=1):
            # Keep only events from the last 24 hours
            cutoff = now - timedelta(hours=24)
            
            # Convert deque to list, filter, and convert back
            filtered_events = [e for e in self.error_events if e.timestamp >= cutoff]
            self.error_events.clear()
            self.error_events.extend(filtered_events)
            
            self.last_cleanup = now
            logger.info(f"Cleaned up old error events, kept {len(filtered_events)} events")
    
    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get error summary for the specified time period."""
        now = datetime.now()
        cutoff = now - timedelta(hours=hours)
        
        recent_events = [e for e in self.error_events if e.timestamp >= cutoff]
        
        # Group by error type
        error_types = defaultdict(int)
        services = defaultdict(int)
        severities = defaultdict(int)
        
        for event in recent_events:
            error_types[event.error_type] += 1
            services[event.service] += 1
            severities[event.severity] += 1
        
        return {
            "time_period_hours": hours,
            "total_errors": len(recent_events),
            "error_types": dict(error_types),
            "services": dict(services),
            "severities": dict(severities),
            "generated_at": now.isoformat()
        }
    
    def get_recent_errors(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent error events."""
        recent = list(self.error_events)[-limit:]
        return [event.to_dict() for event in reversed(recent)]


# Global error monitor instance
error_monitor = ErrorMonitor()

# Default alert rules
default_alert_rules = [
    AlertRule(
        name="High Error Rate",
        condition="error_rate",
        threshold=0.1,  # 10% error rate
        time_window_minutes=5,
        severity="critical"
    ),
    AlertRule(
        name="Error Spike",
        condition="error_count",
        threshold=50,  # 50 errors in 5 minutes
        time_window_minutes=5,
        severity="warning"
    ),
    AlertRule(
        name="Payment Failures",
        condition="specific_error",
        threshold=5,  # 5 payment errors in 10 minutes
        time_window_minutes=10,
        severity="critical",
        metadata={"error_type": "PAYMENT_ERROR"}
    ),
    AlertRule(
        name="Authentication Failures",
        condition="specific_error",
        threshold=20,  # 20 auth failures in 5 minutes
        time_window_minutes=5,
        severity="warning",
        metadata={"error_type": "AUTHENTICATION_ERROR"}
    )
]

# Initialize default alert rules
for rule in default_alert_rules:
    error_monitor.add_alert_rule(rule)


# Alert callback functions
async def log_alert_callback(alert_data: Dict[str, Any]):
    """Log alert to structured logging."""
    logger.critical(
        f"ALERT: {alert_data['rule_name']}",
        extra={"alert": alert_data}
    )


async def webhook_alert_callback(alert_data: Dict[str, Any]):
    """Send alert to webhook (placeholder for external integrations)."""
    # This would integrate with services like Slack, PagerDuty, etc.
    logger.info(f"Would send webhook alert: {alert_data['rule_name']}")


# Register default callbacks
error_monitor.add_alert_callback(log_alert_callback)
error_monitor.add_alert_callback(webhook_alert_callback)


# Helper function to record errors from exception handlers
async def record_exception_error(
    exception: Exception,
    trace_id: str,
    service: str = "api",
    endpoint: Optional[str] = None,
    user_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """Record an error from an exception."""
    await error_monitor.record_error(
        error_type=type(exception).__name__,
        error_message=str(exception),
        trace_id=trace_id,
        service=service,
        endpoint=endpoint,
        user_id=user_id,
        severity="error",
        metadata=metadata
    )