from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import Session, selectinload
from apps.user.models.user import User, UUID
from apps.user.schemas.user import ProductCreate, ProductUpdate
from core.utils.reponse import Response
import sys, json
from datetime import datetime
from sqlalchemy import exc, func

# Define a custom exception for product not found
class ProductNotFoundException(Exception):
    def __init__(self, message="Product not found", code=None):
        self.message = message
        self.code = code
        super().__init__(self.message)

    def __str__(self):
        return f"{self.message}"



# Service function to get all products

async def get_users_by_demographics(
    db: AsyncSession, 
    age: int = None, 
    gender: str = None, 
    skip: int = 0, 
    limit: int = 10
):
    query = select(User).offset(skip).limit(limit).options(selectinload(User.addresses))

    # Apply the filters only if the arguments are provided
    if age is not None:
        query = query.filter(User.age == age)

    if gender is not None:
        query = query.filter(User.gender == gender)

    # Execute the query asynchronously and retrieve the results
    result = await db.execute(query)

    # Return the results as a list of users
    users = result.scalars().all()
    return users


async def get_users_by_address(
    db: AsyncSession, 
    street: str = None, 
    city: str = None, 
    state: str = None, 
    country: str = None, 
    post_code: str = None, 
    kind: str = None, 
    skip: int = 0, 
    limit: int = 10
):
    query = select(User).offset(skip).limit(limit).options(selectinload(User.addresses))

    # Apply filters only if the values are provided
    if street is not None:
        query = query.filter(User.addresses.any(Address.street == street))
    
    if city is not None:
        query = query.filter(User.addresses.any(Address.city == city))

    if state is not None:
        query = query.filter(User.addresses.any(Address.state == state))

    if country is not None:
        query = query.filter(User.addresses.any(Address.country == country))

    if post_code is not None:
        query = query.filter(User.addresses.any(Address.post_code == post_code))

    if kind is not None:
        query = query.filter(User.addresses.any(Address.kind == kind))

    # Execute the query asynchronously and retrieve the results
    result = await db.execute(query)

    # Return the results as a list of users
    users = result.scalars().all()
    return users

async def get_users_by_date(
    db: AsyncSession, 
    created_at: str = None
):
    # If created_at is provided, convert it to a datetime object
    if created_at:
        try:
            # Convert the string date to a datetime object
            created_at_datetime = datetime.fromisoformat(created_at)
        except ValueError:
            raise ValueError("Invalid date format. Please provide a valid ISO 8601 date string.")
    else:
        created_at_datetime = None

    # Build the query
    query = select(User).options(selectinload(User.addresses))

    # If created_at is provided, apply the filter
    if created_at_datetime:
        query = query.filter(User.created_at == created_at_datetime)

    # Execute the query asynchronously
    result = await db.execute(query)
    
    # Fetch all the results
    users = result.scalars().all()

    return users  # Return all users matching the criteria

# Customer Acquisition Report: Tracks the number of new customers acquired over a specific period.

async def get_new_customers_count(
    db: AsyncSession, 
    start_date: str = None, 
    end_date: str = None
):
    # Convert string dates to datetime objects if provided
    if start_date:
        try:
            start_date_datetime = datetime.fromisoformat(start_date)
        except ValueError:
            raise ValueError("Invalid start date format. Please provide a valid ISO 8601 date string.")
    else:
        start_date_datetime = None
    
    if end_date:
        try:
            end_date_datetime = datetime.fromisoformat(end_date)
        except ValueError:
            raise ValueError("Invalid end date format. Please provide a valid ISO 8601 date string.")
    else:
        end_date_datetime = None

    # Build the query to count new users acquired in the specified date range
    query = select(User).options(selectinload(User.addresses))

    # Apply date range filters if provided
    if start_date_datetime and end_date_datetime:
        query = query.filter(User.created_at >= start_date_datetime, User.created_at <= end_date_datetime)
    elif start_date_datetime:
        query = query.filter(User.created_at >= start_date_datetime)
    elif end_date_datetime:
        query = query.filter(User.created_at <= end_date_datetime)

    # Execute the query asynchronously
    result = await db.execute(query)
    
    # Fetch the count of users created within the date range
    new_customers_count = result.scalars().count()

    return new_customers_count

# Customer Retention Report: Shows the percentage of customers who continue to shop with the business after their first purchase.
async def get_repeat_customer_percentage(db: AsyncSession):
    # Query to find users with at least one purchase
    query_total = select(User).join(Order).distinct()  # Ensures that we only count users who have made purchases
    result_total = await db.execute(query_total)
    total_users_count = result_total.rowcount  # Get the total number of users with at least one purchase

    if total_users_count == 0:
        return 0  # If no users have made purchases, the percentage is 0%

    # Query to find users with more than one purchase
    query_repeat = (
        select(User)
        .join(Order)
        .group_by(User.id)
        .having(func.count(Order.id) > 1)  # Filter users with more than one purchase
    )
    result_repeat = await db.execute(query_repeat)
    repeat_users_count = result_repeat.rowcount  # Get the count of repeat customers

    # Calculate the percentage of repeat customers
    repeat_percentage = (repeat_users_count / total_users_count) * 100

    return repeat_percentage

# Average Order Value (AOV): Reports on the average value of customer orders, helping to evaluate purchasing behavior.
async def get_average_order_value(db: AsyncSession):
    # Query to calculate the total order value and total number of orders
    query = select(func.sum(Order.total_amount).label("total_value"), func.count(Order.id).label("total_orders"))

    result = await db.execute(query)

    # Fetch the result
    total_value, total_orders = result.scalar()

    # If no orders exist, return 0 to avoid division by zero
    if total_orders == 0:
        return 0

    # Calculate the average order value
    average_order_value = total_value / total_orders

    return average_order_value

# Lifetime Value (LTV): Estimates the total value a customer will bring over their lifetime, providing insights into long-term customer retention.
# LTV=Average Order Value (AOV)×Purchase Frequency (PF)×Customer Lifetime (CL)
async def get_customer_lifetime_value(db: AsyncSession):
    # Calculate Average Order Value (AOV)
    query_aov = select(func.avg(Order.total_amount).label("average_order_value"))
    result_aov = await db.execute(query_aov)
    average_order_value = result_aov.scalar()

    if average_order_value is None:
        return 0  # If there are no orders, LTV will be 0

    # Calculate Purchase Frequency (PF)
    query_pf = select(func.count(Order.id).label("total_orders"), func.count(func.distinct(Order.user_id)).label("total_customers"))
    result_pf = await db.execute(query_pf)
    total_orders, total_customers = result_pf.scalar()

    if total_customers == 0:
        return 0  # Avoid division by zero

    purchase_frequency = total_orders / total_customers

    # Calculate Customer Lifetime (CL)
    query_cl = select(func.min(Order.created_at).label("first_order_date"), func.max(Order.created_at).label("last_order_date"))
    result_cl = await db.execute(query_cl)
    first_order_date, last_order_date = result_cl.scalar()

    if first_order_date and last_order_date:
        customer_lifetime_years = (last_order_date - first_order_date).days / 365.25
    else:
        customer_lifetime_years = 0  # If there are no valid dates, return 0

    # Calculate LTV: AOV * PF * CL
    customer_lifetime_value = average_order_value * purchase_frequency * customer_lifetime_years

    return customer_lifetime_value

# Customer Segmentation: This categorizes customers into groups based on behavior (e.g., frequent shoppers, high spenders, etc.).
async def segment_customers(db: AsyncSession):
    # Get current date to calculate recency
    current_date = datetime.now()

    # Query to get Recency, Frequency, and Monetary values for each customer
    query = select(
        Order.user_id,
        func.max(Order.created_at).label('last_purchase_date'),
        func.count(Order.id).label('purchase_count'),
        func.sum(Order.total_amount).label('total_spent')
    ).group_by(Order.user_id)

    result = await db.execute(query)

    
    recency_dict = {}
    frequency_dict = {}
    total_spent_dict = {}
    
    for row in result:
        user_id = row.user_id
        last_purchase_date = row.last_purchase_date
        purchase_count = row.purchase_count
        total_spent = row.total_spent

        # Calculate Recency (secs since last purchase)
        recency = (current_date - last_purchase_date).seconds

        recency_dict[recency]=user_id
        frequency_dict[purchase_count]=user_id
        total_spent_dict[total_spent]=user_id

    customer_segments = {
        "recency": dict(sorted(recency_dict.items(), key=lambda item: item[0], reverse=True)), # Sort the dictionary by keys in descending order (highest to lowest)
        "frequency": dict(sorted(frequency_dict.items(), key=lambda item: item[0], reverse=True)), # Sort the dictionary by keys in descending order (highest to lowest)
        "total_spent": dict(sorted(total_spent_dict.items(), key=lambda item: item[0], reverse=True)) # Sort the dictionary by keys in descending order (highest to lowest)
        }
   
    
    return customer_segments