"""
Task monitoring and error handling utilities for Celery tasks.
"""
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from celery import current_app
from celery.events.state import State
from ..core.celery_app import celery_app
from ..core.redis import redis_client


class TaskMonitor:
    """Monitor and track Celery task execution."""
    
    def __init__(self):
        self.redis = redis_client
    
    async def log_task_start(self, task_id: str, task_name: str, args: tuple, kwargs: dict) -> None:
        """Log task start event."""
        task_info = {
            "task_id": task_id,
            "task_name": task_name,
            "args": args,
            "kwargs": kwargs,
            "status": "started",
            "started_at": datetime.utcnow().isoformat(),
            "worker_id": None  # Will be set by worker
        }
        
        await self.redis.set_json(
            f"task_log:{task_id}",
            task_info,
            expire=86400  # Keep for 24 hours
        )
    
    async def log_task_success(self, task_id: str, result: Any, execution_time: float) -> None:
        """Log task success event."""
        task_info = await self.redis.get_json(f"task_log:{task_id}")
        if task_info:
            task_info.update({
                "status": "success",
                "result": result,
                "completed_at": datetime.utcnow().isoformat(),
                "execution_time_seconds": execution_time
            })
            
            await self.redis.set_json(
                f"task_log:{task_id}",
                task_info,
                expire=86400
            )
    
    async def log_task_failure(self, task_id: str, error: str, traceback: str) -> None:
        """Log task failure event."""
        task_info = await self.redis.get_json(f"task_log:{task_id}")
        if task_info:
            task_info.update({
                "status": "failed",
                "error": error,
                "traceback": traceback,
                "failed_at": datetime.utcnow().isoformat()
            })
            
            await self.redis.set_json(
                f"task_log:{task_id}",
                task_info,
                expire=86400
            )
            
            # Also log to failure queue for alerting
            await self.redis.set_json(
                f"task_failure:{task_id}",
                task_info,
                expire=604800  # Keep failures for 7 days
            )
    
    async def log_task_retry(self, task_id: str, retry_count: int, next_retry: datetime) -> None:
        """Log task retry event."""
        task_info = await self.redis.get_json(f"task_log:{task_id}")
        if task_info:
            task_info.update({
                "status": "retrying",
                "retry_count": retry_count,
                "next_retry_at": next_retry.isoformat(),
                "last_retry_at": datetime.utcnow().isoformat()
            })
            
            await self.redis.set_json(
                f"task_log:{task_id}",
                task_info,
                expire=86400
            )
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get current task status."""
        return await self.redis.get_json(f"task_log:{task_id}")
    
    async def get_failed_tasks(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get failed tasks from the last N hours."""
        pattern = "task_failure:*"
        keys = await self.redis.keys(pattern)
        
        failed_tasks = []
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        for key in keys:
            task_info = await self.redis.get_json(key)
            if task_info and task_info.get("failed_at"):
                failed_at = datetime.fromisoformat(task_info["failed_at"])
                if failed_at >= cutoff_time:
                    failed_tasks.append(task_info)
        
        return sorted(failed_tasks, key=lambda x: x["failed_at"], reverse=True)
    
    async def get_task_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get task execution statistics."""
        pattern = "task_log:*"
        keys = await self.redis.keys(pattern)
        
        stats = {
            "total_tasks": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "retrying_tasks": 0,
            "running_tasks": 0,
            "task_types": {},
            "average_execution_time": 0,
            "period_hours": hours
        }
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        execution_times = []
        
        for key in keys:
            task_info = await self.redis.get_json(key)
            if not task_info:
                continue
            
            started_at = task_info.get("started_at")
            if not started_at:
                continue
            
            started_dt = datetime.fromisoformat(started_at)
            if started_dt < cutoff_time:
                continue
            
            stats["total_tasks"] += 1
            
            status = task_info.get("status", "unknown")
            task_name = task_info.get("task_name", "unknown")
            
            # Count by status
            if status == "success":
                stats["successful_tasks"] += 1
                execution_time = task_info.get("execution_time_seconds")
                if execution_time:
                    execution_times.append(execution_time)
            elif status == "failed":
                stats["failed_tasks"] += 1
            elif status == "retrying":
                stats["retrying_tasks"] += 1
            elif status == "started":
                stats["running_tasks"] += 1
            
            # Count by task type
            if task_name not in stats["task_types"]:
                stats["task_types"][task_name] = {
                    "total": 0,
                    "successful": 0,
                    "failed": 0
                }
            
            stats["task_types"][task_name]["total"] += 1
            if status == "success":
                stats["task_types"][task_name]["successful"] += 1
            elif status == "failed":
                stats["task_types"][task_name]["failed"] += 1
        
        # Calculate average execution time
        if execution_times:
            stats["average_execution_time"] = sum(execution_times) / len(execution_times)
        
        return stats


class TaskHealthChecker:
    """Health checker for Celery tasks and workers."""
    
    def __init__(self):
        self.redis = redis_client
        self.monitor = TaskMonitor()
    
    async def check_worker_health(self) -> Dict[str, Any]:
        """Check the health of Celery workers."""
        try:
            # Get active workers
            inspect = celery_app.control.inspect()
            active_workers = inspect.active()
            registered_tasks = inspect.registered()
            
            if not active_workers:
                return {
                    "healthy": False,
                    "message": "No active workers found",
                    "workers": [],
                    "total_workers": 0
                }
            
            worker_info = []
            for worker_name, tasks in active_workers.items():
                worker_info.append({
                    "name": worker_name,
                    "active_tasks": len(tasks),
                    "registered_tasks": len(registered_tasks.get(worker_name, [])) if registered_tasks else 0
                })
            
            return {
                "healthy": True,
                "message": f"{len(active_workers)} workers active",
                "workers": worker_info,
                "total_workers": len(active_workers)
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "message": f"Error checking worker health: {str(e)}",
                "workers": [],
                "total_workers": 0
            }
    
    async def check_queue_health(self) -> Dict[str, Any]:
        """Check the health of task queues."""
        try:
            # Get queue lengths from Redis
            queues = ["email", "sms", "notifications", "cleanup", "celery"]  # Default queue
            queue_info = {}
            
            for queue in queues:
                # Check queue length in Redis
                queue_key = f"celery:queue:{queue}"
                queue_length = await self.redis.redis.llen(queue_key) if self.redis.redis else 0
                
                queue_info[queue] = {
                    "length": queue_length,
                    "healthy": queue_length < 1000  # Threshold for queue health
                }
            
            total_queued = sum(info["length"] for info in queue_info.values())
            all_healthy = all(info["healthy"] for info in queue_info.values())
            
            return {
                "healthy": all_healthy,
                "message": f"Total queued tasks: {total_queued}",
                "queues": queue_info,
                "total_queued_tasks": total_queued
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "message": f"Error checking queue health: {str(e)}",
                "queues": {},
                "total_queued_tasks": 0
            }
    
    async def check_task_failure_rate(self, hours: int = 1) -> Dict[str, Any]:
        """Check task failure rate over the last N hours."""
        try:
            stats = await self.monitor.get_task_statistics(hours)
            
            total_tasks = stats["total_tasks"]
            failed_tasks = stats["failed_tasks"]
            
            if total_tasks == 0:
                failure_rate = 0
            else:
                failure_rate = (failed_tasks / total_tasks) * 100
            
            healthy = failure_rate < 10  # Less than 10% failure rate is healthy
            
            return {
                "healthy": healthy,
                "failure_rate_percent": round(failure_rate, 2),
                "total_tasks": total_tasks,
                "failed_tasks": failed_tasks,
                "period_hours": hours,
                "message": f"Failure rate: {failure_rate:.2f}% over {hours} hours"
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "message": f"Error checking failure rate: {str(e)}",
                "failure_rate_percent": 0,
                "total_tasks": 0,
                "failed_tasks": 0
            }
    
    async def get_comprehensive_health_report(self) -> Dict[str, Any]:
        """Get a comprehensive health report for the task system."""
        worker_health = await self.check_worker_health()
        queue_health = await self.check_queue_health()
        failure_rate = await self.check_task_failure_rate()
        task_stats = await self.monitor.get_task_statistics()
        
        overall_healthy = (
            worker_health["healthy"] and 
            queue_health["healthy"] and 
            failure_rate["healthy"]
        )
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_healthy": overall_healthy,
            "components": {
                "workers": worker_health,
                "queues": queue_health,
                "failure_rate": failure_rate
            },
            "statistics": task_stats,
            "recommendations": self._generate_recommendations(
                worker_health, queue_health, failure_rate, task_stats
            )
        }
    
    def _generate_recommendations(
        self, 
        worker_health: Dict[str, Any], 
        queue_health: Dict[str, Any], 
        failure_rate: Dict[str, Any], 
        task_stats: Dict[str, Any]
    ) -> List[str]:
        """Generate health recommendations based on current status."""
        recommendations = []
        
        if not worker_health["healthy"]:
            recommendations.append("Start Celery workers to process tasks")
        
        if not queue_health["healthy"]:
            high_queues = [
                queue for queue, info in queue_health["queues"].items() 
                if not info["healthy"]
            ]
            recommendations.append(f"High queue lengths detected in: {', '.join(high_queues)}")
        
        if not failure_rate["healthy"]:
            recommendations.append("High task failure rate - investigate failed tasks")
        
        if task_stats["average_execution_time"] > 300:  # 5 minutes
            recommendations.append("High average task execution time - optimize slow tasks")
        
        if not recommendations:
            recommendations.append("Task system is healthy")
        
        return recommendations


# Global instances
task_monitor = TaskMonitor()
health_checker = TaskHealthChecker()