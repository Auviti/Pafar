from redis import asyncio as aioredis
from fastapi import FastAPI, Request,HTTPException, WebSocket, WebSocketDisconnect
from typing import List
from core.config import Settings
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.cors import CORSMiddleware

from apps.user.routes.oauth2.google import router as google_router
from apps.user.routes.user import router as user_router
from apps.user.routes.vehicle import router as vehicle_router

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
app.include_router(user_router, prefix='/api/v1')
app.include_router(vehicle_router, prefix='/api/v1')
app.include_router(google_router, prefix='/api/v1')


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

    
# user, rides,bus
# # List of active connections (can be used for broadcasting messages)
# active_connections: List[WebSocket] = []



# @app.websocket("/wss")
# async def websocket_endpoint(websocket: WebSocket):
#     # Accept the WebSocket connection
#     await websocket.accept()  # "on_open" - connection established
#     print(f"Client connected--{websocket}")
    
#     # Add the new WebSocket connection to the list
#     active_connections.append(websocket)
    
#     try:
#         while True:
#             # Receive a message from the client
#             data = await websocket.receive_text() # Receive message
#             print(f"Message sent: {data}")
#             # You can implement your own logic to determine the event type.
#             # For instance, check if the message is a command like "update" or "custom_event"
#             if data == "update":
#                 await on_update(websocket, data)
#             elif data == "leave":
#                 await on_leave(websocket)
#                 break
#             elif data.startswith("custom:"):
#                 event = data.split(":", 1)[1]  # Get the custom event message
#                 await on_custom_event(websocket, event)
#             else:
#                 await on_message(websocket, data)

#             # Broadcast the message to all active connections
#             for connection in active_connections:
#                 if connection != websocket:
#                     await connection.send_text(f"Broadcast message: {data}")
    
#     except WebSocketDisconnect:
#         # Remove the connection when the client disconnects
#         active_connections.remove(websocket)
#         print("Client disconnected")