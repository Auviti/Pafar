"""
Unit tests for cleanup tasks.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from app.tasks.cleanup_tasks import (
    cleanup_expired_reservations,
    cleanup_old_trip_locations,
    cleanup_old_notifications,
    cleanup_inactive_user_sessions,
    cleanup_temporary_files,
    generate_cleanup_report,
    _cleanup_expired_reservations_async,
    _cleanup_old_trip_locations_async,
    _generate_cleanup_report_async
)


class TestCleanupTasks:
    """Test cases for cleanup tasks."""
    
    @pytest.fixture
    def mock_session(self):
        """Mock database session."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        return session
    
    @pytest.fixture
    def expired_bookings(self):
        """Mock expired bookings."""
        booking1 = Mock()
        booking1.booking_reference = "BK123456"
        booking1.status = "pending"
        booking1.payment_status = "pending"
        booking1.created_at = datetime.utcnow() - timedelta(minutes=15)
        
        booking2 = Mock()
        booking2.booking_reference = "BK789012"
        booking2.status = "pending"
        booking2.payment_status = "pending"
        booking2.created_at = datetime.utcnow() - timedelta(minutes=20)
        
        return [booking1, booking2]
    
    @patch('app.tasks.cleanup_tasks.asyncio.run')
    def test_cleanup_expired_reservations_success(self, mock_asyncio_run):
        """Test successful cleanup of expired reservations."""
        # Arrange
        expected_result = {
            "success": True,
            "message": "Cleaned up 2 expired reservations",
            "cleaned_count": 2,
            "booking_references": ["BK123456", "BK789012"],
            "timestamp": datetime.utcnow().isoformat()
        }
        mock_asyncio_run.return_value = expected_result
        
        # Act
        result = cleanup_expired_reservations()
        
        # Assert
        assert result["success"] is True
        assert result["cleaned_count"] == 2
        assert len(result["booking_references"]) == 2
        mock_asyncio_run.assert_called_once()
    
    @patch('app.tasks.cleanup_tasks.asyncio.run')
    def test_cleanup_expired_reservations_failure(self, mock_asyncio_run):
        """Test cleanup failure handling."""
        # Arrange
        mock_asyncio_run.side_effect = Exception("Database error")
        
        # Act
        result = cleanup_expired_reservations()
        
        # Assert
        assert result["success"] is False
        assert "Failed to cleanup" in result["message"]
        assert result["cleaned_count"] == 0
    
    @patch('app.tasks.cleanup_tasks.get_async_session')
    @pytest.mark.asyncio
    async def test_cleanup_expired_reservations_async_success(
        self, mock_get_session, mock_session, expired_bookings
    ):
        """Test async cleanup of expired reservations."""
        # Arrange
        mock_get_session.return_value.__aenter__.return_value = mock_session
        
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = expired_bookings
        mock_session.execute.return_value = mock_result
        
        # Act
        result = await _cleanup_expired_reservations_async()
        
        # Assert
        assert result["success"] is True
        assert result["cleaned_count"] == 2
        assert "BK123456" in result["booking_references"]
        assert "BK789012" in result["booking_references"]
        mock_session.commit.assert_called_once()
        
        # Check that booking statuses were updated
        for booking in expired_bookings:
            assert booking.status == "expired"
    
    @patch('app.tasks.cleanup_tasks.get_async_session')
    @pytest.mark.asyncio
    async def test_cleanup_expired_reservations_async_failure(
        self, mock_get_session, mock_session
    ):
        """Test async cleanup failure handling."""
        # Arrange
        mock_get_session.return_value.__aenter__.return_value = mock_session
        mock_session.execute.side_effect = Exception("Database error")
        
        # Act & Assert
        with pytest.raises(Exception, match="Database error"):
            await _cleanup_expired_reservations_async()
        
        mock_session.rollback.assert_called_once()
    
    @patch('app.tasks.cleanup_tasks.asyncio.run')
    def test_cleanup_old_trip_locations_success(self, mock_asyncio_run):
        """Test successful cleanup of old trip locations."""
        # Arrange
        expected_result = {
            "success": True,
            "message": "Cleaned up 150 old trip location records",
            "cleaned_count": 150,
            "cutoff_date": (datetime.utcnow() - timedelta(days=7)).isoformat(),
            "timestamp": datetime.utcnow().isoformat()
        }
        mock_asyncio_run.return_value = expected_result
        
        # Act
        result = cleanup_old_trip_locations()
        
        # Assert
        assert result["success"] is True
        assert result["cleaned_count"] == 150
        assert "cutoff_date" in result
    
    @patch('app.tasks.cleanup_tasks.get_async_session')
    @pytest.mark.asyncio
    async def test_cleanup_old_trip_locations_async_success(
        self, mock_get_session, mock_session
    ):
        """Test async cleanup of old trip locations."""
        # Arrange
        mock_get_session.return_value.__aenter__.return_value = mock_session
        
        mock_result = Mock()
        mock_result.rowcount = 75
        mock_session.execute.return_value = mock_result
        
        # Act
        result = await _cleanup_old_trip_locations_async()
        
        # Assert
        assert result["success"] is True
        assert result["cleaned_count"] == 75
        mock_session.commit.assert_called_once()
    
    @patch('app.tasks.cleanup_tasks.asyncio.run')
    def test_cleanup_old_notifications_success(self, mock_asyncio_run):
        """Test cleanup of old notifications (placeholder)."""
        # Arrange
        expected_result = {
            "success": True,
            "message": "Cleaned up 0 old notification records",
            "cleaned_count": 0,
            "cutoff_date": (datetime.utcnow() - timedelta(days=30)).isoformat(),
            "timestamp": datetime.utcnow().isoformat(),
            "note": "Notification table not yet implemented - placeholder cleanup"
        }
        mock_asyncio_run.return_value = expected_result
        
        # Act
        result = cleanup_old_notifications()
        
        # Assert
        assert result["success"] is True
        assert "placeholder" in result["note"]
    
    @patch('app.tasks.cleanup_tasks.asyncio.run')
    def test_cleanup_inactive_user_sessions_success(self, mock_asyncio_run):
        """Test cleanup of inactive user sessions."""
        # Arrange
        expected_result = {
            "success": True,
            "message": "Cleaned up 5 inactive user sessions",
            "cleaned_count": 5,
            "total_sessions_checked": 20,
            "cutoff_date": (datetime.utcnow() - timedelta(days=30)).isoformat(),
            "timestamp": datetime.utcnow().isoformat()
        }
        mock_asyncio_run.return_value = expected_result
        
        # Act
        result = cleanup_inactive_user_sessions()
        
        # Assert
        assert result["success"] is True
        assert result["cleaned_count"] == 5
        assert result["total_sessions_checked"] == 20
    
    @patch('app.tasks.cleanup_tasks.redis_client')
    @pytest.mark.asyncio
    async def test_cleanup_inactive_user_sessions_async_success(self, mock_redis):
        """Test async cleanup of inactive user sessions."""
        # Arrange
        session_keys = ["session:user1", "session:user2", "session:user3"]
        mock_redis.keys.return_value = session_keys
        
        # Mock session data - some active, some inactive
        old_session = {
            "user_id": "user1",
            "last_activity": (datetime.utcnow() - timedelta(days=35)).isoformat()
        }
        recent_session = {
            "user_id": "user2", 
            "last_activity": (datetime.utcnow() - timedelta(days=5)).isoformat()
        }
        
        mock_redis.get_json.side_effect = [old_session, recent_session, None]
        mock_redis.delete.return_value = True
        
        # Act
        from app.tasks.cleanup_tasks import _cleanup_inactive_user_sessions_async
        result = await _cleanup_inactive_user_sessions_async()
        
        # Assert
        assert result["success"] is True
        assert result["cleaned_count"] == 1  # Only old_session should be deleted
        assert result["total_sessions_checked"] == 3
        mock_redis.delete.assert_called_once_with("session:user1")
    
    @patch('os.path.exists')
    @patch('glob.glob')
    @patch('os.path.getmtime')
    @patch('os.remove')
    def test_cleanup_temporary_files_success(
        self, mock_remove, mock_getmtime, mock_glob, mock_exists
    ):
        """Test cleanup of temporary files."""
        # Arrange
        mock_exists.return_value = True
        mock_glob.return_value = ["/tmp/pafar_receipts/old.pdf", "/tmp/pafar_receipts/new.pdf"]
        
        # Mock file times - one old, one recent
        old_time = (datetime.utcnow() - timedelta(hours=30)).timestamp()
        recent_time = (datetime.utcnow() - timedelta(hours=1)).timestamp()
        mock_getmtime.side_effect = [old_time, recent_time]
        
        # Act
        result = cleanup_temporary_files()
        
        # Assert
        assert result["success"] is True
        assert result["cleaned_count"] == 1  # Only old file should be removed
        mock_remove.assert_called_once_with("/tmp/pafar_receipts/old.pdf")
    
    @patch('os.path.exists')
    def test_cleanup_temporary_files_no_directory(self, mock_exists):
        """Test cleanup when temporary directory doesn't exist."""
        # Arrange
        mock_exists.return_value = False
        
        # Act
        result = cleanup_temporary_files()
        
        # Assert
        assert result["success"] is True
        assert result["cleaned_count"] == 0
        assert "does not exist" in result["message"]
    
    @patch('app.tasks.cleanup_tasks.asyncio.run')
    def test_generate_cleanup_report_success(self, mock_asyncio_run):
        """Test generation of cleanup report."""
        # Arrange
        expected_result = {
            "success": True,
            "message": "Cleanup report generated successfully",
            "report": {
                "timestamp": datetime.utcnow().isoformat(),
                "database_stats": {
                    "bookings": {"total": 100, "pending": 5, "expired": 2},
                    "trip_locations": {"recent_24h": 50, "older_than_24h": 200, "total": 250}
                },
                "recommendations": ["Database is in good health."]
            }
        }
        mock_asyncio_run.return_value = expected_result
        
        # Act
        result = generate_cleanup_report()
        
        # Assert
        assert result["success"] is True
        assert "report" in result
        assert "database_stats" in result["report"]
        assert "recommendations" in result["report"]
    
    @patch('app.tasks.cleanup_tasks.get_async_session')
    @pytest.mark.asyncio
    async def test_generate_cleanup_report_async_success(
        self, mock_get_session, mock_session
    ):
        """Test async generation of cleanup report."""
        # Arrange
        mock_get_session.return_value.__aenter__.return_value = mock_session
        
        # Mock database query results
        pending_result = Mock()
        pending_result.scalars.return_value.all.return_value = [Mock()] * 5
        
        expired_result = Mock()
        expired_result.scalars.return_value.all.return_value = [Mock()] * 2
        
        total_result = Mock()
        total_result.scalars.return_value.all.return_value = [Mock()] * 100
        
        recent_locations_result = Mock()
        recent_locations_result.scalars.return_value.all.return_value = [Mock()] * 50
        
        old_locations_result = Mock()
        old_locations_result.scalars.return_value.all.return_value = [Mock()] * 200
        
        mock_session.execute.side_effect = [
            pending_result, expired_result, total_result,
            recent_locations_result, old_locations_result
        ]
        
        # Act
        result = await _generate_cleanup_report_async()
        
        # Assert
        assert result["success"] is True
        assert result["report"]["database_stats"]["bookings"]["total"] == 100
        assert result["report"]["database_stats"]["bookings"]["pending"] == 5
        assert result["report"]["database_stats"]["bookings"]["expired"] == 2
        assert result["report"]["database_stats"]["trip_locations"]["recent_24h"] == 50
        assert result["report"]["database_stats"]["trip_locations"]["older_than_24h"] == 200
        assert "Database is in good health." in result["report"]["recommendations"]
    
    @patch('app.tasks.cleanup_tasks.get_async_session')
    @pytest.mark.asyncio
    async def test_generate_cleanup_report_with_warnings(
        self, mock_get_session, mock_session
    ):
        """Test cleanup report generation with warning conditions."""
        # Arrange
        mock_get_session.return_value.__aenter__.return_value = mock_session
        
        # Mock high numbers that should trigger warnings
        pending_result = Mock()
        pending_result.scalars.return_value.all.return_value = [Mock()] * 150  # > 100
        
        expired_result = Mock()
        expired_result.scalars.return_value.all.return_value = [Mock()] * 75   # > 50
        
        total_result = Mock()
        total_result.scalars.return_value.all.return_value = [Mock()] * 500
        
        recent_locations_result = Mock()
        recent_locations_result.scalars.return_value.all.return_value = [Mock()] * 100
        
        old_locations_result = Mock()
        old_locations_result.scalars.return_value.all.return_value = [Mock()] * 15000  # > 10000
        
        mock_session.execute.side_effect = [
            pending_result, expired_result, total_result,
            recent_locations_result, old_locations_result
        ]
        
        # Act
        result = await _generate_cleanup_report_async()
        
        # Assert
        assert result["success"] is True
        recommendations = result["report"]["recommendations"]
        
        # Check that warnings are generated
        assert any("pending bookings" in rec for rec in recommendations)
        assert any("expired bookings" in rec for rec in recommendations)
        assert any("old location records" in rec for rec in recommendations)
    
    def test_cleanup_task_error_handling(self):
        """Test error handling in cleanup tasks."""
        # Test that all cleanup tasks handle exceptions gracefully
        with patch('app.tasks.cleanup_tasks.asyncio.run', side_effect=Exception("Test error")):
            
            # Test each cleanup task
            tasks = [
                cleanup_expired_reservations,
                cleanup_old_trip_locations,
                cleanup_old_notifications,
                cleanup_inactive_user_sessions,
                generate_cleanup_report
            ]
            
            for task in tasks:
                result = task()
                assert result["success"] is False
                assert "Failed to" in result["message"] or "Error" in result["message"]