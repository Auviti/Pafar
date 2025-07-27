"""
WebSocket endpoints for real-time tracking and notifications.
"""
import uuid
import json
import asyncio
from typing import Dict, Set, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import decode_access_token
from app.services.tracking_service import TrackingService
from app.core.redis import redis_client
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()

# Connection manager for WebSocket connections
class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        # Store connections by trip_id -> set of websockets
        self.trip_connections: Dict[str, Set[WebSocket]] = {}
        # Store user connections for direct messaging
        self.user_connections: Dict[str, WebSocket] = {}
        # Store driver connections
        self.driver_connections: Dict[str, WebSocket] = {}
    
    async def connect_passenger(self, websocket: WebSocket, trip_id: str, user_id: str):
        """Connect a passenger to trip updates."""
        await websocket.accept()
        
        if trip_id not in self.trip_connections:
            self.trip_connections[trip_id] = set()
        
        self.trip_connections[trip_id].add(websocket)
        self.user_connections[user_id] = websocket
        
        logger.info(f"Passenger {user_id} connected to trip {trip_id}")
    
    async def connect_driver(self, websocket: WebSocket, driver_id: str):
        """Connect a driver for location updates."""
        await websocket.accept()
        self.driver_connections[driver_id] = websocket
        logger.info(f"Driver {driver_id} connected")
    
    def disconnect_passenger(self, websocket: WebSocket, trip_id: str, user_id: str):
        """Disconnect a passenger."""
        if trip_id in self.trip_connections:
            self.trip_connections[trip_id].discard(websocket)
            if not self.trip_connections[trip_id]:
                del self.trip_connections[trip_id]
        
        if user_id in self.user_connections:
            del self.user_connections[user_id]
        
        logger.info(f"Passenger {user_id} disconnected from trip {trip_id}")
    
    def disconnect_driver(self, websocket: WebSocket, driver_id: str):
        """Disconnect a driver."""
        if driver_id in self.driver_connections:
            del self.driver_connections[driver_id]
        logger.info(f"Driver {driver_id} disconnected")
    
    async def broadcast_to_trip(self, trip_id: str, message: dict):
        """Broadcast message to all passengers on a trip."""
        if trip_id not in self.trip_connections:
            return
        
        message_str = json.dumps(message)
        disconnected = set()
        
        for websocket in self.trip_connections[trip_id]:
            try:
                await websocket.send_text(message_str)
            except Exception as e:
                logger.error(f"Error sending message to websocket: {e}")
                disconnected.add(websocket)
        
        # Remove disconnected websockets
        for websocket in disconnected:
            self.trip_connections[trip_id].discard(websocket)
    
    async def send_to_driver(self, driver_id: str, message: dict):
        """Send message to a specific driver."""
        if driver_id not in self.driver_connections:
            return
        
        try:
            await self.driver_connections[driver_id].send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending message to driver {driver_id}: {e}")
            del self.driver_connections[driver_id]
    
    async def send_to_user(self, user_id: str, message: dict):
        """Send message to a specific user."""
        if user_id not in self.user_connections:
            return
        
        try:
            await self.user_connections[user_id].send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending message to user {user_id}: {e}")
            del self.user_connections[user_id]


# Global connection manager instance
manager = ConnectionManager()


async def get_current_user_from_token(token: str) -> Optional[dict]:
    """Extract user info from JWT token."""
    try:
        payload = decode_access_token(token)
        return payload
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        return None


@router.websocket("/ws/trip/{trip_id}")
async def websocket_trip_tracking(
    websocket: WebSocket,
    trip_id: str,
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """WebSocket endpoint for passengers to receive trip updates."""
    # Validate token and get user info
    user_info = await get_current_user_from_token(token)
    if not user_info:
        await websocket.close(code=4001, reason="Invalid token")
        return
    
    user_id = user_info.get("sub")
    if not user_id:
        await websocket.close(code=4001, reason="Invalid user")
        return
    
    # Validate trip_id format
    try:
        uuid.UUID(trip_id)
    except ValueError:
        await websocket.close(code=4000, reason="Invalid trip ID")
        return
    
    tracking_service = TrackingService(db)
    
    try:
        await manager.connect_passenger(websocket, trip_id, user_id)
        
        # Send initial trip location if available
        location = await tracking_service.get_trip_location(uuid.UUID(trip_id))
        if location:
            await websocket.send_text(json.dumps({
                "type": "location_update",
                "data": location
            }))
        
        # Listen for messages (keep connection alive)
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle ping/pong for connection health
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                break
    
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect_passenger(websocket, trip_id, user_id)


@router.websocket("/ws/driver/{driver_id}")
async def websocket_driver_updates(
    websocket: WebSocket,
    driver_id: str,
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """WebSocket endpoint for drivers to send location updates."""
    # Validate token and get user info
    user_info = await get_current_user_from_token(token)
    if not user_info:
        await websocket.close(code=4001, reason="Invalid token")
        return
    
    # Verify driver authorization
    token_user_id = user_info.get("sub")
    if token_user_id != driver_id:
        await websocket.close(code=4003, reason="Unauthorized driver")
        return
    
    tracking_service = TrackingService(db)
    
    try:
        await manager.connect_driver(websocket, driver_id)
        
        # Send active trips for driver
        active_trips = await tracking_service.get_active_trips_for_driver(uuid.UUID(driver_id))
        await websocket.send_text(json.dumps({
            "type": "active_trips",
            "data": [
                {
                    "trip_id": str(trip.id),
                    "status": trip.status.value,
                    "departure_time": trip.departure_time.isoformat()
                }
                for trip in active_trips
            ]
        }))
        
        # Listen for location updates from driver
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "location_update":
                    await handle_driver_location_update(message, tracking_service, driver_id)
                elif message.get("type") == "status_update":
                    await handle_driver_status_update(message, tracking_service, driver_id)
                elif message.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))
            except Exception as e:
                logger.error(f"Driver WebSocket error: {e}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": str(e)
                }))
    
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect_driver(websocket, driver_id)


async def handle_driver_location_update(message: dict, tracking_service: TrackingService, driver_id: str):
    """Handle location update from driver."""
    data = message.get("data", {})
    trip_id = data.get("trip_id")
    latitude = data.get("latitude")
    longitude = data.get("longitude")
    speed = data.get("speed")
    heading = data.get("heading")
    
    if not all([trip_id, latitude is not None, longitude is not None]):
        raise ValueError("Missing required location data")
    
    # Update location in database
    location = await tracking_service.update_trip_location(
        trip_id=uuid.UUID(trip_id),
        latitude=float(latitude),
        longitude=float(longitude),
        speed=float(speed) if speed is not None else None,
        heading=float(heading) if heading is not None else None
    )
    
    # Broadcast to all passengers on this trip
    await manager.broadcast_to_trip(trip_id, {
        "type": "location_update",
        "data": {
            "trip_id": str(location.trip_id),
            "latitude": float(location.latitude),
            "longitude": float(location.longitude),
            "speed": float(location.speed) if location.speed else None,
            "heading": float(location.heading) if location.heading else None,
            "recorded_at": location.recorded_at.isoformat()
        }
    })


async def handle_driver_status_update(message: dict, tracking_service: TrackingService, driver_id: str):
    """Handle trip status update from driver."""
    data = message.get("data", {})
    trip_id = data.get("trip_id")
    status = data.get("status")
    
    if not all([trip_id, status]):
        raise ValueError("Missing required status data")
    
    # Update trip status
    from app.models.fleet import TripStatus
    trip = await tracking_service.update_trip_status(
        trip_id=uuid.UUID(trip_id),
        status=TripStatus(status),
        driver_id=uuid.UUID(driver_id)
    )
    
    # Broadcast status update to passengers
    await manager.broadcast_to_trip(trip_id, {
        "type": "status_update",
        "data": {
            "trip_id": str(trip.id),
            "status": trip.status.value,
            "updated_at": datetime.utcnow().isoformat()
        }
    })


# Background task to handle Redis pub/sub for cross-instance communication
async def redis_message_handler():
    """Handle Redis pub/sub messages for cross-instance WebSocket communication."""
    pubsub = redis_client.pubsub()
    await pubsub.subscribe("trip_updates", "driver_updates", "passenger_notifications")
    
    async for message in pubsub.listen():
        if message["type"] == "message":
            try:
                data = json.loads(message["data"])
                channel = message["channel"].decode()
                
                if channel == "trip_updates":
                    trip_id = data.get("trip_id")
                    if trip_id:
                        await manager.broadcast_to_trip(trip_id, data)
                
                elif channel == "driver_updates":
                    driver_id = data.get("driver_id")
                    if driver_id:
                        await manager.send_to_driver(driver_id, data)
                
                elif channel == "passenger_notifications":
                    user_id = data.get("user_id")
                    if user_id:
                        await manager.send_to_user(user_id, data)
                        
            except Exception as e:
                logger.error(f"Error handling Redis message: {e}")


# Start Redis message handler on module import
import asyncio
from datetime import datetime

def start_redis_handler():
    """Start Redis message handler in background."""
    try:
        loop = asyncio.get_event_loop()
        loop.create_task(redis_message_handler())
    except RuntimeError:
        # No event loop running, will be started later
        pass

# Uncomment to enable Redis handler
# start_redis_handler()