"""Add indexes and constraints for performance optimization

Revision ID: 9ce070ba8747
Revises: 4900a3e8969c
Create Date: 2025-07-25 12:24:20.716620

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9ce070ba8747'
down_revision: Union[str, None] = '4900a3e8969c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add indexes for better query performance
    
    # Rides table indexes
    op.create_index('ix_rides_customer_id', 'rides', ['customer_id'])
    op.create_index('ix_rides_driver_id', 'rides', ['driver_id'])
    op.create_index('ix_rides_status', 'rides', ['status'])
    op.create_index('ix_rides_requested_at', 'rides', ['requested_at'])
    op.create_index('ix_rides_completed_at', 'rides', ['completed_at'])
    
    # Composite indexes for common queries
    op.create_index('ix_rides_customer_status', 'rides', ['customer_id', 'status'])
    op.create_index('ix_rides_driver_status', 'rides', ['driver_id', 'status'])
    op.create_index('ix_rides_status_requested_at', 'rides', ['status', 'requested_at'])
    
    # Payments table indexes
    op.create_index('ix_payments_ride_id', 'payments', ['ride_id'])
    op.create_index('ix_payments_user_id', 'payments', ['user_id'])
    op.create_index('ix_payments_status', 'payments', ['status'])
    op.create_index('ix_payments_created_at', 'payments', ['created_at'])
    op.create_index('ix_payments_stripe_payment_intent_id', 'payments', ['stripe_payment_intent_id'])
    
    # Composite indexes for payments
    op.create_index('ix_payments_user_status', 'payments', ['user_id', 'status'])
    
    # Locations table indexes for geospatial queries
    op.create_index('ix_locations_latitude_longitude', 'locations', ['latitude', 'longitude'])
    op.create_index('ix_locations_city', 'locations', ['city'])
    op.create_index('ix_locations_country', 'locations', ['country'])
    
    # Driver locations indexes for real-time tracking
    op.create_index('ix_driver_locations_is_available', 'driver_locations', ['is_available'])
    op.create_index('ix_driver_locations_updated_at', 'driver_locations', ['updated_at'])
    op.create_index('ix_driver_locations_lat_lng', 'driver_locations', ['latitude', 'longitude'])
    
    # Composite index for finding available drivers
    op.create_index('ix_driver_locations_available_updated', 'driver_locations', ['is_available', 'updated_at'])
    
    # Users table additional indexes
    op.create_index('ix_users_user_type', 'users', ['user_type'])
    op.create_index('ix_users_is_active', 'users', ['is_active'])
    op.create_index('ix_users_is_verified', 'users', ['is_verified'])
    op.create_index('ix_users_created_at', 'users', ['created_at'])
    
    # Composite indexes for user queries
    op.create_index('ix_users_type_active', 'users', ['user_type', 'is_active'])
    op.create_index('ix_users_type_verified', 'users', ['user_type', 'is_verified'])


def downgrade() -> None:
    # Drop indexes in reverse order
    
    # Users table indexes
    op.drop_index('ix_users_type_verified', table_name='users')
    op.drop_index('ix_users_type_active', table_name='users')
    op.drop_index('ix_users_created_at', table_name='users')
    op.drop_index('ix_users_is_verified', table_name='users')
    op.drop_index('ix_users_is_active', table_name='users')
    op.drop_index('ix_users_user_type', table_name='users')
    
    # Driver locations indexes
    op.drop_index('ix_driver_locations_available_updated', table_name='driver_locations')
    op.drop_index('ix_driver_locations_lat_lng', table_name='driver_locations')
    op.drop_index('ix_driver_locations_updated_at', table_name='driver_locations')
    op.drop_index('ix_driver_locations_is_available', table_name='driver_locations')
    
    # Locations table indexes
    op.drop_index('ix_locations_country', table_name='locations')
    op.drop_index('ix_locations_city', table_name='locations')
    op.drop_index('ix_locations_latitude_longitude', table_name='locations')
    
    # Payments table indexes
    op.drop_index('ix_payments_user_status', table_name='payments')
    op.drop_index('ix_payments_stripe_payment_intent_id', table_name='payments')
    op.drop_index('ix_payments_created_at', table_name='payments')
    op.drop_index('ix_payments_status', table_name='payments')
    op.drop_index('ix_payments_user_id', table_name='payments')
    op.drop_index('ix_payments_ride_id', table_name='payments')
    
    # Rides table indexes
    op.drop_index('ix_rides_status_requested_at', table_name='rides')
    op.drop_index('ix_rides_driver_status', table_name='rides')
    op.drop_index('ix_rides_customer_status', table_name='rides')
    op.drop_index('ix_rides_completed_at', table_name='rides')
    op.drop_index('ix_rides_requested_at', table_name='rides')
    op.drop_index('ix_rides_status', table_name='rides')
    op.drop_index('ix_rides_driver_id', table_name='rides')
    op.drop_index('ix_rides_customer_id', table_name='rides')