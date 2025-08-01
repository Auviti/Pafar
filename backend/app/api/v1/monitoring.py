"""
Monitoring and error reporting endpoints.
"""
from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from ...core.monitoring import error_monitor
from ...core.exceptions import get_trace_id
from ...core.logging import get_logger

logger = get_logger("monitoring")
router = APIRouter()


class ClientErrorReport(BaseModel):
    """Client-side error report model."""
    type: str = Field(..., description="Error type (javascript, react_error_boundary, etc.)")
    message: str = Field(..., description="Error message")
    stack: Optional[str] = Field(None, description="Stack trace")
    timestamp: str = Field(..., description="Error timestamp")
    url: str = Field(..., description="URL where error occurred")
    userAgent: str = Field(..., description="User agent string")
    errorId: Optional[str] = Field(None, description="Client-generated error ID")
    sessionId: Optional[str] = Field(None, description="Session ID")
    userId: Optional[str] = Field(None, description="User ID")
    buildVersion: Optional[str] = Field(None, description="Application build version")
    environment: Optional[str] = Field(None, description="Environment (development, production)")
    viewport: Optional[Dict[str, int]] = Field(None, description="Viewport dimensions")
    memory: Optional[Dict[str, int]] = Field(None, description="Memory usage info")
    connection: Optional[Dict[str, Any]] = Field(None, description="Network connection info")
    componentStack: Optional[str] = Field(None, description="React component stack")
    retryCount: Optional[int] = Field(0, description="Number of retries")
    severity: Optional[str] = Field("error", description="Error severity")


class HealthCheckResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: str
    services: Dict[str, Any]
    uptime: float


@router.post("/client-errors", status_code=status.HTTP_201_CREATED)
async def report_client_error(
    error_report: ClientErrorReport,
    request: Request
):
    """Receive and process client-side error reports."""
    trace_id = get_trace_id(request)
    
    try:
        # Record the client error in our monitoring system
        await error_monitor.record_error(
            error_type=f"CLIENT_{error_report.type.upper()}",
            error_message=error_report.message,
            trace_id=trace_id,
            service="frontend",
            endpoint=error_report.url,
            user_id=error_report.userId,
            severity=error_report.severity or "error",
            metadata={
                "client_error_id": error_report.errorId,
                "session_id": error_report.sessionId,
                "user_agent": error_report.userAgent,
                "build_version": error_report.buildVersion,
                "environment": error_report.environment,
                "viewport": error_report.viewport,
                "memory": error_report.memory,
                "connection": error_report.connection,
                "component_stack": error_report.componentStack,
                "retry_count": error_report.retryCount,
                "stack_trace": error_report.stack,
                "client_timestamp": error_report.timestamp
            }
        )
        
        logger.info(
            f"Client error reported: {error_report.type} - {error_report.message}",
            extra={
                "trace_id": trace_id,
                "client_error_id": error_report.errorId,
                "user_id": error_report.userId,
                "error_type": error_report.type,
                "url": error_report.url
            }
        )
        
        return {
            "status": "received",
            "trace_id": trace_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(
            f"Failed to process client error report: {str(e)}",
            extra={
                "trace_id": trace_id,
                "client_error_id": error_report.errorId,
                "error": str(e)
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process error report"
        )


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Get system health status."""
    try:
        from ...core.fallbacks import get_service_health_status
        import time
        
        # Get service health status
        health_status = await get_service_health_status()
        
        # Calculate uptime (simplified - in production you'd track actual start time)
        uptime = time.time()
        
        return HealthCheckResponse(
            status=health_status["status"],
            timestamp=health_status["timestamp"],
            services=health_status["services"],
            uptime=uptime
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Health check failed"
        )


@router.get("/errors/summary")
async def get_error_summary(
    hours: int = 24,
    # current_user: User = Depends(get_current_admin_user)  # Uncomment when auth is ready
):
    """Get error summary for the specified time period."""
    try:
        summary = error_monitor.get_error_summary(hours=hours)
        return summary
        
    except Exception as e:
        logger.error(f"Failed to get error summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve error summary"
        )


@router.get("/errors/recent")
async def get_recent_errors(
    limit: int = 50,
    # current_user: User = Depends(get_current_admin_user)  # Uncomment when auth is ready
):
    """Get recent error events."""
    try:
        if limit > 1000:
            limit = 1000  # Cap the limit
            
        recent_errors = error_monitor.get_recent_errors(limit=limit)
        return {
            "errors": recent_errors,
            "count": len(recent_errors),
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Failed to get recent errors: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve recent errors"
        )


@router.get("/metrics")
async def get_system_metrics(
    # current_user: User = Depends(get_current_admin_user)  # Uncomment when auth is ready
):
    """Get system performance metrics."""
    try:
        import psutil
        import os
        
        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Get process metrics
        process = psutil.Process(os.getpid())
        process_memory = process.memory_info()
        
        metrics = {
            "system": {
                "cpu_percent": cpu_percent,
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": (disk.used / disk.total) * 100
                }
            },
            "process": {
                "memory": {
                    "rss": process_memory.rss,
                    "vms": process_memory.vms
                },
                "cpu_percent": process.cpu_percent(),
                "num_threads": process.num_threads()
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return metrics
        
    except ImportError:
        # psutil not available
        return {
            "error": "System metrics not available - psutil not installed",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get system metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system metrics"
        )