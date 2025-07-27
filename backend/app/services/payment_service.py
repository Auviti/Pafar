"""
Payment service for handling secure payment processing with Stripe integration.
"""
import logging
import stripe
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.payment import Payment, PaymentStatus, PaymentMethod, PaymentGateway
from app.models.booking import Booking
from app.models.user import User
from app.schemas.payment import (
    PaymentCreate, PaymentUpdate, PaymentResponse, PaymentIntentCreate,
    PaymentIntentResponse, PaymentConfirmation, PaymentMethodTokenCreate,
    PaymentMethodToken, PaymentReceiptData, PaymentRetryRequest,
    SavedPaymentMethod, PaymentMethodList
)

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

logger = logging.getLogger(__name__)


class PaymentServiceError(Exception):
    """Base exception for payment service errors."""
    pass


class PaymentNotFoundError(PaymentServiceError):
    """Raised when payment is not found."""
    pass


class PaymentProcessingError(PaymentServiceError):
    """Raised when payment processing fails."""
    pass


class PaymentService:
    """Service for handling payment operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_payment_intent(
        self, 
        user_id: UUID, 
        payment_data: PaymentIntentCreate
    ) -> PaymentIntentResponse:
        """Create a Stripe payment intent for a booking."""
        try:
            # Get booking details
            booking = await self._get_booking_with_details(payment_data.booking_id)
            if not booking:
                raise PaymentServiceError("Booking not found")
            
            if booking.user_id != user_id:
                raise PaymentServiceError("Unauthorized access to booking")
            
            if booking.payment_status == "completed":
                raise PaymentServiceError("Booking already paid")
            
            # Calculate amount in cents for Stripe
            amount_cents = int(booking.total_amount * 100)
            
            # Create Stripe payment intent
            intent_params = {
                "amount": amount_cents,
                "currency": "usd",
                "metadata": {
                    "booking_id": str(booking.id),
                    "user_id": str(user_id),
                    "booking_reference": booking.booking_reference
                },
                "automatic_payment_methods": {"enabled": True}
            }
            
            # Add payment method if provided
            if payment_data.payment_method_token:
                intent_params["payment_method"] = payment_data.payment_method_token
                intent_params["confirmation_method"] = "manual"
                intent_params["confirm"] = True
            
            # Add return URL if provided
            if payment_data.return_url:
                intent_params["return_url"] = payment_data.return_url
            
            # Setup future usage if saving payment method
            if payment_data.save_payment_method:
                intent_params["setup_future_usage"] = "off_session"
            
            payment_intent = stripe.PaymentIntent.create(**intent_params)
            
            # Create payment record
            payment = Payment(
                booking_id=booking.id,
                amount=booking.total_amount,
                currency="USD",
                payment_method=PaymentMethod.CARD,
                payment_gateway=PaymentGateway.STRIPE,
                gateway_transaction_id=payment_intent.id,
                status=PaymentStatus.PENDING
            )
            
            self.db.add(payment)
            await self.db.commit()
            await self.db.refresh(payment)
            
            logger.info(f"Created payment intent {payment_intent.id} for booking {booking.id}")
            
            return PaymentIntentResponse(
                payment_intent_id=payment_intent.id,
                client_secret=payment_intent.client_secret,
                amount=booking.total_amount,
                currency="USD",
                status=payment_intent.status,
                requires_action=payment_intent.status == "requires_action",
                next_action=payment_intent.next_action
            )
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating payment intent: {str(e)}")
            raise PaymentProcessingError(f"Payment processing error: {str(e)}")
        except Exception as e:
            logger.error(f"Error creating payment intent: {str(e)}")
            raise PaymentServiceError(f"Failed to create payment intent: {str(e)}")
    
    async def confirm_payment(
        self, 
        user_id: UUID, 
        confirmation_data: PaymentConfirmation
    ) -> PaymentResponse:
        """Confirm a payment intent and update booking status."""
        try:
            # Retrieve payment intent from Stripe
            payment_intent = stripe.PaymentIntent.retrieve(
                confirmation_data.payment_intent_id
            )
            
            # Get payment record
            payment = await self._get_payment_by_transaction_id(
                confirmation_data.payment_intent_id
            )
            if not payment:
                raise PaymentNotFoundError("Payment not found")
            
            # Verify user authorization
            booking = await self._get_booking_with_details(payment.booking_id)
            if booking.user_id != user_id:
                raise PaymentServiceError("Unauthorized access to payment")
            
            # Update payment status based on Stripe status
            if payment_intent.status == "succeeded":
                payment.status = PaymentStatus.COMPLETED
                payment.processed_at = datetime.utcnow()
                
                # Update booking payment status
                await self._update_booking_payment_status(
                    payment.booking_id, 
                    "completed"
                )
                
                logger.info(f"Payment {payment.id} completed successfully")
                
            elif payment_intent.status == "requires_action":
                payment.status = PaymentStatus.PROCESSING
                logger.info(f"Payment {payment.id} requires additional action")
                
            elif payment_intent.status in ["canceled", "payment_failed"]:
                payment.status = PaymentStatus.FAILED
                logger.warning(f"Payment {payment.id} failed or was canceled")
                
            await self.db.commit()
            await self.db.refresh(payment)
            
            return PaymentResponse.model_validate(payment)
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error confirming payment: {str(e)}")
            raise PaymentProcessingError(f"Payment confirmation error: {str(e)}")
        except Exception as e:
            logger.error(f"Error confirming payment: {str(e)}")
            raise PaymentServiceError(f"Failed to confirm payment: {str(e)}")
    
    async def create_payment_method_token(
        self, 
        user_id: UUID, 
        card_data: PaymentMethodTokenCreate
    ) -> PaymentMethodToken:
        """Create a tokenized payment method for future use."""
        try:
            # Create Stripe payment method
            payment_method = stripe.PaymentMethod.create(
                type="card",
                card={
                    "number": card_data.card_number,
                    "exp_month": card_data.exp_month,
                    "exp_year": card_data.exp_year,
                    "cvc": card_data.cvc
                },
                billing_details={
                    "name": card_data.cardholder_name
                }
            )
            
            # Get user's Stripe customer ID or create one
            customer_id = await self._get_or_create_stripe_customer(user_id)
            
            # Attach payment method to customer
            payment_method.attach(customer=customer_id)
            
            logger.info(f"Created payment method token {payment_method.id} for user {user_id}")
            
            return PaymentMethodToken(
                token_id=payment_method.id,
                last_four=payment_method.card.last4,
                brand=payment_method.card.brand,
                exp_month=payment_method.card.exp_month,
                exp_year=payment_method.card.exp_year,
                created_at=datetime.utcnow()
            )
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating payment method: {str(e)}")
            raise PaymentProcessingError(f"Payment method creation error: {str(e)}")
        except Exception as e:
            logger.error(f"Error creating payment method: {str(e)}")
            raise PaymentServiceError(f"Failed to create payment method: {str(e)}")
    
    async def get_saved_payment_methods(self, user_id: UUID) -> PaymentMethodList:
        """Get user's saved payment methods."""
        try:
            customer_id = await self._get_stripe_customer_id(user_id)
            if not customer_id:
                return PaymentMethodList(payment_methods=[], total=0)
            
            # Retrieve payment methods from Stripe
            payment_methods = stripe.PaymentMethod.list(
                customer=customer_id,
                type="card"
            )
            
            saved_methods = []
            for pm in payment_methods.data:
                saved_methods.append(SavedPaymentMethod(
                    id=pm.id,
                    last_four=pm.card.last4,
                    brand=pm.card.brand,
                    exp_month=pm.card.exp_month,
                    exp_year=pm.card.exp_year,
                    created_at=datetime.fromtimestamp(pm.created)
                ))
            
            return PaymentMethodList(
                payment_methods=saved_methods,
                total=len(saved_methods)
            )
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error retrieving payment methods: {str(e)}")
            raise PaymentProcessingError(f"Error retrieving payment methods: {str(e)}")
        except Exception as e:
            logger.error(f"Error getting saved payment methods: {str(e)}")
            raise PaymentServiceError(f"Failed to get payment methods: {str(e)}")
    
    async def retry_payment(
        self, 
        user_id: UUID, 
        retry_data: PaymentRetryRequest
    ) -> PaymentIntentResponse:
        """Retry a failed payment."""
        try:
            # Get original payment
            payment = await self._get_payment_by_id(retry_data.payment_id)
            if not payment:
                raise PaymentNotFoundError("Payment not found")
            
            # Verify user authorization
            booking = await self._get_booking_with_details(payment.booking_id)
            if booking.user_id != user_id:
                raise PaymentServiceError("Unauthorized access to payment")
            
            if payment.status == PaymentStatus.COMPLETED:
                raise PaymentServiceError("Payment already completed")
            
            # Create new payment intent
            payment_intent_data = PaymentIntentCreate(
                booking_id=payment.booking_id,
                payment_method_token=retry_data.payment_method_token
            )
            
            return await self.create_payment_intent(user_id, payment_intent_data)
            
        except Exception as e:
            logger.error(f"Error retrying payment: {str(e)}")
            raise PaymentServiceError(f"Failed to retry payment: {str(e)}")
    
    async def handle_webhook_event(self, event_data: Dict[str, Any]) -> bool:
        """Handle Stripe webhook events."""
        try:
            event_type = event_data.get("type")
            payment_intent = event_data.get("data", {}).get("object", {})
            payment_intent_id = payment_intent.get("id")
            
            if not payment_intent_id:
                logger.warning("Webhook event missing payment intent ID")
                return False
            
            # Get payment record
            payment = await self._get_payment_by_transaction_id(payment_intent_id)
            if not payment:
                logger.warning(f"Payment not found for webhook event: {payment_intent_id}")
                return False
            
            # Handle different event types
            if event_type == "payment_intent.succeeded":
                payment.status = PaymentStatus.COMPLETED
                payment.processed_at = datetime.utcnow()
                
                await self._update_booking_payment_status(
                    payment.booking_id, 
                    "completed"
                )
                
                logger.info(f"Webhook: Payment {payment.id} completed")
                
            elif event_type == "payment_intent.payment_failed":
                payment.status = PaymentStatus.FAILED
                logger.info(f"Webhook: Payment {payment.id} failed")
                
            elif event_type == "payment_intent.canceled":
                payment.status = PaymentStatus.CANCELLED
                logger.info(f"Webhook: Payment {payment.id} canceled")
            
            await self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error handling webhook event: {str(e)}")
            return False
    
    async def generate_receipt_data(self, payment_id: UUID) -> PaymentReceiptData:
        """Generate receipt data for a completed payment."""
        try:
            # Get payment with booking details
            query = select(Payment).options(
                selectinload(Payment.booking).selectinload(Booking.user),
                selectinload(Payment.booking).selectinload(Booking.trip)
            ).where(Payment.id == payment_id)
            
            result = await self.db.execute(query)
            payment = result.scalar_one_or_none()
            
            if not payment:
                raise PaymentNotFoundError("Payment not found")
            
            if payment.status != PaymentStatus.COMPLETED:
                raise PaymentServiceError("Payment not completed")
            
            booking = payment.booking
            user = booking.user
            trip = booking.trip
            
            # Build trip details
            trip_details = {
                "departure_time": trip.departure_time.isoformat(),
                "route": f"{trip.route.origin_terminal.name} to {trip.route.destination_terminal.name}",
                "bus": trip.bus.license_plate,
                "seats": booking.seat_numbers
            }
            
            return PaymentReceiptData(
                payment_id=payment.id,
                booking_reference=booking.booking_reference,
                passenger_name=f"{user.first_name} {user.last_name}",
                passenger_email=user.email,
                trip_details=trip_details,
                amount=payment.amount,
                currency=payment.currency,
                payment_method=payment.payment_method.value if payment.payment_method else "card",
                transaction_id=payment.gateway_transaction_id or "",
                payment_date=payment.processed_at or payment.created_at
            )
            
        except Exception as e:
            logger.error(f"Error generating receipt data: {str(e)}")
            raise PaymentServiceError(f"Failed to generate receipt: {str(e)}")
    
    # Private helper methods
    
    async def _get_booking_with_details(self, booking_id: UUID) -> Optional[Booking]:
        """Get booking with related details."""
        query = select(Booking).options(
            selectinload(Booking.trip).selectinload("route"),
            selectinload(Booking.trip).selectinload("bus"),
            selectinload(Booking.user)
        ).where(Booking.id == booking_id)
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def _get_payment_by_id(self, payment_id: UUID) -> Optional[Payment]:
        """Get payment by ID."""
        query = select(Payment).where(Payment.id == payment_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def _get_payment_by_transaction_id(self, transaction_id: str) -> Optional[Payment]:
        """Get payment by gateway transaction ID."""
        query = select(Payment).where(Payment.gateway_transaction_id == transaction_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def _update_booking_payment_status(self, booking_id: UUID, status: str):
        """Update booking payment status."""
        query = update(Booking).where(Booking.id == booking_id).values(
            payment_status=status,
            updated_at=datetime.utcnow()
        )
        await self.db.execute(query)
    
    async def _get_or_create_stripe_customer(self, user_id: UUID) -> str:
        """Get or create Stripe customer for user."""
        # Get user details
        query = select(User).where(User.id == user_id)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            raise PaymentServiceError("User not found")
        
        # Check if user already has a Stripe customer ID (you might want to store this)
        # For now, create a new customer each time or search by email
        customers = stripe.Customer.list(email=user.email, limit=1)
        
        if customers.data:
            return customers.data[0].id
        
        # Create new customer
        customer = stripe.Customer.create(
            email=user.email,
            name=f"{user.first_name} {user.last_name}",
            metadata={"user_id": str(user_id)}
        )
        
        return customer.id
    
    async def _get_stripe_customer_id(self, user_id: UUID) -> Optional[str]:
        """Get Stripe customer ID for user."""
        # Get user details
        query = select(User).where(User.id == user_id)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        # Search for existing customer
        customers = stripe.Customer.list(email=user.email, limit=1)
        return customers.data[0].id if customers.data else None