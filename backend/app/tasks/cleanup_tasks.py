"""
Periodic cleanup tasks for expired reservations and old data.
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List
from sqlalchemy import select, delete, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from celery import current_task
from ..core.celery_app import celery_app
from ..core.database import AsyncSessionLocal
from ..models.booking import Booking
from ..models.tracking import TripLocation
from ..models.user import User


@celery_app.task(bind=True)
def cleanup_expired_reservations(self) -> Dict[str, Any]:
    """
    Clean up expired seat reservations that haven't been confirmed.
    Runs every 5 minutes to free up temporarily reserved seats.
    
    Returns:
        Dict with cleanup statistics
    """
    try:
        import asyncio
        return asyncio.run(_cleanup_expired_reservations_async())
    except Exception as exc:
        return {
            "success": False,
            "message": f"Failed to cleanup expired reservations: {str(exc)}",
            "cleaned_count": 0
        }


async def _cleanup_expired_reservations_async() -> Dict[str, Any]:
    """Async implementation of expired reservations cleanup."""
    async with AsyncSessionLocal() as session:
        try:
            # Find bookings that are in 'pending' status and older than 10 minutes
            expiry_time = datetime.utcnow() - timedelta(minutes=10)
            
            # Query for expired pending bookings
            stmt = select(Booking).where(
                and_(
                    Booking.status == "pending",
                    Booking.payment_status == "pending",
                    Booking.created_at < expiry_time
                )
            )
            
            result = await session.execute(stmt)
            expired_bookings = result.scalars().all()
            
            cleaned_count = 0
            booking_refs = []
            
            for booking in expired_bookings:
                # Update booking status to expired
                booking.status = "expired"
                booking.updated_at = datetime.utcnow()
                
                booking_refs.append(booking.booking_reference)
                cleaned_count += 1
            
            await session.commit()
            
            return {
                "success": True,
                "message": f"Cleaned up {cleaned_count} expired reservations",
                "cleaned_count": cleaned_count,
                "booking_references": booking_refs,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            await session.rollback()
            raise e


@celery_app.task(bind=True)
def cleanup_old_trip_locations(self) -> Dict[str, Any]:
    """
    Clean up old trip location records older than 7 days.
    Keeps the database size manageable by removing historical location data.
    
    Returns:
        Dict with cleanup statistics
    """
    try:
        import asyncio
        return asyncio.run(_cleanup_old_trip_locations_async())
    except Exception as exc:
        return {
            "success": False,
            "message": f"Failed to cleanup old trip locations: {str(exc)}",
            "cleaned_count": 0
        }


async def _cleanup_old_trip_locations_async() -> Dict[str, Any]:
    """Async implementation of old trip locations cleanup."""
    async with AsyncSessionLocal() as session:
        try:
            # Delete location records older than 7 days
            cutoff_time = datetime.utcnow() - timedelta(days=7)
            
            stmt = delete(TripLocation).where(
                TripLocation.recorded_at < cutoff_time
            )
            
            result = await session.execute(stmt)
            cleaned_count = result.rowcount
            
            await session.commit()
            
            return {
                "success": True,
                "message": f"Cleaned up {cleaned_count} old trip location records",
                "cleaned_count": cleaned_count,
                "cutoff_date": cutoff_time.isoformat(),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            await session.rollback()
            raise e


@celery_app.task(bind=True)
def cleanup_old_notifications(self) -> Dict[str, Any]:
    """
    Clean up old notification records older than 30 days.
    Maintains notification history while preventing database bloat.
    
    Returns:
        Dict with cleanup statistics
    """
    try:
        import asyncio
        return asyncio.run(_cleanup_old_notifications_async())
    except Exception as exc:
        return {
            "success": False,
            "message": f"Failed to cleanup old notifications: {str(exc)}",
            "cleaned_count": 0
        }


async def _cleanup_old_notifications_async() -> Dict[str, Any]:
    """Async implementation of old notifications cleanup."""
    # Note: This assumes you have a notifications table
    # If not implemented yet, this will be a placeholder
    
    try:
        # Placeholder for notification cleanup
        # In a real implementation, you would:
        # 1. Query old notification records
        # 2. Delete records older than 30 days
        # 3. Keep important notifications (booking confirmations, etc.)
        
        cutoff_time = datetime.utcnow() - timedelta(days=30)
        cleaned_count = 0  # Placeholder
        
        return {
            "success": True,
            "message": f"Cleaned up {cleaned_count} old notification records",
            "cleaned_count": cleaned_count,
            "cutoff_date": cutoff_time.isoformat(),
            "timestamp": datetime.utcnow().isoformat(),
            "note": "Notification table not yet implemented - placeholder cleanup"
        }
        
    except Exception as e:
        raise e


@celery_app.task(bind=True)
def cleanup_inactive_user_sessions(self) -> Dict[str, Any]:
    """
    Clean up inactive user sessions from Redis.
    Removes session data for users who haven't been active for 30 days.
    
    Returns:
        Dict with cleanup statistics
    """
    try:
        import asyncio
        return asyncio.run(_cleanup_inactive_user_sessions_async())
    except Exception as exc:
        return {
            "success": False,
            "message": f"Failed to cleanup inactive user sessions: {str(exc)}",
            "cleaned_count": 0
        }


async def _cleanup_inactive_user_sessions_async() -> Dict[str, Any]:
    """Async implementation of inactive user sessions cleanup."""
    from ..core.redis import redis_client
    
    try:
        # Get all session keys
        session_keys = await redis_client.keys("session:*")
        
        cleaned_count = 0
        cutoff_time = datetime.utcnow() - timedelta(days=30)
        
        for key in session_keys:
            # Get session data
            session_data = await redis_client.get_json(key)
            
            if session_data:
                last_activity = session_data.get("last_activity")
                if last_activity:
                    last_activity_dt = datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
                    
                    if last_activity_dt < cutoff_time:
                        await redis_client.delete(key)
                        cleaned_count += 1
        
        return {
            "success": True,
            "message": f"Cleaned up {cleaned_count} inactive user sessions",
            "cleaned_count": cleaned_count,
            "total_sessions_checked": len(session_keys),
            "cutoff_date": cutoff_time.isoformat(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise e


@celery_app.task(bind=True)
def cleanup_temporary_files(self) -> Dict[str, Any]:
    """
    Clean up temporary files like generated receipts older than 24 hours.
    
    Returns:
        Dict with cleanup statistics
    """
    try:
        import os
        import glob
        
        temp_dir = "/tmp/pafar_receipts"  # Adjust path as needed
        if not os.path.exists(temp_dir):
            return {
                "success": True,
                "message": "Temporary directory does not exist",
                "cleaned_count": 0
            }
        
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        cleaned_count = 0
        
        # Find all PDF files in temp directory
        pdf_files = glob.glob(os.path.join(temp_dir, "*.pdf"))
        
        for file_path in pdf_files:
            try:
                # Get file modification time
                file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                
                if file_mtime < cutoff_time:
                    os.remove(file_path)
                    cleaned_count += 1
                    
            except OSError:
                # File might have been deleted by another process
                continue
        
        return {
            "success": True,
            "message": f"Cleaned up {cleaned_count} temporary files",
            "cleaned_count": cleaned_count,
            "cutoff_time": cutoff_time.isoformat(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        return {
            "success": False,
            "message": f"Failed to cleanup temporary files: {str(exc)}",
            "cleaned_count": 0
        }


@celery_app.task(bind=True)
def generate_cleanup_report(self) -> Dict[str, Any]:
    """
    Generate a comprehensive cleanup report with database statistics.
    
    Returns:
        Dict with database statistics and cleanup recommendations
    """
    try:
        import asyncio
        return asyncio.run(_generate_cleanup_report_async())
    except Exception as exc:
        return {
            "success": False,
            "message": f"Failed to generate cleanup report: {str(exc)}"
        }


async def _generate_cleanup_report_async() -> Dict[str, Any]:
    """Async implementation of cleanup report generation."""
    async with AsyncSessionLocal() as session:
        try:
            report = {
                "timestamp": datetime.utcnow().isoformat(),
                "database_stats": {},
                "recommendations": []
            }
            
            # Count pending bookings
            pending_stmt = select(Booking).where(Booking.status == "pending")
            pending_result = await session.execute(pending_stmt)
            pending_count = len(pending_result.scalars().all())
            
            # Count expired bookings
            expired_stmt = select(Booking).where(Booking.status == "expired")
            expired_result = await session.execute(expired_stmt)
            expired_count = len(expired_result.scalars().all())
            
            # Count total bookings
            total_stmt = select(Booking)
            total_result = await session.execute(total_stmt)
            total_bookings = len(total_result.scalars().all())
            
            # Count trip locations (last 24 hours vs older)
            recent_time = datetime.utcnow() - timedelta(hours=24)
            recent_locations_stmt = select(TripLocation).where(
                TripLocation.recorded_at >= recent_time
            )
            recent_locations_result = await session.execute(recent_locations_stmt)
            recent_locations_count = len(recent_locations_result.scalars().all())
            
            old_locations_stmt = select(TripLocation).where(
                TripLocation.recorded_at < recent_time
            )
            old_locations_result = await session.execute(old_locations_stmt)
            old_locations_count = len(old_locations_result.scalars().all())
            
            report["database_stats"] = {
                "bookings": {
                    "total": total_bookings,
                    "pending": pending_count,
                    "expired": expired_count
                },
                "trip_locations": {
                    "recent_24h": recent_locations_count,
                    "older_than_24h": old_locations_count,
                    "total": recent_locations_count + old_locations_count
                }
            }
            
            # Generate recommendations
            if pending_count > 100:
                report["recommendations"].append(
                    "High number of pending bookings detected. Consider reviewing payment flow."
                )
            
            if expired_count > 50:
                report["recommendations"].append(
                    "Many expired bookings found. Cleanup task is working effectively."
                )
            
            if old_locations_count > 10000:
                report["recommendations"].append(
                    "Large number of old location records. Consider more frequent cleanup."
                )
            
            if not report["recommendations"]:
                report["recommendations"].append("Database is in good health.")
            
            return {
                "success": True,
                "message": "Cleanup report generated successfully",
                "report": report
            }
            
        except Exception as e:
            raise e