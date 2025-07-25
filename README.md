# Pafar Ride Booking System

A comprehensive ride booking platform built with FastAPI, React, and Flutter.

## 🏗️ Architecture

- **Backend**: FastAPI with kafka, PostgreSQL and Redis
- **Frontend**: React with Vite and TypeScript
- **Mobile**: Flutter for iOS and Android
- **Infrastructure**: Docker, kafka and Docker Compose

## 📁 Project Structure

```
pafar/
├── backend/                 # FastAPI backend application
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Core configuration and database
│   │   ├── models/         # SQLAlchemy models
│   │   ├── services/       # Business logic services
│   │   └── utils/          # Utility functions
│   ├── migrations/         # Alembic database migrations
│   ├── scripts/           # Database and utility scripts
│   └── tests/             # Backend tests
├── frontend/               # React frontend application
│   ├── src/
│   │   ├── components/    # Reusable React components
│   │   ├── contexts/      # React contexts
│   │   ├── pages/         # Page components
│   │   └── test/          # Frontend tests
│   └── public/            # Static assets
├── mobile/                 # Flutter mobile application
│   ├── lib/
│   │   ├── app/           # App configuration
│   │   ├── core/          # Core utilities and DI
│   │   └── features/      # Feature modules
│   └── test/              # Mobile tests
└── .kiro/                 # Kiro specifications and tasks
    └── specs/
        └── ride-booking-system/
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher
- Flutter 3.10 or higher (for mobile development)
- PostgreSQL 14 or higher
- Redis 7 or higher
- Docker and Docker Compose (optional)

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd pafar
   ```

2. **Run the setup script**
   ```bash
   ./setup.sh
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

### Development

#### Using Docker (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

#### Manual Setup

1. **Start Backend**
   ```bash
   cd backend
   source ../.venv/bin/activate
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Start Frontend**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Start Mobile App**
   ```bash
   cd mobile
   flutter run
   ```

## 🗄️ Database

### Migrations

```bash
cd backend
source ../.venv/bin/activate

# Create a new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Database Management

```bash
cd backend
source ../.venv/bin/activate

# Check database connection
python scripts/manage_db.py check

# Initialize database
python scripts/manage_db.py init

# Reset database (WARNING: Deletes all data)
python scripts/manage_db.py reset

# Seed database with initial data
python scripts/manage_db.py seed
```

## 🧪 Testing

### Backend Tests
```bash
cd backend
source ../.venv/bin/activate
pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

### Mobile Tests
```bash
cd mobile
flutter test
```

## 📦 Deployment

### Production Build

```bash
# Build all services for production
docker-compose -f docker-compose.prod.yml build

# Deploy to production
docker-compose -f docker-compose.prod.yml up -d
```

### Environment Configuration

Create production environment files:
- `.env.production` - Production environment variables
- Update `docker-compose.prod.yml` with production settings

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://pafar_user:pafar_password@localhost:5432/pafar_db` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379` |
| `SECRET_KEY` | Application secret key | Required |
| `JWT_SECRET_KEY` | JWT signing key | Required |
| `STRIPE_SECRET_KEY` | Stripe payment processing key | Optional |
| `GOOGLE_MAPS_API_KEY` | Google Maps API key | Optional |

### API Documentation

Once the backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🏃‍♂️ Development Workflow

### Task Management

This project uses Kiro specs for feature development:

1. **View Tasks**: Open `.kiro/specs/ride-booking-system/tasks.md`
2. **Execute Tasks**: Use Kiro to execute individual tasks
3. **Track Progress**: Tasks are marked as completed when finished

### Code Style

- **Backend**: Black, isort, flake8
- **Frontend**: ESLint, Prettier
- **Mobile**: Dart formatter

### Git Workflow

1. Create feature branch from `main`
2. Implement changes following the task specifications
3. Run tests and ensure they pass
4. Submit pull request for review

## 📚 API Reference

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `POST /auth/refresh` - Refresh JWT token

### Rides
- `POST /rides` - Create ride request
- `GET /rides/{id}` - Get ride details
- `PUT /rides/{id}/status` - Update ride status

### Users
- `GET /users/profile` - Get user profile
- `PUT /users/profile` - Update user profile

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Check the documentation in `/docs`
- Review the task specifications in `.kiro/specs`
- Create an issue in the repository

## 🔄 Status

This project is currently in development. The following tasks have been completed:

- ✅ Task 1: Project structure and core infrastructure setup
- ⏳ Task 2: Core data models and database schema (Next)

See `.kiro/specs/ride-booking-system/tasks.md` for the complete task list and progress.