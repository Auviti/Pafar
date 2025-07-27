"""
Admin endpoints for administrative operations and system management.
"""
from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.admin_service import AdminService
from app.services.auth_service import AuthService
from app.models.user import UserRole
from app.schemas.admin import (
    AdminDashboardMetrics, UserSearchFilters, UserSearchResponse,
    UserManagementAction, FleetAssignment, ReviewModerationAction,
    FraudAlertResponse, LiveTripData, SystemHealth
)
from app.api.v1.auth import get_current_user

router = APIRouter(prefix="/admin", tags=["admin"])


def get_admin_service(db: AsyncSession = Depends(get_db)) -> AdminService:
    """Dependency to get admin service."""
    return AdminService(db)


async def require_admin_role(current_user = Depends(get_current_user)):
    """Dependency to ensure user has admin role."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


@router.get("/dashboard", response_model=AdminDashboardMetrics)
async def get_dashboard_metrics(
    admin_user = Depends(require_admin_role),
    admin_service: AdminService = Depends(get_admin_service)
):
    """
    Get comprehensive dashboard metrics for admin overview.
    
    Returns key metrics including:
    - User statistics (total, active)
    - Booking statistics (total, by status)
    - Revenue metrics (total, monthly)
    - Trip statistics (active, total)
    - Review and fraud alert counts
    
    Requires admin role.
    """
    return await admin_service.get_dashboard_metrics()


@router.get("/users/search", response_model=UserSearchResponse)
async def search_users(
    email: Optional[str] = Query(None, description="Filter by email (partial match)"),
    phone: Optional[str] = Query(None, description="Filter by phone (partial match)"),
    role: Optional[UserRole] = Query(None, description="Filter by user role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_verified: Optional[bool] = Query(None, description="Filter by verification status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    admin_user = Depends(require_admin_role),
    admin_service: AdminService = Depends(get_admin_service)
):
    """
    Search users with various filters and pagination.
    
    - **email**: Partial email match (case-insensitive)
    - **phone**: Partial phone match
    - **role**: Filter by user role (passenger, driver, admin)
    - **is_active**: Filter by active status
    - **is_verified**: Filter by verification status
    - **page**: Page number (starts from 1)
    - **page_size**: Number of items per page (max 100)
    
    Returns paginated list of users matching the criteria.
    Requires admin role.
    """
    filters = UserSearchFilters(
        email=email,
        phone=phone,
        role=role,
        is_active=is_active,
        is_verified=is_verified
    )
    
    return await admin_service.search_users(filters, page, page_size)


@router.post("/users/{user_id}/manage")
async def manage_user(
    user_id: UUID,
    action: UserManagementAction,
    request: Request,
    admin_user = Depends(require_admin_role),
    admin_service: AdminService = Depends(get_admin_service)
):
    """
    Perform management actions on a user account.
    
    Available actions:
    - **suspend**: Deactivate user account
    - **activate**: Reactivate user account
    - **verify**: Mark user as verified
    - **reset_password**: Generate temporary password
    
    - **reason**: Optional reason for the action (recommended for auditing)
    
    All actions are logged for audit purposes.
    Requires admin role.
    """
    # Get client IP for logging
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    result = await admin_service.manage_user(user_id, action, admin_user.id)
    
    return result


@router.post("/fleet/assign")
async def assign_fleet(
    assignment: FleetAssignment,
    admin_user = Depends(require_admin_role),
    admin_service: AdminService = Depends(get_admin_service)
):
    """
    Assign bus and driver to a route for a scheduled trip.
    
    - **bus_id**: ID of the bus to assign
    - **driver_id**: ID of the driver to assign
    - **route_id**: ID of the route for the trip
    - **departure_time**: Scheduled departure time
    - **fare**: Trip fare amount
    
    Validates that:
    - Bus exists and is active
    - Driver exists, has driver role, and is active
    - Route exists and is active
    - No conflicts with existing assignments
    
    Creates a new scheduled trip and logs the assignment.
    Requires admin role.
    """
    return await admin_service.assign_fleet(assignment, admin_user.id)


@router.get("/trips/live", response_model=List[LiveTripData])
async def get_live_trip_data(
    admin_user = Depends(require_admin_role),
    admin_service: AdminService = Depends(get_admin_service)
):
    """
    Get real-time data for all active trips.
    
    Returns live information for trips that are currently:
    - Boarding passengers
    - In transit
    
    For each trip, includes:
    - Route information
    - Bus and driver details
    - Current location (if available)
    - Passenger count
    - Status and timing information
    
    Requires admin role.
    """
    return await admin_service.get_live_trip_data()


@router.post("/reviews/{review_id}/moderate")
async def moderate_review(
    review_id: UUID,
    action: ReviewModerationAction,
    admin_user = Depends(require_admin_role),
    admin_service: AdminService = Depends(get_admin_service)
):
    """
    Moderate user reviews and feedback.
    
    Available actions:
    - **approve**: Approve review for public display
    - **reject**: Reject review (hide from public)
    - **flag**: Flag review for further investigation
    - **hide**: Hide review temporarily
    
    - **reason**: Reason for the moderation action
    - **admin_notes**: Internal notes for the moderation team
    
    All moderation actions are logged for audit purposes.
    Requires admin role.
    """
    return await admin_service.moderate_review(review_id, action, admin_user.id)


@router.get("/fraud-alerts", response_model=FraudAlertResponse)
async def get_fraud_alerts(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    severity: Optional[str] = Query(None, description="Filter by severity (low, medium, high, critical)"),
    status: Optional[str] = Query(None, description="Filter by status (open, investigating, resolved, false_positive)"),
    admin_user = Depends(require_admin_role),
    admin_service: AdminService = Depends(get_admin_service)
):
    """
    Get fraud detection alerts with filtering and pagination.
    
    - **severity**: Filter by alert severity level
    - **status**: Filter by alert status
    - **page**: Page number (starts from 1)
    - **page_size**: Number of items per page (max 100)
    
    Returns paginated list of fraud alerts for investigation.
    Requires admin role.
    """
    return await admin_service.get_fraud_alerts(page, page_size, severity, status)


@router.get("/system/health", response_model=SystemHealth)
async def get_system_health(
    admin_user = Depends(require_admin_role),
    admin_service: AdminService = Depends(get_admin_service)
):
    """
    Get system health and performance metrics.
    
    Returns current status of:
    - Database connectivity
    - Redis connectivity
    - API response times
    - System resource usage (CPU, memory, disk)
    - Active connections
    
    Used for monitoring system performance and detecting issues.
    Requires admin role.
    """
    return await admin_service.get_system_health()


@router.get("/reviews/unmoderated")
async def get_unmoderated_reviews(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    admin_user = Depends(require_admin_role),
    admin_service: AdminService = Depends(get_admin_service)
):
    """
    Get unmoderated reviews for admin review.
    
    - **page**: Page number (starts from 1)
    - **page_size**: Number of items per page (max 100)
    
    Returns paginated list of reviews that need moderation.
    Requires admin role.
    """
    return await admin_service.get_unmoderated_reviews(page, page_size)


@router.get("/reviews/flagged")
async def get_flagged_reviews(
    admin_user = Depends(require_admin_role),
    admin_service: AdminService = Depends(get_admin_service)
):
    """
    Get reviews that have been flagged for investigation.
    
    Returns list of reviews flagged by moderators for further review.
    Requires admin role.
    """
    return await admin_service.get_flagged_reviews()


@router.post("/fraud-alerts/create")
async def create_fraud_alert(
    alert_type: str,
    severity: str,
    description: str,
    user_id: Optional[UUID] = None,
    booking_id: Optional[UUID] = None,
    admin_user = Depends(require_admin_role),
    admin_service: AdminService = Depends(get_admin_service)
):
    """
    Create a new fraud alert (for testing or manual reporting).
    
    - **alert_type**: Type of fraud detected
    - **severity**: Severity level (low, medium, high, critical)
    - **description**: Description of the suspicious activity
    - **user_id**: Associated user ID (optional)
    - **booking_id**: Associated booking ID (optional)
    
    This endpoint is primarily for testing the fraud alert system
    or for manual reporting of suspicious activities.
    Requires admin role.
    """
    alert = await admin_service.create_fraud_alert(
        alert_type=alert_type,
        severity=severity,
        description=description,
        user_id=user_id,
        booking_id=booking_id
    )
    
    return {
        "success": True,
        "message": "Fraud alert created successfully",
        "alert_id": alert.id
    }


@router.post("/fraud-detection/trigger/{user_id}")
async def trigger_fraud_detection(
    user_id: UUID,
    booking_id: Optional[UUID] = None,
    admin_user = Depends(require_admin_role),
    admin_service: AdminService = Depends(get_admin_service)
):
    """
    Manually trigger fraud detection for a user.
    
    - **user_id**: ID of the user to check
    - **booking_id**: Optional booking ID to check (optional)
    
    Runs fraud detection algorithms and creates alerts if suspicious activity is found.
    Requires admin role.
    """
    await admin_service.trigger_fraud_detection(user_id, booking_id)
    
    return {
        "success": True,
        "message": "Fraud detection triggered successfully"
    }