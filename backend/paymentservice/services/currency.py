from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status
from uuid import UUID
from typing import List, Optional

from models.currency import Currency
from schemas.currency import CurrencyCreate, CurrencyUpdate, CurrencyOut


class CurrencyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_currency(self, data: CurrencyCreate) -> CurrencyOut:
        try:
            new_currency = Currency(**data.dict())
            self.db.add(new_currency)
            await self.db.commit()
            await self.db.refresh(new_currency)
            return CurrencyOut.from_orm(new_currency)
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create currency"
            )

    async def get_all_currencies(self) -> List[CurrencyOut]:
        try:
            result = await self.db.execute(select(Currency))
            currencies = result.scalars().all()
            return [CurrencyOut.from_orm(c) for c in currencies]
        except SQLAlchemyError:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch currencies"
            )

    async def get_currency_by_id(self, currency_id: UUID) -> CurrencyOut:
        currency = await self.db.get(Currency, currency_id)
        if not currency:
            raise HTTPException(status_code=404, detail="Currency not found")
        return CurrencyOut.from_orm(currency)

    async def update_currency(self, currency_id: UUID, data: CurrencyUpdate) -> CurrencyOut:
        currency = await self.db.get(Currency, currency_id)
        if not currency:
            raise HTTPException(status_code=404, detail="Currency not found")

        for key, value in data.dict(exclude_unset=True).items():
            setattr(currency, key, value)

        try:
            self.db.add(currency)
            await self.db.commit()
            await self.db.refresh(currency)
            return CurrencyOut.from_orm(currency)
        except SQLAlchemyError:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update currency"
            )

    async def delete_currency(self, currency_id: UUID) -> bool:
        currency = await self.db.get(Currency, currency_id)
        if not currency:
            raise HTTPException(status_code=404, detail="Currency not found")

        try:
            await self.db.delete(currency)
            await self.db.commit()
            return true
        except SQLAlchemyError:
            await self.db.rollback()
            return False
