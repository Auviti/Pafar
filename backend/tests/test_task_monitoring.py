"""
Unit tests for task monitoring utilities.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from app.utils.task_monitoring import TaskMonitor, TaskHealthChecker, task_monitor, health_checker


class TestTaskMonitor:
    """Test cases for TaskMonitor class."""
    
    @pytest.fixture
    def monitor(self):
        """Create TaskMonitor instance for testing."""
        return TaskMonitor()
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client."""
        redis_mock = AsyncMock()
        return redis_mock
    
    @pytest.mark.asyncio
    async def test_log_task_start(self, monitor, mock_redis):
        """Test logging task start event."""
        # Arrange
        monitor.redis = mock_redis
        task_id = "task123"
        task_name = "test_task"
        args = ("arg1", "arg2")
        kwargs = {"key": "value"}
        
        # Act
        await monitor.log_task_start(task_id, task_name, args, kwargs)
        
        # Assert
        mock_redis.set_json.assert_called_once()
        call_args = mock_redis.set_json.call_args
        
        assert call_args[0][0] == f"task_log:{task_id}"
        task_info = call_args[0][1]
        assert task_info["task_id"] == task_id
        assert task_info["task_name"] == task_name
        assert task_info["args"] == args
        assert task_info["kwargs"] == kwargs
        assert task_info["status"] == "started"
        assert call_args[1]["expire"] == 86400
    
    @pytest.mark.asyncio
    async def test_log_task_success(self, monitor, mock_redis):
        """Test logging task success event."""
        # Arrange
        monitor.redis = mock_redis
        task_id = "task123"
        result = {"success": True}
        execution_time = 5.5
        
        existing_task_info = {
            "task_id": task_id,
            "status": "started",
            "started_at": datetime.utcnow().isoformat()
        }
        mock_redis.get_json.return_value = existing_task_info
        
        # Act
        await monitor.log_task_success(task_id, result, execution_time)
        
        # Assert
        mock_redis.get_json.assert_called_once_with(f"task_log:{task_id}")
        mock_redis.set_json.assert_called_once()
        
        call_args = mock_redis.set_json.call_args
        updated_info = call_args[0][1]
        assert updated_info["status"] == "success"
        assert updated_info["result"] == result
        assert updated_info["execution_time_seconds"] == execution_time
        assert "completed_at" in updated_info
    
    @pytest.mark.asyncio
    async def test_log_task_failure(self, monitor, mock_redis):
        """Test logging task failure event."""
        # Arrange
        monitor.redis = mock_redis
        task_id = "task123"
        error = "Test error"
        traceback = "Traceback..."
        
        existing_task_info = {
            "task_id": task_id,
            "status": "started"
        }
        mock_redis.get_json.return_value = existing_task_info
        
        # Act
        await monitor.log_task_failure(task_id, error, traceback)
        
        # Assert
        assert mock_redis.set_json.call_count == 2  # Update log and create failure record
        
        # Check failure record
        failure_call = [call for call in mock_redis.set_json.call_args_list 
                       if call[0][0].startswith("task_failure:")][0]
        failure_info = failure_call[0][1]
        assert failure_info["status"] == "failed"
        assert failure_info["error"] == error
        assert failure_info["traceback"] == traceback
    
    @pytest.mark.asyncio
    async def test_log_task_retry(self, monitor, mock_redis):
        """Test logging task retry event."""
        # Arrange
        monitor.redis = mock_redis
        task_id = "task123"
        retry_count = 2
        next_retry = datetime.utcnow() + timedelta(minutes=5)
        
        existing_task_info = {"task_id": task_id, "status": "started"}
        mock_redis.get_json.return_value = existing_task_info
        
        # Act
        await monitor.log_task_retry(task_id, retry_count, next_retry)
        
        # Assert
        mock_redis.set_json.assert_called_once()
        call_args = mock_redis.set_json.call_args
        updated_info = call_args[0][1]
        assert updated_info["status"] == "retrying"
        assert updated_info["retry_count"] == retry_count
        assert updated_info["next_retry_at"] == next_retry.isoformat()
    
    @pytest.mark.asyncio
    async def test_get_task_status(self, monitor, mock_redis):
        """Test getting task status."""
        # Arrange
        monitor.redis = mock_redis
        task_id = "task123"
        expected_status = {"task_id": task_id, "status": "success"}
        mock_redis.get_json.return_value = expected_status
        
        # Act
        result = await monitor.get_task_status(task_id)
        
        # Assert
        assert result == expected_status
        mock_redis.get_json.assert_called_once_with(f"task_log:{task_id}")
    
    @pytest.mark.asyncio
    async def test_get_failed_tasks(self, monitor, mock_redis):
        """Test getting failed tasks."""
        # Arrange
        monitor.redis = mock_redis
        mock_redis.keys.return_value = ["task_failure:task1", "task_failure:task2"]
        
        recent_failure = {
            "task_id": "task1",
            "failed_at": (datetime.utcnow() - timedelta(hours=2)).isoformat()
        }
        old_failure = {
            "task_id": "task2", 
            "failed_at": (datetime.utcnow() - timedelta(hours=30)).isoformat()
        }
        
        mock_redis.get_json.side_effect = [recent_failure, old_failure]
        
        # Act
        result = await monitor.get_failed_tasks(hours=24)
        
        # Assert
        assert len(result) == 1  # Only recent failure should be returned
        assert result[0]["task_id"] == "task1"
    
    @pytest.mark.asyncio
    async def test_get_task_statistics(self, monitor, mock_redis):
        """Test getting task statistics."""
        # Arrange
        monitor.redis = mock_redis
        mock_redis.keys.return_value = ["task_log:task1", "task_log:task2", "task_log:task3"]
        
        # Mock task data
        successful_task = {
            "task_name": "email_task",
            "status": "success",
            "started_at": datetime.utcnow().isoformat(),
            "execution_time_seconds": 2.5
        }
        failed_task = {
            "task_name": "sms_task",
            "status": "failed",
            "started_at": datetime.utcnow().isoformat()
        }
        running_task = {
            "task_name": "email_task",
            "status": "started",
            "started_at": datetime.utcnow().isoformat()
        }
        
        mock_redis.get_json.side_effect = [successful_task, failed_task, running_task]
        
        # Act
        result = await monitor.get_task_statistics(hours=24)
        
        # Assert
        assert result["total_tasks"] == 3
        assert result["successful_tasks"] == 1
        assert result["failed_tasks"] == 1
        assert result["running_tasks"] == 1
        assert result["average_execution_time"] == 2.5
        assert "email_task" in result["task_types"]
        assert result["task_types"]["email_task"]["total"] == 2


class TestTaskHealthChecker:
    """Test cases for TaskHealthChecker class."""
    
    @pytest.fixture
    def health_checker(self):
        """Create TaskHealthChecker instance for testing."""
        return TaskHealthChecker()
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client."""
        return AsyncMock()
    
    @patch('app.utils.task_monitoring.celery_app.control.inspect')
    @pytest.mark.asyncio
    async def test_check_worker_health_healthy(self, mock_inspect, health_checker):
        """Test worker health check when workers are healthy."""
        # Arrange
        mock_inspect_instance = Mock()
        mock_inspect_instance.active.return_value = {
            "worker1": [{"id": "task1"}, {"id": "task2"}],
            "worker2": [{"id": "task3"}]
        }
        mock_inspect_instance.registered.return_value = {
            "worker1": ["task_type1", "task_type2"],
            "worker2": ["task_type1"]
        }
        mock_inspect.return_value = mock_inspect_instance
        
        # Act
        result = await health_checker.check_worker_health()
        
        # Assert
        assert result["healthy"] is True
        assert result["total_workers"] == 2
        assert len(result["workers"]) == 2
        assert result["workers"][0]["name"] == "worker1"
        assert result["workers"][0]["active_tasks"] == 2
    
    @patch('app.utils.task_monitoring.celery_app.control.inspect')
    @pytest.mark.asyncio
    async def test_check_worker_health_no_workers(self, mock_inspect, health_checker):
        """Test worker health check when no workers are active."""
        # Arrange
        mock_inspect_instance = Mock()
        mock_inspect_instance.active.return_value = None
        mock_inspect.return_value = mock_inspect_instance
        
        # Act
        result = await health_checker.check_worker_health()
        
        # Assert
        assert result["healthy"] is False
        assert "No active workers" in result["message"]
        assert result["total_workers"] == 0
    
    @pytest.mark.asyncio
    async def test_check_queue_health_healthy(self, health_checker, mock_redis):
        """Test queue health check when queues are healthy."""
        # Arrange
        health_checker.redis = mock_redis
        mock_redis.redis.llen.side_effect = [5, 10, 2, 0, 1]  # Queue lengths
        
        # Act
        result = await health_checker.check_queue_health()
        
        # Assert
        assert result["healthy"] is True
        assert result["total_queued_tasks"] == 18
        assert len(result["queues"]) == 5
        assert all(queue_info["healthy"] for queue_info in result["queues"].values())
    
    @pytest.mark.asyncio
    async def test_check_queue_health_unhealthy(self, health_checker, mock_redis):
        """Test queue health check when queues are unhealthy."""
        # Arrange
        health_checker.redis = mock_redis
        mock_redis.redis.llen.side_effect = [1500, 10, 2, 0, 1]  # One queue too long
        
        # Act
        result = await health_checker.check_queue_health()
        
        # Assert
        assert result["healthy"] is False
        assert result["total_queued_tasks"] == 1513
        assert not result["queues"]["email"]["healthy"]
    
    @pytest.mark.asyncio
    async def test_check_task_failure_rate_healthy(self, health_checker):
        """Test task failure rate check when rate is healthy."""
        # Arrange
        with patch.object(health_checker.monitor, 'get_task_statistics') as mock_stats:
            mock_stats.return_value = {
                "total_tasks": 100,
                "failed_tasks": 5
            }
            
            # Act
            result = await health_checker.check_task_failure_rate(hours=1)
            
            # Assert
            assert result["healthy"] is True
            assert result["failure_rate_percent"] == 5.0
            assert result["total_tasks"] == 100
            assert result["failed_tasks"] == 5
    
    @pytest.mark.asyncio
    async def test_check_task_failure_rate_unhealthy(self, health_checker):
        """Test task failure rate check when rate is unhealthy."""
        # Arrange
        with patch.object(health_checker.monitor, 'get_task_statistics') as mock_stats:
            mock_stats.return_value = {
                "total_tasks": 100,
                "failed_tasks": 15  # 15% failure rate
            }
            
            # Act
            result = await health_checker.check_task_failure_rate(hours=1)
            
            # Assert
            assert result["healthy"] is False
            assert result["failure_rate_percent"] == 15.0
    
    @pytest.mark.asyncio
    async def test_check_task_failure_rate_no_tasks(self, health_checker):
        """Test task failure rate check when no tasks exist."""
        # Arrange
        with patch.object(health_checker.monitor, 'get_task_statistics') as mock_stats:
            mock_stats.return_value = {
                "total_tasks": 0,
                "failed_tasks": 0
            }
            
            # Act
            result = await health_checker.check_task_failure_rate(hours=1)
            
            # Assert
            assert result["healthy"] is True
            assert result["failure_rate_percent"] == 0
    
    @pytest.mark.asyncio
    async def test_get_comprehensive_health_report(self, health_checker):
        """Test comprehensive health report generation."""
        # Arrange
        with patch.object(health_checker, 'check_worker_health') as mock_worker_health, \
             patch.object(health_checker, 'check_queue_health') as mock_queue_health, \
             patch.object(health_checker, 'check_task_failure_rate') as mock_failure_rate, \
             patch.object(health_checker.monitor, 'get_task_statistics') as mock_stats:
            
            mock_worker_health.return_value = {"healthy": True}
            mock_queue_health.return_value = {"healthy": True}
            mock_failure_rate.return_value = {"healthy": True}
            mock_stats.return_value = {"average_execution_time": 2.5}
            
            # Act
            result = await health_checker.get_comprehensive_health_report()
            
            # Assert
            assert result["overall_healthy"] is True
            assert "components" in result
            assert "statistics" in result
            assert "recommendations" in result
            assert "Task system is healthy" in result["recommendations"]
    
    @pytest.mark.asyncio
    async def test_get_comprehensive_health_report_unhealthy(self, health_checker):
        """Test comprehensive health report when system is unhealthy."""
        # Arrange
        with patch.object(health_checker, 'check_worker_health') as mock_worker_health, \
             patch.object(health_checker, 'check_queue_health') as mock_queue_health, \
             patch.object(health_checker, 'check_task_failure_rate') as mock_failure_rate, \
             patch.object(health_checker.monitor, 'get_task_statistics') as mock_stats:
            
            mock_worker_health.return_value = {"healthy": False}
            mock_queue_health.return_value = {
                "healthy": False,
                "queues": {"email": {"healthy": False}, "sms": {"healthy": True}}
            }
            mock_failure_rate.return_value = {"healthy": False}
            mock_stats.return_value = {"average_execution_time": 350}  # > 300 seconds
            
            # Act
            result = await health_checker.get_comprehensive_health_report()
            
            # Assert
            assert result["overall_healthy"] is False
            recommendations = result["recommendations"]
            assert any("Start Celery workers" in rec for rec in recommendations)
            assert any("High queue lengths" in rec for rec in recommendations)
            assert any("High task failure rate" in rec for rec in recommendations)
            assert any("High average task execution time" in rec for rec in recommendations)
    
    def test_generate_recommendations(self, health_checker):
        """Test recommendation generation logic."""
        # Test healthy system
        worker_health = {"healthy": True}
        queue_health = {"healthy": True, "queues": {}}
        failure_rate = {"healthy": True}
        task_stats = {"average_execution_time": 2.5}
        
        recommendations = health_checker._generate_recommendations(
            worker_health, queue_health, failure_rate, task_stats
        )
        
        assert "Task system is healthy" in recommendations
        
        # Test unhealthy system
        worker_health = {"healthy": False}
        queue_health = {
            "healthy": False,
            "queues": {"email": {"healthy": False}, "sms": {"healthy": False}}
        }
        failure_rate = {"healthy": False}
        task_stats = {"average_execution_time": 350}
        
        recommendations = health_checker._generate_recommendations(
            worker_health, queue_health, failure_rate, task_stats
        )
        
        assert len(recommendations) == 4  # All issues should be flagged
        assert any("workers" in rec for rec in recommendations)
        assert any("queue" in rec for rec in recommendations)
        assert any("failure rate" in rec for rec in recommendations)
        assert any("execution time" in rec for rec in recommendations)


class TestGlobalInstances:
    """Test global instances are properly initialized."""
    
    def test_task_monitor_instance(self):
        """Test that global task_monitor instance exists."""
        assert task_monitor is not None
        assert isinstance(task_monitor, TaskMonitor)
    
    def test_health_checker_instance(self):
        """Test that global health_checker instance exists."""
        assert health_checker is not None
        assert isinstance(health_checker, TaskHealthChecker)