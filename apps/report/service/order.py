from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import Order  # Assuming Order model exists

async def order_status_report(db: AsyncSession):
    # Query to count orders based on their status
    query = select(Order.status, func.count(Order.id).label('order_count'))\
        .group_by(Order.status)

    result = await db.execute(query)
    
    status_report = {row.status: row.order_count for row in result}
    return status_report
async def abandoned_cart_report(db: AsyncSession):
    # Query to fetch users with items in their cart but no completed orders
    query = select(Order.user_id, func.count(Order.id).label('abandoned_count'))\
        .filter(Order.status == 'pending', Order.payment_status == 'unpaid')\
        .group_by(Order.user_id)

    result = await db.execute(query)
    
    abandoned_report = {row.user_id: row.abandoned_count for row in result}
    return abandoned_report
from datetime import datetime, timedelta

async def order_fulfillment_report(db: AsyncSession, start_date: datetime, end_date: datetime):
    # Query to count orders that were fulfilled within the specified time frame
    query = select(func.count(Order.id).label('fulfilled_orders'))\
        .filter(Order.status == 'shipped', Order.fulfilled_date >= start_date, Order.fulfilled_date <= end_date)

    result = await db.execute(query)
    
    return result.scalar()  # Returns the count of orders fulfilled in the given time period
async def return_refund_report(db: AsyncSession):
    # Query to count orders that were returned or refunded
    query = select(Order.status, func.count(Order.id).label('return_refund_count'))\
        .filter(Order.status.in_(['returned', 'refunded']))\
        .group_by(Order.status)

    result = await db.execute(query)
    
    return {row.status: row.return_refund_count for row in result}
async def shipping_report(db: AsyncSession):
    # Query to get shipping status, delivery time, and shipping cost
    query = select(Order.shipping_status, func.avg(Order.shipping_cost).label('avg_shipping_cost'),
                   func.avg(Order.delivery_time).label('avg_delivery_time'))\
        .group_by(Order.shipping_status)

    result = await db.execute(query)
    
    shipping_report = {row.shipping_status: {'avg_shipping_cost': row.avg_shipping_cost,
                                              'avg_delivery_time': row.avg_delivery_time}
                       for row in result}
    
    return shipping_report
async def order_cancellation_report(db: AsyncSession):
    # Query to get orders that were canceled, along with reasons
    query = select(Order.cancellation_reason, func.count(Order.id).label('cancelled_count'))\
        .filter(Order.status == 'canceled')\
        .group_by(Order.cancellation_reason)

    result = await db.execute(query)
    
    cancellation_report = {row.cancellation_reason: row.cancelled_count for row in result}
    
    return cancellation_report
