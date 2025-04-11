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

class Currency(Base):
    __tablename__ = "currencies"
    
    # Unique identifier for each currency
    id: Mapped[mappeditem] = mapped_column(UUIDType, primary_key=True, default=default)
    
    # Currency code (USD, EUR, GBP, etc.)
    code: Mapped[str] = mapped_column(String(CHAR_LENGTH), nullable=False, unique=True)
    
    # Currency symbol (e.g., $, €, ¥)
    symbol: Mapped[str] = mapped_column(String(CHAR_LENGTH), nullable=False, unique=True)
    
    # Name of the currency (e.g., US Dollar, Euro, British Pound)
    name: Mapped[str] = mapped_column(String(CHAR_LENGTH), nullable=False, unique=True)

    # Optional - Number of decimals the currency supports (e.g., 2 for USD, 0 for JPY)
    decimals: Mapped[int] = mapped_column(Integer, default=2)

    
    def _to_dict(self):
        """
        Converts the Currency instance to a dictionary.
        """
        return {
            "id": str(self.id),
            "code": self.code,
            "symbol": self.symbol,
            "name": self.name,
            "decimals": self.decimals,
        }
        
    def __repr__(self):
        return f"<Currency(code={self.code}, symbol={self.symbol}, name={self.name})>"


