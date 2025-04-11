from redis import asyncio as aioredis
from fastapi import FastAPI, Request,HTTPException, WebSocket, WebSocketDisconnect
from typing import List
from core.config import Settings
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.cors import CORSMiddleware

# from apps.user.routes.oauth2.google import router as google_router
from routes import booking_router
# from apps.products.routes.product import router as product_router
# from apps.products.routes.category import router as category_router
# from apps.products.routes.market import router as market_router
# from apps.payments.routes.payments import router as payments_router

from core.utils.response import Response, RequestValidationError 
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
app.include_router(booking_router, prefix='/api/v1')


@app.get("/", response_model=dict)
def initialization_api():
    return {
        "message": "Welcome to the Booking Analytics API",
        "version": "1.0.0",
        "description": "This API allows you to manage bookings for different periods (daily, weekly, monthly, quarterly, yearly).",
        "endpoints": {
            "/daily": "Create or update daily bookings",
            "/weekly": "Create or update weekly bookings",
            "/monthly": "Create or update monthly bookings",
            "/quarterly": "Create or update quarterly bookings",
            "/yearly": "Create or update yearly bookings",
            "/{booking_type}/{booking_id}": "Get a specific booking by ID",
            "/{booking_type}/all": "Get all bookings of a specific type",
        },
        "contact": {
            "email": "support@example.com",
            "website": "https://www.example.com"
        }
    }



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
