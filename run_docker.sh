#!/bin/bash

# Define color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Check if an argument is provided
if [ -z "$1" ]; then
    echo -e "${YELLOW}Usage: $0 <environment> [up|down [delete]]${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Initializing ..."

# Check if the system is running Linux
if [ "$(uname)" == "Linux" ]; then
    echo -e "${GREEN}✓${NC} System OS: Linux Detected"
    
    # Get the IP address of the Linux system
    ip_address=$(hostname -I | awk '{print $1}')
    echo -e "${GREEN}✓${NC} IP Address: $ip_address"
    
    # Step 1: Copy the environment file
    echo "Step 1: Copying the environment file..."
    cp ./backend/userservice/.env.local ./backend/userservice/.env
    cp ./backend/bookingservice/.env.local ./backend/bookingservice/.env
    cp ./backend/analyticsservice/.env.local ./backend/analytics/.env
fi

# Function to create the network and volume
create_network_and_volume() {
    # Create the Docker network if it doesn't exist
    docker network create webnet || echo "Network 'webnet' already exists or failed to create"

    # Create the Docker volume if it doesn't exist
    # docker volume create --name users-db-data || echo "Volume 'users-db-data' already exists or failed to create"
    # docker volume create --name bookings-db-data || echo "Volume 'bookings-db-data' already exists or failed to create"
    # docker volume create --name analytics-db-data || echo "Volume 'analytics-db-data' already exists or failed to create"

}

# Function to start containers
start_containers() {
    create_network_and_volume
    # Build docker-compose for development
    docker-compose -f docker-compose.dev.yml build
    
    # Run docker-compose for the specified environment
    docker-compose -f docker-compose.dev.yml up -d
}

# Function to stop containers
stop_containers() {
    docker-compose down
}


# Function to stop and remove containers, images, volumes, and orphan containers
stop_and_remove_containers() {
    docker-compose down --rmi all --volumes --remove-orphans
}

# Function to handle environment-specific actions
handle_environment() {
    case "$1" in
        "dev")
            compose_file="docker-compose.dev.yml"
            ;;
        "prod")
            compose_file="docker-compose.prod.yml"
            ;;
        *)
            echo -e "${RED}Invalid environment! Please specify 'dev' or 'prod'.${NC}"
            exit 1
            ;;
    esac
    
    if [ "$2" == "up" ]; then
        start_containers
    elif [ "$2" == "down" ]; then
        if [ "$3" == "delete" ]; then
            stop_and_remove_containers
        else
            stop_containers
        fi
    else
        echo "Usage: $0 {up|down [delete]}"
        exit 1
    fi
}

# Main script logic
handle_environment "$1" "$2" "$3"
