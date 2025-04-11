from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional


# Shared base schema
class CurrencyBase(BaseModel):
    code: str = Field(..., example="USD")
    symbol: str = Field(..., example="$")
    name: str = Field(..., example="US Dollar")
    decimals: Optional[int] = Field(default=2, example=2)


# Schema for creating a new currency
class CurrencyCreate(CurrencyBase):
    pass


# Schema for updating an existing currency
class CurrencyUpdate(BaseModel):
    code: Optional[str] = None
    symbol: Optional[str] = None
    name: Optional[str] = None
    decimals: Optional[int] = None


# Schema for reading/returning currency data
class CurrencyOut(CurrencyBase):
    id: UUID

    class Config:
        from_attributes = True
