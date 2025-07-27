"""
Admin-related Pydantic schemas for administrative operations.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, EmailStr
from app.models.user import UserRole
from app.models.booking import BookingStatus, PaymentStatus
from app.models.fleet import TripStatus
from app.schemas.user import UserResponse
from app.schemas.booking import BookingResponse
from app.schemas.fleet import TripWithDetails


class AdminDashboardMetrics(BaseModel):
    """Schema for admin dashboard metrics."""
    total_users: int
    active_users: int
    total_bookings: int
    pending_bookings: int
    completed_bookings: int
    cancelled_bookings: int
    total_revenue: float
    monthly_revenue: float
    active_trips: int
    total_trips: int
    pending_reviews: int
    flagged_reviews: int
    fraud_alerts: int


class UserSearchFilters(BaseModel):
    """Schema for user search filters."""
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None


class UserSearchResponse(BaseModel):
    """Schema for user search response."""
    users: List[UserResponse]
    total_count: int
    page: int
    page_size: int


class UserManagementAction(BaseModel):
    """Schema for user management actions."""
    action: str  # suspend, activate, verify, reset_password
    reason: Optional[str] = None


class FleetAssignment(BaseModel):
    """Schema for fleet assignment."""
    bus_id: UUID
    driver_id: UUID
    route_id: UUID
    departure_time: datetime
    fare: float


class ReviewModerationAction(BaseModel):
    """Schema for review moderation actions."""
    action: str  # approve, reject, flag, hide
    reason: Optional[str] = None
    admin_notes: Optional[str] = None


class FraudAlert(BaseModel):
    """Schema for fraud alerts."""
    id: UUID
    alert_type: str
    severity: str  # low, medium, high, critical
    user_id: Optional[UUID] = None
    booking_id: Optional[UUID] = None
    description: str
    metadata: Dict[str, Any]
    status: str  # open, investigating, resolved, false_positive
    created_at: datetime
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[UUID] = None


class FraudAlertResponse(BaseModel):
    """Schema for fraud alert response."""
    alerts: List[FraudAlert]
    total_count: int
    page: int
    page_size: int


class AdminActivityLog(BaseModel):
    """Schema for admin activity logging."""
    id: UUID
    admin_id: UUID
    action: str
    resource_type: str  # user, booking, trip, review, etc.
    resource_id: Optional[UUID] = None
    details: Dict[str, Any]
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime


class LiveTripData(BaseModel):
    """Schema for live trip data."""
    trip_id: UUID
    route_name: str
    bus_license_plate: str
    driver_name: str
    status: TripStatus
    current_location: Optional[Dict[str, float]] = None
    passenger_count: int
    departure_time: datetime
    estimated_arrival: Optional[datetime] = None


class SystemHealth(BaseModel):
    """Schema for system health metrics."""
    database_status: str
    redis_status: str
    api_response_time: float
    active_connections: int
    memory_usage: float
    cpu_usage: float
    disk_usage: float
    last_updated: datetime