#!/bin/bash

# Pafar Ride Booking System Setup Script
# This script sets up the development environment for the Pafar ride booking platform

set -e

echo "🚀 Setting up Pafar Ride Booking System..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.11 or higher."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18 or higher."
    exit 1
fi

# Check if Flutter is installed
if ! command -v flutter &> /dev/null; then
    echo "⚠️  Flutter is not installed. Mobile app development will not be available."
    echo "   To install Flutter, visit: https://flutter.dev/docs/get-started/install"
fi

echo "✅ Prerequisites check completed"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment and install backend dependencies
echo "📦 Installing backend dependencies..."
source .venv/bin/activate
cd backend
pip install -r requirements-minimal.txt
cd ..

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd frontend
npm install
cd ..

# Install mobile dependencies if Flutter is available
if command -v flutter &> /dev/null; then
    echo "📦 Installing mobile dependencies..."
    cd mobile
    flutter pub get
    cd ..
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️  Creating environment configuration..."
    cp .env.example .env
    echo "📝 Please update the .env file with your configuration values"
fi

# Copy .env to backend directory
cp .env backend/.env

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Update the .env file with your configuration values"
echo "2. Install and start PostgreSQL and Redis services"
echo "3. Run database migrations (will be available in task 2)"
echo "4. Start the development servers:"
echo "   - Backend: cd backend && source ../.venv/bin/activate && uvicorn app.main:app --reload"
echo "   - Frontend: cd frontend && npm run dev"
echo "   - Mobile: cd mobile && flutter run (requires device/emulator)"
echo ""
echo "For Docker setup:"
echo "1. Install Docker and Docker Compose"
echo "2. Run: docker-compose up -d"
echo ""
echo "📚 Check the README.md for detailed instructions"