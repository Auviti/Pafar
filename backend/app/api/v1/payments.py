"""
Payment API endpoints for secure payment processing.
"""
import json
import logging
import stripe
from typing import Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.payment_service import (
    PaymentService, PaymentServiceError, PaymentNotFoundError, 
    PaymentProcessingError
)
from app.schemas.payment import (
    PaymentIntentCreate, PaymentIntentResponse, PaymentConfirmation,
    PaymentResponse, PaymentMethodTokenCreate, PaymentMethodToken,
    PaymentReceiptData, PaymentRetryRequest, PaymentMethodList
)
from app.utils.receipt_generator import ReceiptGenerator

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/payment-intent", response_model=PaymentIntentResponse)
async def create_payment_intent(
    payment_data: PaymentIntentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a payment intent for a booking.
    
    This endpoint creates a Stripe payment intent that can be used to process
    payment for a specific booking. The payment intent includes the booking
    amount and can optionally use a saved payment method.
    """
    try:
        payment_service = PaymentService(db)
        result = await payment_service.create_payment_intent(
            current_user.id, 
            payment_data
        )
        return result
        
    except PaymentServiceError as e:
        logger.error(f"Payment service error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except PaymentProcessingError as e:
        logger.error(f"Payment processing error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error creating payment intent: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/confirm", response_model=PaymentResponse)
async def confirm_payment(
    confirmation_data: PaymentConfirmation,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Confirm a payment intent.
    
    This endpoint confirms a payment intent and updates the booking status
    based on the payment result. It should be called after the client-side
    payment confirmation is complete.
    """
    try:
        payment_service = PaymentService(db)
        result = await payment_service.confirm_payment(
            current_user.id, 
            confirmation_data
        )
        return result
        
    except PaymentNotFoundError as e:
        logger.error(f"Payment not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except PaymentServiceError as e:
        logger.error(f"Payment service error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except PaymentProcessingError as e:
        logger.error(f"Payment processing error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error confirming payment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/payment-methods", response_model=PaymentMethodToken)
async def create_payment_method(
    card_data: PaymentMethodTokenCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a tokenized payment method.
    
    This endpoint creates a secure token for a payment method that can be
    saved and reused for future payments. The actual card details are
    stored securely by Stripe.
    """
    try:
        payment_service = PaymentService(db)
        result = await payment_service.create_payment_method_token(
            current_user.id, 
            card_data
        )
        return result
        
    except PaymentProcessingError as e:
        logger.error(f"Payment method creation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except PaymentServiceError as e:
        logger.error(f"Payment service error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error creating payment method: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/payment-methods", response_model=PaymentMethodList)
async def get_saved_payment_methods(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user's saved payment methods.
    
    This endpoint returns a list of the user's saved payment methods
    with masked card information for security.
    """
    try:
        payment_service = PaymentService(db)
        result = await payment_service.get_saved_payment_methods(current_user.id)
        return result
        
    except PaymentProcessingError as e:
        logger.error(f"Error retrieving payment methods: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except PaymentServiceError as e:
        logger.error(f"Payment service error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error getting payment methods: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/retry", response_model=PaymentIntentResponse)
async def retry_payment(
    retry_data: PaymentRetryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retry a failed payment.
    
    This endpoint allows retrying a failed payment with the same or
    different payment method. It creates a new payment intent for
    the same booking.
    """
    try:
        payment_service = PaymentService(db)
        result = await payment_service.retry_payment(
            current_user.id, 
            retry_data
        )
        return result
        
    except PaymentNotFoundError as e:
        logger.error(f"Payment not found for retry: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except PaymentServiceError as e:
        logger.error(f"Payment service error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except PaymentProcessingError as e:
        logger.error(f"Payment processing error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error retrying payment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/receipt/{payment_id}", response_model=PaymentReceiptData)
async def get_payment_receipt(
    payment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get payment receipt data.
    
    This endpoint returns detailed receipt information for a completed
    payment, including trip details and transaction information.
    """
    try:
        payment_service = PaymentService(db)
        result = await payment_service.generate_receipt_data(payment_id)
        return result
        
    except PaymentNotFoundError as e:
        logger.error(f"Payment not found for receipt: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except PaymentServiceError as e:
        logger.error(f"Payment service error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error getting receipt: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/receipt/{payment_id}/download", response_class=HTMLResponse)
async def download_payment_receipt(
    payment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Download payment receipt as HTML.
    
    This endpoint generates and returns an HTML receipt for a completed
    payment that can be viewed in browser or printed.
    """
    try:
        payment_service = PaymentService(db)
        receipt_data = await payment_service.generate_receipt_data(payment_id)
        
        # Generate HTML receipt
        html_content = ReceiptGenerator.generate_html_receipt(receipt_data)
        
        return HTMLResponse(
            content=html_content,
            headers={
                "Content-Disposition": f"inline; filename=receipt_{receipt_data.booking_reference}.html"
            }
        )
        
    except PaymentNotFoundError as e:
        logger.error(f"Payment not found for receipt download: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except PaymentServiceError as e:
        logger.error(f"Payment service error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error downloading receipt: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Handle Stripe webhook events.
    
    This endpoint receives webhook events from Stripe to handle
    payment status updates asynchronously. It's used to update
    payment and booking statuses when payments are processed.
    """
    try:
        # Get raw body for signature verification
        body = await request.body()
        sig_header = request.headers.get('stripe-signature')
        
        # Verify webhook signature if webhook secret is configured
        from app.core.config import settings
        if settings.STRIPE_WEBHOOK_SECRET and sig_header:
            try:
                event = stripe.Webhook.construct_event(
                    body, sig_header, settings.STRIPE_WEBHOOK_SECRET
                )
                event_data = event
                logger.info(f"Verified webhook event: {event['type']}")
            except ValueError as e:
                logger.error(f"Invalid webhook payload: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid payload"
                )
            except stripe.error.SignatureVerificationError as e:
                logger.error(f"Invalid webhook signature: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid signature"
                )
        else:
            # Fallback for development - parse JSON directly
            import json
            event_data = json.loads(body)
            logger.warning("Processing webhook without signature verification")
        
        payment_service = PaymentService(db)
        success = await payment_service.handle_webhook_event(event_data)
        
        if success:
            return {"status": "success"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to process webhook event"
            )
            
    except json.JSONDecodeError:
        logger.error("Invalid JSON in webhook payload")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload"
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )