from redis import asyncio as aioredis
from fastapi import FastAPI, Request,HTTPException, WebSocket, WebSocketDisconnect
from typing import List
from core.config import Settings
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.cors import CORSMiddleware

# from apps.user.routes.oauth2.google import router as google_router
# from apps.user.routes.user import router as user_router
# from apps.products.routes.product import router as product_router
# from apps.products.routes.category import router as category_router
# from apps.products.routes.market import router as market_router
# from apps.payments.routes.payments import router as payments_router

from core.utils.reponse import Response, RequestValidationError 
import redis.asyncio as aioredis
app = FastAPI()
settings = Settings()
app = FastAPI()

# Add CORS middleware if configured
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            str(origin).strip("/") for origin in settings.BACKEND_CORS_ORIGINS
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Add session middleware
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

        
# Include the routers
# app.include_router(user_router, prefix='/api/v1')
# app.include_router(product_router, prefix='/api/v1')
# app.include_router(category_router, prefix='/api/v1')
# app.include_router(market_router, prefix='/api/v1')
# app.include_router(google_router, prefix='/api/v1')
# app.include_router(payments_router, prefix='/api/v1')
@app.get("/")
def read_root():
    return {"Hello": "World"}


# Handle validation errors globally
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        e = {}
        e['type'] = error['type']
        e['loc'] = error['loc']
        e['msg'] = error['msg']
        if 'ctx' in error.keys():
            e['ctx'] = error['ctx']['error']

        errors.append(e)
    errors = errors[0] if len(errors) == 1 else errors

    return Response(message=errors, success=False, code=422)

# Connect to Redis when FastAPI starts
@app.on_event("startup")
async def startup():
    try:
        app.state.redis = await aioredis.from_url(f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}", encoding="utf-8", decode_responses=True)
        print("Connected to Redis successfully.")
    except Exception as e:
        print(f"Error connecting to Redis: {e}")
        raise HTTPException(status_code=500, detail="Redis connection failed")

# Close Redis connection when FastAPI shuts down
@app.on_event("shutdown")
async def shutdown():
    if hasattr(app.state, "redis"):
        await app.state.redis.close()
        print("Redis connection closed successfully.")

# Example endpoint to set a key-value pair in Redis
@app.post("/set_key/")
async def set_redis_key(key: str, value: str):
    try:
        await app.state.redis.set(key, value)
        return Response(message="Key set successfully", data={"key": key, "value": value},code=200)
    except aioredis.RedisError as e:
        return Response(message=str(e), success=False, code=500)
    
# Example endpoint to get a value from Redis by key
@app.get("/get_key/")
async def get_redis_key(key: str):
    try:
        value = await app.state.redis.get(key, encoding="utf-8")
        if value is None:
            return Response(message="Key not found",success=False,code=404)
        return Response(message="Key set successfully", data={"key": key, "value": value},code=201)
    except aioredis.RedisError as e:
        raise HTTPException(status_code=500, detail=f"Redis error: {str(e)}")
    
# List of active connections (can be used for broadcasting messages)
active_connections: List[WebSocket] = []


# Custom event handlers
async def on_join(websocket: WebSocket):
    await websocket.send_text("Welcome! You have successfully joined the chat.")

async def on_message(websocket: WebSocket, data: str):
    # Handle received message
    print(f"Message received: {data}")
    await websocket.send_text(f"Message received: {data}")

async def on_update(websocket: WebSocket, data: str):
    # Handle an update event (e.g., a status update or data refresh)
    print(f"Update received: {data}")
    await websocket.send_text(f"Update received: {data}")

async def on_leave(websocket: WebSocket):
    # Handle client leaving (e.g., notifying others, cleanup, etc.)
    await websocket.send_text("You have left the chat.")
    print("Client left the chat")

async def on_custom_event(websocket: WebSocket, event: str):
    # Handle a custom event
    await websocket.send_text(f"Custom event triggered: {event}")
    print(f"Custom event triggered: {event}")

@app.websocket("/wss")
async def websocket_endpoint(websocket: WebSocket):
    # Accept the WebSocket connection
    await websocket.accept()  # "on_open" - connection established
    print(f"Client connected--{websocket}")
    
    # Add the new WebSocket connection to the list
    active_connections.append(websocket)
    
    try:
        while True:
            # Receive a message from the client
            data = await websocket.receive_text() # Receive message
            print(f"Message sent: {data}")
            # You can implement your own logic to determine the event type.
            # For instance, check if the message is a command like "update" or "custom_event"
            if data == "update":
                await on_update(websocket, data)
            elif data == "leave":
                await on_leave(websocket)
                break
            elif data.startswith("custom:"):
                event = data.split(":", 1)[1]  # Get the custom event message
                await on_custom_event(websocket, event)
            else:
                await on_message(websocket, data)

            # Broadcast the message to all active connections
            for connection in active_connections:
                if connection != websocket:
                    await connection.send_text(f"Broadcast message: {data}")
    
    except WebSocketDisconnect:
        # Remove the connection when the client disconnects
        active_connections.remove(websocket)
        print("Client disconnected")