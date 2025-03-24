from sqlalchemy.orm import mapped_column, Mapped, relationship, validates
from sqlalchemy import Enum, Integer, String, DateTime, ForeignKey, Boolean
from core.database import Base, CHAR_LENGTH
from core.utils.encryption import PasswordManager
from uuid import uuid4  # to generate unique UUIDs
from datetime import datetime
from enum import Enum as PyEnum
from typing import List, Optional
from uuid import UUID
import sys


# Database type detection for UUID support
if 'postgresql' in sys.argv:
    UUIDType = UUID(as_uuid=True)
    mappeditem = UUID
    default = uuid4
else:
    UUIDType = String(36)
    mappeditem = str
    default = lambda: str(uuid4())


# Enum for the type of clicks (can be extended if needed)
class ClickType(PyEnum):
    PRODUCT = 'Product'
    CATEGORY = 'Category'

# Detailed Clicks model to capture both product and category clicks
class Clicks(Base):
    __tablename__ = "clicks"
    
    # Unique identifier for each click record
    id: Mapped[mappeditem] = mapped_column(UUIDType, primary_key=True, default=default)
    
    # Timestamp when the click occurred (UTC)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # The type of click, either product or category (as Enum)
    click_type: Mapped[ClickType] = mapped_column(Enum(ClickType), nullable=False)
    
    # Foreign key reference to a product (if click is on a product)
    product_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("products.id"), nullable=True)
    
    # Foreign key reference to a category (if click is on a category)
    category_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("categories.id"), nullable=True)
    
    # Session ID to track the session of the user clicking
    session_id: Mapped[str] = mapped_column(String(CHAR_LENGTH), nullable=True)
    
    # User IP address to identify from where the click originated (could be used for analytics)
    ip_address: Mapped[str] = mapped_column(String(CHAR_LENGTH), nullable=True)  # For IPv6 support
    
    # User agent string to track the browser or device being used (useful for device analytics)
    user_agent: Mapped[str] = mapped_column(String(CHAR_LENGTH), nullable=True)
    
    # User identifier if available (optional, this could be related to a logged-in user)
    user_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    
    
    ispromotional: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # product recommendations
    # related products
    # featured product areas

    # filters like "Price Range", "Color", "Size", "Brand", etc., to refine the product selection within a category.
    filters: Mapped[str] = mapped_column(String(CHAR_LENGTH), nullable=True) #eg '#color, #price'


    # Method to return a detailed dictionary representation of the click
    def to_dict(self):
        return {
            "id": str(self.id),
            "timestamp": self.timestamp.isoformat(),
            "click_type": self.click_type.value,
            "product_id": str(self.product_id) if self.product_id else None,
            "category_id": str(self.category_id) if self.category_id else None,
            "session_id": self.session_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "user_id": str(self.user_id) if self.user_id else None,
            "filters":self.filters,
            "ispromotional":self.ispromotional
        }

    def __repr__(self):
        return f"Click(id={self.id!r}, timestamp={self.timestamp!r}, click_type={self.click_type!r})"

