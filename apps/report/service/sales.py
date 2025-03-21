from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from datetime import datetime

async def total_sales_report(db: AsyncSession, start_date: datetime, end_date: datetime):
    query = select(func.sum(Order.total_amount).label('total_sales'))\
        .filter(Order.created_at >= start_date, Order.created_at <= end_date)

    result = await db.execute(query)
    
    return result.scalar()  # Returns the total sales revenue in the specified time period
async def sales_by_product_report(db: AsyncSession, start_date: datetime, end_date: datetime):
    query = select(Product.name, func.sum(OrderItem.total_amount).label('total_sales'))\
        .join(OrderItem, Order.id == OrderItem.order_id)\
        .join(Product, Product.id == OrderItem.product_id)\
        .filter(Order.created_at >= start_date, Order.created_at <= end_date)\
        .group_by(Product.name)

    result = await db.execute(query)
    
    return {row.name: row.total_sales for row in result}
async def sales_by_category_report(db: AsyncSession, start_date: datetime, end_date: datetime):
    query = select(Category.name, func.sum(OrderItem.total_amount).label('total_sales'))\
        .join(OrderItem, Order.id == OrderItem.order_id)\
        .join(Product, Product.id == OrderItem.product_id)\
        .join(Category, Category.id == Product.category_id)\
        .filter(Order.created_at >= start_date, Order.created_at <= end_date)\
        .group_by(Category.name)

    result = await db.execute(query)
    
    return {row.name: row.total_sales for row in result}
async def sales_by_region_report(db: AsyncSession, start_date: datetime, end_date: datetime):
    query = select(Region.name, func.sum(Order.total_amount).label('total_sales'))\
        .join(Region, Region.id == Order.shipping_region_id)\
        .filter(Order.created_at >= start_date, Order.created_at <= end_date)\
        .group_by(Region.name)

    result = await db.execute(query)
    
    return {row.name: row.total_sales for row in result}
async def sales_by_time_report(db: AsyncSession, start_date: datetime, end_date: datetime):
    query = select(func.extract('hour', Order.created_at).label('hour'),
                   func.sum(Order.total_amount).label('total_sales'))\
        .filter(Order.created_at >= start_date, Order.created_at <= end_date)\
        .group_by(func.extract('hour', Order.created_at))

    result = await db.execute(query)
    
    return {row.hour: row.total_sales for row in result}
async def sales_by_payment_method_report(db: AsyncSession, start_date: datetime, end_date: datetime):
    query = select(PaymentMethod.name, func.sum(Order.total_amount).label('total_sales'))\
        .join(PaymentMethod, PaymentMethod.id == Order.payment_method_id)\
        .filter(Order.created_at >= start_date, Order.created_at <= end_date)\
        .group_by(PaymentMethod.name)

    result = await db.execute(query)
    
    return {row.name: row.total_sales for row in result}

async def sales_by_discount_report(db: AsyncSession, start_date: datetime, end_date: datetime):
    query = select(Discount.code, func.sum(Order.total_amount).label('total_sales'))\
        .join(Discount, Discount.id == Order.discount_id)\
        .filter(Order.created_at >= start_date, Order.created_at <= end_date)\
        .group_by(Discount.code)

    result = await db.execute(query)
    
    return {row.code: row.total_sales for row in result}
