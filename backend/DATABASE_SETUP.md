# Database Setup and Management

This document provides instructions for setting up and managing the Pafar ride booking system database.

## Database Configuration

The application supports both SQLite (for development) and PostgreSQL (for production).

### Environment Configuration

Set the `DATABASE_URL` environment variable in your `.env` file:

**For Development (SQLite):**
```
DATABASE_URL=sqlite:///./pafar.db
```

**For Production (PostgreSQL):**
```
DATABASE_URL=postgresql://username:password@localhost:5432/database_name
```

## Database Models

The system includes the following core models:

### User Model
- Supports customers, drivers, and admin users
- Includes authentication, profile, and rating information
- Fields: id, email, phone, full_name, user_type, is_verified, is_active, profile_image_url, average_rating, total_rides

### Ride Model
- Manages ride lifecycle from request to completion
- Includes fare calculation, timing, and status tracking
- Fields: id, customer_id, driver_id, pickup_location_id, destination_location_id, status, estimated_fare, actual_fare, distance, timestamps

### Location Model
- Stores pickup and destination locations
- Includes geocoding information
- Fields: id, latitude, longitude, address, city, country, postal_code

### Payment Model
- Handles payment processing and transaction history
- Integrates with Stripe payment gateway
- Fields: id, ride_id, user_id, amount, currency, payment_method_id, stripe_payment_intent_id, status, timestamps

### DriverLocation Model
- Real-time driver location tracking
- Supports availability status and movement data
- Fields: id, driver_id, latitude, longitude, heading, speed, is_available, updated_at

## Database Management Commands

Use the `scripts/manage_db.py` script for database operations:

### Check Database Connection
```bash
python scripts/manage_db.py check
```

### Initialize Database Tables
```bash
python scripts/manage_db.py init
```

### Reset Database (WARNING: Deletes all data)
```bash
python scripts/manage_db.py reset
```

### Seed Database with Sample Data
```bash
python scripts/manage_db.py seed
```

## Migration Management

The application uses Alembic for database migrations.

### Create a New Migration
```bash
python -m alembic revision --autogenerate -m "Description of changes"
```

### Apply Migrations
```bash
python -m alembic upgrade head
```

### Rollback Migration
```bash
python -m alembic downgrade -1
```

### View Migration History
```bash
python -m alembic history
```

### View Current Migration
```bash
python -m alembic current
```

## Database Indexes and Performance

The system includes optimized indexes for:

### Rides Table
- Customer and driver lookups
- Status-based queries
- Date range queries
- Composite indexes for common query patterns

### Payments Table
- User payment history
- Ride payment lookups
- Status-based filtering
- Stripe integration queries

### Locations Table
- Geospatial queries (latitude/longitude)
- City and country filtering

### Driver Locations Table
- Real-time availability queries
- Geospatial proximity searches
- Recent location updates

### Users Table
- User type filtering
- Active/verified user queries
- Authentication lookups

## Sample Data

The seeding script creates:
- 3 sample customers
- 3 sample drivers
- 1 admin user
- 5 sample locations in Lagos, Nigeria
- 3 completed rides with payments
- Driver location data

All sample users use the password hash "testhash" (replace with proper hashing in production).

## Production Considerations

### PostgreSQL Setup
1. Install PostgreSQL
2. Create database and user
3. Update DATABASE_URL in environment
4. Run migrations: `python -m alembic upgrade head`

### Security
- Use strong passwords for database users
- Enable SSL connections in production
- Regularly backup database
- Monitor for unusual query patterns

### Performance
- Monitor query performance with database logs
- Consider connection pooling for high traffic
- Implement database monitoring and alerting
- Regular maintenance and optimization

### Backup Strategy
- Implement automated daily backups
- Test backup restoration procedures
- Store backups in secure, separate location
- Document recovery procedures

## Troubleshooting

### Common Issues

**Connection Refused Error:**
- Check if database server is running
- Verify DATABASE_URL is correct
- Ensure database exists and user has permissions

**Migration Errors:**
- Check for conflicting schema changes
- Verify all models are imported in migrations/env.py
- Review migration files for syntax errors

**Performance Issues:**
- Check query execution plans
- Verify indexes are being used
- Monitor connection pool usage
- Review slow query logs

### Environment Variables

Ensure these environment variables are set:
- `DATABASE_URL`: Database connection string
- `SECRET_KEY`: Application secret key (32+ characters)
- `JWT_SECRET_KEY`: JWT signing key (32+ characters)

## Development Workflow

1. Make model changes in `app/models/`
2. Update Pydantic schemas in `app/schemas/`
3. Generate migration: `python -m alembic revision --autogenerate -m "Description"`
4. Review and edit migration file if needed
5. Apply migration: `python -m alembic upgrade head`
6. Test changes with sample data
7. Update tests and documentation

## Testing

The database configuration supports separate test databases:
- Use in-memory SQLite for unit tests
- Use separate PostgreSQL database for integration tests
- Reset database state between test runs
- Mock external services in tests