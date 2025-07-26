"""
Tracking and review models for real-time location and feedback.
"""
import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, DECIMAL, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class TripLocation(Base):
    """Trip location model for real-time GPS tracking."""
    
    __tablename__ = "trip_locations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trip_id = Column(UUID(as_uuid=True), ForeignKey("trips.id"), nullable=False)
    latitude = Column(DECIMAL(10, 8), nullable=False)
    longitude = Column(DECIMAL(11, 8), nullable=False)
    speed = Column(DECIMAL(5, 2), nullable=True)
    heading = Column(DECIMAL(5, 2), nullable=True)
    recorded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    trip = relationship("Trip", back_populates="locations")
    
    def __repr__(self) -> str:
        return f"<TripLocation(id={self.id}, trip={self.trip_id}, lat={self.latitude}, lng={self.longitude})>"


class Review(Base):
    """Review model for trip ratings and feedback."""
    
    __tablename__ = "reviews"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_id = Column(UUID(as_uuid=True), ForeignKey("bookings.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    driver_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5 rating
    comment = Column(Text, nullable=True)
    is_moderated = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    booking = relationship("Booking", back_populates="reviews")
    user = relationship("User", back_populates="reviews_given", foreign_keys=[user_id])
    driver = relationship("User", back_populates="reviews_received", foreign_keys=[driver_id])
    
    @property
    def is_valid_rating(self) -> bool:
        """Check if rating is within valid range."""
        return 1 <= self.rating <= 5
    
    def __repr__(self) -> str:
        return f"<Review(id={self.id}, booking={self.booking_id}, rating={self.rating})>"