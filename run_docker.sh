#!/bin/bash

# Pafar Ride Booking System Docker Runner
# This script provides various options for running the system

set -e

# Default values
ENVIRONMENT="development"
BUILD=false
DETACHED=false
SERVICES=""

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS] [SERVICES]"
    echo ""
    echo "Options:"
    echo "  -e, --env ENV        Environment (development|production) [default: development]"
    echo "  -b, --build          Force rebuild of images"
    echo "  -d, --detached       Run in detached mode"
    echo "  -h, --help           Show this help message"
    echo ""
    echo "Services (optional):"
    echo "  backend              Run only backend service"
    echo "  frontend             Run only frontend service"
    echo "  db                   Run only database service"
    echo "  redis                Run only Redis service"
    echo ""
    echo "Examples:"
    echo "  $0                   Start all services in development mode"
    echo "  $0 -e production     Start all services in production mode"
    echo "  $0 -b -d             Build and start all services in detached mode"
    echo "  $0 backend db        Start only backend and database services"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--env)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -b|--build)
            BUILD=true
            shift
            ;;
        -d|--detached)
            DETACHED=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        backend|frontend|db|redis)
            SERVICES="$SERVICES $1"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Validate environment
if [[ "$ENVIRONMENT" != "development" && "$ENVIRONMENT" != "production" ]]; then
    echo "❌ Invalid environment: $ENVIRONMENT"
    echo "Valid environments: development, production"
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cp .env.example .env
    echo "✅ Please update .env file with your configuration"
fi

# Build Docker Compose command
COMPOSE_FILE="docker-compose.yml"
if [[ "$ENVIRONMENT" == "production" ]]; then
    COMPOSE_FILE="docker-compose.prod.yml"
fi

DOCKER_CMD="docker-compose -f $COMPOSE_FILE"

# Add build flag if requested
if [[ "$BUILD" == true ]]; then
    DOCKER_CMD="$DOCKER_CMD up --build"
else
    DOCKER_CMD="$DOCKER_CMD up"
fi

# Add detached flag if requested
if [[ "$DETACHED" == true ]]; then
    DOCKER_CMD="$DOCKER_CMD -d"
fi

# Add specific services if provided
if [[ -n "$SERVICES" ]]; then
    DOCKER_CMD="$DOCKER_CMD$SERVICES"
fi

echo "🚀 Starting Pafar Ride Booking System..."
echo "📝 Environment: $ENVIRONMENT"
echo "🐳 Command: $DOCKER_CMD"
echo ""

# Execute the command
eval $DOCKER_CMD

if [[ "$DETACHED" == true ]]; then
    echo ""
    echo "✅ Services started in detached mode"
    echo "📊 Check status: docker-compose ps"
    echo "📋 View logs: docker-compose logs -f"
    echo "🛑 Stop services: docker-compose down"
else
    echo ""
    echo "🛑 Press Ctrl+C to stop all services"
fi