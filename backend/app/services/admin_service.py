"""
Admin service for administrative operations and system management.
"""
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, text
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from app.models.user import User, UserRole
from app.models.booking import Booking, BookingStatus, PaymentStatus
from app.models.fleet import Trip, TripStatus, Bus, Route, Terminal
from app.models.payment import Payment
from app.models.tracking import TripLocation
from app.schemas.admin import (
    AdminDashboardMetrics, UserSearchFilters, UserSearchResponse,
    UserManagementAction, FleetAssignment, ReviewModerationAction,
    FraudAlert, FraudAlertResponse, AdminActivityLog, LiveTripData,
    SystemHealth
)
from app.core.redis import redis_client
from app.core.security import get_password_hash
import secrets
import string


class AdminService:
    """Service for administrative operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_dashboard_metrics(self) -> AdminDashboardMetrics:
        """Get comprehensive dashboard metrics."""
        # User metrics
        total_users_result = await self.db.execute(select(func.count(User.id)))
        total_users = total_users_result.scalar()
        
        active_users_result = await self.db.execute(
            select(func.count(User.id)).where(User.is_active == True)
        )
        active_users = active_users_result.scalar()
        
        # Booking metrics
        total_bookings_result = await self.db.execute(select(func.count(Booking.id)))
        total_bookings = total_bookings_result.scalar()
        
        pending_bookings_result = await self.db.execute(
            select(func.count(Booking.id)).where(Booking.status == BookingStatus.PENDING)
        )
        pending_bookings = pending_bookings_result.scalar()
        
        completed_bookings_result = await self.db.execute(
            select(func.count(Booking.id)).where(Booking.status == BookingStatus.COMPLETED)
        )
        completed_bookings = completed_bookings_result.scalar()
        
        cancelled_bookings_result = await self.db.execute(
            select(func.count(Booking.id)).where(Booking.status == BookingStatus.CANCELLED)
        )
        cancelled_bookings = cancelled_bookings_result.scalar()
        
        # Revenue metrics
        total_revenue_result = await self.db.execute(
            select(func.coalesce(func.sum(Payment.amount), 0))
            .where(Payment.status == "completed")
        )
        total_revenue = float(total_revenue_result.scalar() or 0)
        
        # Monthly revenue (current month)
        current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_revenue_result = await self.db.execute(
            select(func.coalesce(func.sum(Payment.amount), 0))
            .where(
                and_(
                    Payment.status == "completed",
                    Payment.created_at >= current_month_start
                )
            )
        )
        monthly_revenue = float(monthly_revenue_result.scalar() or 0)
        
        # Trip metrics
        total_trips_result = await self.db.execute(select(func.count(Trip.id)))
        total_trips = total_trips_result.scalar()
        
        active_trips_result = await self.db.execute(
            select(func.count(Trip.id)).where(
                Trip.status.in_([TripStatus.BOARDING, TripStatus.IN_TRANSIT])
            )
        )
        active_trips = active_trips_result.scalar()
        
        # Review metrics
        from app.models.tracking import Review
        
        pending_reviews_result = await self.db.execute(
            select(func.count(Review.id)).where(Review.is_moderated == False)
        )
        pending_reviews = pending_reviews_result.scalar()
        
        # Get flagged reviews count from Redis
        flagged_reviews_key = "flagged_reviews"
        flagged_data = await redis_client.get(flagged_reviews_key)
        if flagged_data:
            flagged_list = json.loads(flagged_data)
            flagged_reviews = len([r for r in flagged_list if r.get("status") == "pending_investigation"])
        else:
            flagged_reviews = 0
        
        # Fraud alerts (from Redis cache)
        fraud_alerts = await self._get_fraud_alert_count()
        
        return AdminDashboardMetrics(
            total_users=total_users,
            active_users=active_users,
            total_bookings=total_bookings,
            pending_bookings=pending_bookings,
            completed_bookings=completed_bookings,
            cancelled_bookings=cancelled_bookings,
            total_revenue=total_revenue,
            monthly_revenue=monthly_revenue,
            active_trips=active_trips,
            total_trips=total_trips,
            pending_reviews=pending_reviews,
            flagged_reviews=flagged_reviews,
            fraud_alerts=fraud_alerts
        )
    
    async def search_users(
        self, 
        filters: UserSearchFilters, 
        page: int = 1, 
        page_size: int = 20
    ) -> UserSearchResponse:
        """Search users with filters and pagination."""
        query = select(User)
        
        # Apply filters
        conditions = []
        
        if filters.email:
            conditions.append(User.email.ilike(f"%{filters.email}%"))
        
        if filters.phone:
            conditions.append(User.phone.ilike(f"%{filters.phone}%"))
        
        if filters.role:
            conditions.append(User.role == filters.role)
        
        if filters.is_active is not None:
            conditions.append(User.is_active == filters.is_active)
        
        if filters.is_verified is not None:
            conditions.append(User.is_verified == filters.is_verified)
        
        if filters.created_after:
            conditions.append(User.created_at >= filters.created_after)
        
        if filters.created_before:
            conditions.append(User.created_at <= filters.created_before)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # Get total count
        count_query = select(func.count(User.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        
        total_count_result = await self.db.execute(count_query)
        total_count = total_count_result.scalar()
        
        # Apply pagination and ordering
        query = query.order_by(desc(User.created_at))
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.db.execute(query)
        users = result.scalars().all()
        
        return UserSearchResponse(
            users=users,
            total_count=total_count,
            page=page,
            page_size=page_size
        )
    
    async def manage_user(
        self, 
        user_id: UUID, 
        action: UserManagementAction, 
        admin_id: UUID
    ) -> Dict[str, Any]:
        """Perform user management actions."""
        user = await self._get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        result = {"success": False, "message": ""}
        
        if action.action == "suspend":
            user.is_active = False
            result["message"] = "User suspended successfully"
            
        elif action.action == "activate":
            user.is_active = True
            result["message"] = "User activated successfully"
            
        elif action.action == "verify":
            user.is_verified = True
            result["message"] = "User verified successfully"
            
        elif action.action == "reset_password":
            # Generate temporary password
            temp_password = self._generate_temp_password()
            user.password_hash = get_password_hash(temp_password)
            result["message"] = f"Password reset successfully. Temporary password: {temp_password}"
            
            # Invalidate all refresh tokens
            await redis_client.delete(f"refresh_token:{user.id}")
            
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid action"
            )
        
        user.updated_at = datetime.utcnow()
        await self.db.commit()
        
        # Log admin activity
        await self._log_admin_activity(
            admin_id=admin_id,
            action=f"user_{action.action}",
            resource_type="user",
            resource_id=user_id,
            details={
                "action": action.action,
                "reason": action.reason,
                "target_user": user.email
            }
        )
        
        result["success"] = True
        return result
    
    async def assign_fleet(
        self, 
        assignment: FleetAssignment, 
        admin_id: UUID
    ) -> Dict[str, Any]:
        """Assign bus and driver to a route for a trip."""
        # Validate bus exists and is active
        bus = await self._get_bus_by_id(assignment.bus_id)
        if not bus or not bus.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bus not found or inactive"
            )
        
        # Validate driver exists and has driver role
        driver = await self._get_user_by_id(assignment.driver_id)
        if not driver or driver.role != UserRole.DRIVER or not driver.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Driver not found or invalid"
            )
        
        # Validate route exists
        route = await self._get_route_by_id(assignment.route_id)
        if not route or not route.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Route not found or inactive"
            )
        
        # Check for conflicts (bus or driver already assigned at the same time)
        conflict_query = select(Trip).where(
            and_(
                or_(Trip.bus_id == assignment.bus_id, Trip.driver_id == assignment.driver_id),
                Trip.departure_time == assignment.departure_time,
                Trip.status.in_([TripStatus.SCHEDULED, TripStatus.BOARDING, TripStatus.IN_TRANSIT])
            )
        )
        
        conflict_result = await self.db.execute(conflict_query)
        if conflict_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Bus or driver already assigned at this time"
            )
        
        # Create new trip
        trip = Trip(
            route_id=assignment.route_id,
            bus_id=assignment.bus_id,
            driver_id=assignment.driver_id,
            departure_time=assignment.departure_time,
            fare=assignment.fare,
            available_seats=bus.capacity,
            status=TripStatus.SCHEDULED
        )
        
        self.db.add(trip)
        await self.db.commit()
        await self.db.refresh(trip)
        
        # Log admin activity
        await self._log_admin_activity(
            admin_id=admin_id,
            action="fleet_assignment",
            resource_type="trip",
            resource_id=trip.id,
            details={
                "bus_id": str(assignment.bus_id),
                "driver_id": str(assignment.driver_id),
                "route_id": str(assignment.route_id),
                "departure_time": assignment.departure_time.isoformat(),
                "fare": assignment.fare
            }
        )
        
        return {
            "success": True,
            "message": "Fleet assigned successfully",
            "trip_id": trip.id
        }
    
    async def get_live_trip_data(self) -> List[LiveTripData]:
        """Get live data for all active trips."""
        query = select(Trip).options(
            selectinload(Trip.route).selectinload(Route.origin_terminal),
            selectinload(Trip.route).selectinload(Route.destination_terminal),
            selectinload(Trip.bus),
            selectinload(Trip.driver),
            selectinload(Trip.bookings)
        ).where(
            Trip.status.in_([TripStatus.BOARDING, TripStatus.IN_TRANSIT])
        ).order_by(Trip.departure_time)
        
        result = await self.db.execute(query)
        trips = result.scalars().all()
        
        live_data = []
        for trip in trips:
            # Get latest location
            location_query = select(TripLocation).where(
                TripLocation.trip_id == trip.id
            ).order_by(desc(TripLocation.recorded_at)).limit(1)
            
            location_result = await self.db.execute(location_query)
            latest_location = location_result.scalar_one_or_none()
            
            current_location = None
            if latest_location:
                current_location = {
                    "latitude": float(latest_location.latitude),
                    "longitude": float(latest_location.longitude)
                }
            
            # Calculate passenger count
            passenger_count = sum(len(booking.seat_numbers) for booking in trip.bookings 
                                if booking.status == BookingStatus.CONFIRMED)
            
            # Route name
            route_name = f"{trip.route.origin_terminal.name} → {trip.route.destination_terminal.name}"
            
            live_data.append(LiveTripData(
                trip_id=trip.id,
                route_name=route_name,
                bus_license_plate=trip.bus.license_plate,
                driver_name=trip.driver.full_name,
                status=trip.status,
                current_location=current_location,
                passenger_count=passenger_count,
                departure_time=trip.departure_time,
                estimated_arrival=trip.arrival_time
            ))
        
        return live_data
    
    async def moderate_review(
        self, 
        review_id: UUID, 
        action: ReviewModerationAction, 
        admin_id: UUID
    ) -> Dict[str, Any]:
        """Moderate user reviews."""
        from app.models.tracking import Review
        
        # Get the review
        review_query = select(Review).where(Review.id == review_id)
        result = await self.db.execute(review_query)
        review = result.scalar_one_or_none()
        
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review not found"
            )
        
        # Apply moderation action
        if action.action == "approve":
            review.is_moderated = True
            message = "Review approved successfully"
            
        elif action.action == "reject":
            review.is_moderated = False
            # Could also add a rejected flag or hide the review
            message = "Review rejected successfully"
            
        elif action.action == "flag":
            # Add to flagged reviews (could use Redis or database flag)
            await self._flag_review_for_investigation(review_id, action.reason)
            message = "Review flagged for investigation"
            
        elif action.action == "hide":
            # Hide review from public view but keep for records
            review.is_moderated = False
            message = "Review hidden from public view"
            
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid moderation action"
            )
        
        await self.db.commit()
        
        # Log admin activity
        await self._log_admin_activity(
            admin_id=admin_id,
            action=f"review_{action.action}",
            resource_type="review",
            resource_id=review_id,
            details={
                "action": action.action,
                "reason": action.reason,
                "admin_notes": action.admin_notes,
                "review_rating": review.rating,
                "review_user_id": str(review.user_id)
            }
        )
        
        return {
            "success": True,
            "message": message
        }
    
    async def get_fraud_alerts(
        self, 
        page: int = 1, 
        page_size: int = 20,
        severity: Optional[str] = None,
        status: Optional[str] = None
    ) -> FraudAlertResponse:
        """Get fraud alerts with filtering and pagination."""
        # This would typically come from a fraud detection system
        # For now, we'll return mock data from Redis
        
        alerts_key = "fraud_alerts"
        alerts_data = await redis_client.get(alerts_key)
        
        if not alerts_data:
            # Initialize with empty list
            alerts = []
        else:
            alerts = json.loads(alerts_data)
        
        # Apply filters
        if severity:
            alerts = [alert for alert in alerts if alert.get("severity") == severity]
        
        if status:
            alerts = [alert for alert in alerts if alert.get("status") == status]
        
        # Apply pagination
        total_count = len(alerts)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_alerts = alerts[start_idx:end_idx]
        
        # Convert to FraudAlert objects
        fraud_alerts = []
        for alert_data in paginated_alerts:
            fraud_alerts.append(FraudAlert(**alert_data))
        
        return FraudAlertResponse(
            alerts=fraud_alerts,
            total_count=total_count,
            page=page,
            page_size=page_size
        )
    
    async def create_fraud_alert(
        self,
        alert_type: str,
        severity: str,
        description: str,
        user_id: Optional[UUID] = None,
        booking_id: Optional[UUID] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> FraudAlert:
        """Create a new fraud alert."""
        import uuid
        
        alert = FraudAlert(
            id=uuid.uuid4(),
            alert_type=alert_type,
            severity=severity,
            user_id=user_id,
            booking_id=booking_id,
            description=description,
            metadata=metadata or {},
            status="open",
            created_at=datetime.utcnow()
        )
        
        # Store in Redis
        alerts_key = "fraud_alerts"
        alerts_data = await redis_client.get(alerts_key)
        
        if alerts_data:
            alerts = json.loads(alerts_data)
        else:
            alerts = []
        
        # Convert alert to dict for JSON serialization
        alert_dict = alert.dict()
        alert_dict["id"] = str(alert_dict["id"])
        if alert_dict["user_id"]:
            alert_dict["user_id"] = str(alert_dict["user_id"])
        if alert_dict["booking_id"]:
            alert_dict["booking_id"] = str(alert_dict["booking_id"])
        alert_dict["created_at"] = alert_dict["created_at"].isoformat()
        
        alerts.append(alert_dict)
        
        # Keep only last 1000 alerts
        if len(alerts) > 1000:
            alerts = alerts[-1000:]
        
        await redis_client.set(alerts_key, json.dumps(alerts))
        
        return alert
    
    async def get_system_health(self) -> SystemHealth:
        """Get system health metrics."""
        # Database status
        try:
            await self.db.execute(text("SELECT 1"))
            database_status = "healthy"
        except Exception:
            database_status = "unhealthy"
        
        # Redis status
        try:
            if redis_client.redis:
                await redis_client.redis.ping()
                redis_status = "healthy"
            else:
                redis_status = "unhealthy"
        except Exception:
            redis_status = "unhealthy"
        
        # Mock other metrics (in production, these would come from monitoring systems)
        return SystemHealth(
            database_status=database_status,
            redis_status=redis_status,
            api_response_time=0.15,  # Mock value
            active_connections=42,   # Mock value
            memory_usage=65.5,       # Mock value
            cpu_usage=23.8,          # Mock value
            disk_usage=45.2,         # Mock value
            last_updated=datetime.utcnow()
        )
    
    # Helper methods
    
    async def _get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    
    async def _get_bus_by_id(self, bus_id: UUID) -> Optional[Bus]:
        """Get bus by ID."""
        result = await self.db.execute(select(Bus).where(Bus.id == bus_id))
        return result.scalar_one_or_none()
    
    async def _get_route_by_id(self, route_id: UUID) -> Optional[Route]:
        """Get route by ID."""
        result = await self.db.execute(select(Route).where(Route.id == route_id))
        return result.scalar_one_or_none()
    
    async def _get_fraud_alert_count(self) -> int:
        """Get count of open fraud alerts."""
        alerts_key = "fraud_alerts"
        alerts_data = await redis_client.get(alerts_key)
        
        if not alerts_data:
            return 0
        
        alerts = json.loads(alerts_data)
        return len([alert for alert in alerts if alert.get("status") == "open"])
    
    async def _log_admin_activity(
        self,
        admin_id: UUID,
        action: str,
        resource_type: str,
        resource_id: Optional[UUID] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> None:
        """Log admin activity to Redis."""
        import uuid
        
        log_entry = AdminActivityLog(
            id=uuid.uuid4(),
            admin_id=admin_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.utcnow()
        )
        
        # Store in Redis with expiration (keep logs for 90 days)
        log_key = f"admin_activity:{admin_id}:{datetime.utcnow().strftime('%Y%m%d')}"
        
        # Convert to dict for JSON serialization
        log_dict = log_entry.dict()
        log_dict["id"] = str(log_dict["id"])
        log_dict["admin_id"] = str(log_dict["admin_id"])
        if log_dict["resource_id"]:
            log_dict["resource_id"] = str(log_dict["resource_id"])
        log_dict["created_at"] = log_dict["created_at"].isoformat()
        
        # Get existing logs for the day
        existing_logs = await redis_client.get(log_key)
        if existing_logs:
            logs = json.loads(existing_logs)
        else:
            logs = []
        
        logs.append(log_dict)
        
        # Store with 90-day expiration
        await redis_client.setex(log_key, timedelta(days=90), json.dumps(logs))
    
    def _generate_temp_password(self, length: int = 12) -> str:
        """Generate temporary password."""
        characters = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(characters) for _ in range(length))
    
    async def _flag_review_for_investigation(self, review_id: UUID, reason: Optional[str] = None) -> None:
        """Flag a review for further investigation."""
        flagged_reviews_key = "flagged_reviews"
        
        # Get existing flagged reviews
        flagged_data = await redis_client.get(flagged_reviews_key)
        if flagged_data:
            flagged_reviews = json.loads(flagged_data)
        else:
            flagged_reviews = []
        
        # Add new flagged review
        flag_entry = {
            "review_id": str(review_id),
            "reason": reason,
            "flagged_at": datetime.utcnow().isoformat(),
            "status": "pending_investigation"
        }
        
        flagged_reviews.append(flag_entry)
        
        # Keep only last 500 flagged reviews
        if len(flagged_reviews) > 500:
            flagged_reviews = flagged_reviews[-500:]
        
        await redis_client.set(flagged_reviews_key, json.dumps(flagged_reviews))
    
    async def trigger_fraud_detection(self, user_id: UUID, booking_id: Optional[UUID] = None) -> None:
        """Trigger fraud detection checks for a user/booking."""
        # Check for multiple bookings in short time
        await self._check_rapid_booking_fraud(user_id)
        
        # Check for payment anomalies
        if booking_id:
            await self._check_payment_fraud(booking_id)
        
        # Check for suspicious user patterns
        await self._check_user_behavior_fraud(user_id)
    
    async def _check_rapid_booking_fraud(self, user_id: UUID) -> None:
        """Check for rapid booking patterns that might indicate fraud."""
        # Check bookings in last 10 minutes
        recent_time = datetime.utcnow() - timedelta(minutes=10)
        
        recent_bookings_result = await self.db.execute(
            select(func.count(Booking.id)).where(
                and_(
                    Booking.user_id == user_id,
                    Booking.created_at >= recent_time
                )
            )
        )
        recent_bookings = recent_bookings_result.scalar()
        
        if recent_bookings >= 5:  # 5 or more bookings in 10 minutes
            await self.create_fraud_alert(
                alert_type="rapid_booking",
                severity="high",
                description=f"User made {recent_bookings} bookings in 10 minutes",
                user_id=user_id
            )
    
    async def _check_payment_fraud(self, booking_id: UUID) -> None:
        """Check for payment-related fraud patterns."""
        # Get booking and payment info
        booking_query = select(Booking).options(
            selectinload(Booking.payments)
        ).where(Booking.id == booking_id)
        
        result = await self.db.execute(booking_query)
        booking = result.scalar_one_or_none()
        
        if not booking:
            return
        
        # Check for multiple failed payments
        failed_payments = [p for p in booking.payments if p.status == "failed"]
        if len(failed_payments) >= 3:
            await self.create_fraud_alert(
                alert_type="multiple_payment_failures",
                severity="medium",
                description=f"Booking has {len(failed_payments)} failed payment attempts",
                user_id=booking.user_id,
                booking_id=booking_id
            )
        
        # Check for unusual payment amounts
        if booking.total_amount > 1000:  # Unusually high amount
            await self.create_fraud_alert(
                alert_type="high_value_transaction",
                severity="medium",
                description=f"High value booking: ${booking.total_amount}",
                user_id=booking.user_id,
                booking_id=booking_id
            )
    
    async def _check_user_behavior_fraud(self, user_id: UUID) -> None:
        """Check for suspicious user behavior patterns."""
        # Check for account created recently with immediate high-value bookings
        user = await self._get_user_by_id(user_id)
        if not user:
            return
        
        account_age = datetime.utcnow() - user.created_at
        if account_age.days < 1:  # Account less than 1 day old
            # Check total booking value
            total_bookings_result = await self.db.execute(
                select(func.coalesce(func.sum(Booking.total_amount), 0)).where(
                    Booking.user_id == user_id
                )
            )
            total_amount = float(total_bookings_result.scalar() or 0)
            
            if total_amount > 500:  # New account with high spending
                await self.create_fraud_alert(
                    alert_type="new_account_high_spending",
                    severity="high",
                    description=f"New account (age: {account_age.hours}h) with ${total_amount} in bookings",
                    user_id=user_id
                )
    
    async def get_unmoderated_reviews(self, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """Get unmoderated reviews for admin review."""
        from app.models.tracking import Review
        
        offset = (page - 1) * page_size
        
        # Get unmoderated reviews with user and booking details
        query = select(Review).options(
            selectinload(Review.user),
            selectinload(Review.driver),
            selectinload(Review.booking).selectinload(Booking.trip).selectinload(Trip.route)
        ).where(Review.is_moderated == False).order_by(Review.created_at).offset(offset).limit(page_size)
        
        result = await self.db.execute(query)
        reviews = result.scalars().all()
        
        # Get total count
        count_query = select(func.count(Review.id)).where(Review.is_moderated == False)
        count_result = await self.db.execute(count_query)
        total_count = count_result.scalar()
        
        # Format reviews for response
        formatted_reviews = []
        for review in reviews:
            route_name = "Unknown Route"
            if (review.booking and review.booking.trip and review.booking.trip.route):
                route = review.booking.trip.route
                # We'll need to load terminals separately or adjust the query
                route_name = f"Route {route.id}"
            
            formatted_reviews.append({
                "id": review.id,
                "booking_id": review.booking_id,
                "user_name": review.user.full_name if review.user else "Unknown User",
                "driver_name": review.driver.full_name if review.driver else "Unknown Driver",
                "rating": review.rating,
                "comment": review.comment,
                "route_name": route_name,
                "created_at": review.created_at,
                "is_moderated": review.is_moderated
            })
        
        return {
            "reviews": formatted_reviews,
            "total_count": total_count,
            "page": page,
            "page_size": page_size
        }
    
    async def get_flagged_reviews(self) -> Dict[str, Any]:
        """Get reviews that have been flagged for investigation."""
        flagged_reviews_key = "flagged_reviews"
        flagged_data = await redis_client.get(flagged_reviews_key)
        
        if not flagged_data:
            return {"flagged_reviews": [], "total_count": 0}
        
        flagged_reviews = json.loads(flagged_data)
        
        # Get review details for flagged reviews
        detailed_reviews = []
        for flag_entry in flagged_reviews:
            if flag_entry.get("status") == "pending_investigation":
                review_id = UUID(flag_entry["review_id"])
                
                # Get review details
                from app.models.tracking import Review
                query = select(Review).options(
                    selectinload(Review.user),
                    selectinload(Review.driver)
                ).where(Review.id == review_id)
                
                result = await self.db.execute(query)
                review = result.scalar_one_or_none()
                
                if review:
                    detailed_reviews.append({
                        "id": review.id,
                        "user_name": review.user.full_name if review.user else "Unknown User",
                        "driver_name": review.driver.full_name if review.driver else "Unknown Driver",
                        "rating": review.rating,
                        "comment": review.comment,
                        "flagged_reason": flag_entry.get("reason"),
                        "flagged_at": flag_entry.get("flagged_at"),
                        "created_at": review.created_at
                    })
        
        return {
            "flagged_reviews": detailed_reviews,
            "total_count": len(detailed_reviews)
        }