#!/bin/bash

#!/bin/bash

# Define color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Check if an argument is provided
if [ -z "$1" ]; then
    echo -e "${YELLOW}Usage: $0 <environment>${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Intializing ..."

# Check if the system is running Linux
if [ "$(uname)" == "Linux" ]; then
    echo -e "${GREEN}✓${NC} System OS: Linux Detected"
    
    # getting the ip address
    # Get the IP address of the Linux system
    ip_address=$(hostname -I | awk '{print $1}')


# Function to create the network and volume
create_network_and_volume() {
    # Create the Docker network if it doesn't exist
    docker network create webnet || echo "Network webnet already exists or failed to create"

    # Create the Docker volume if it doesn't exist
    docker volume create --name users-db-data || echo "Volume users-db-data already exists or failed to create"
}

# Function to start containers
start_containers() {
    create_network_and_volume
    # biuld docker-compose for development
    docker-compose -f docker-compose.dev.yml build
    # Run docker-compose for development environment
    docker-compose -f docker-compose.dev.yml up -d
}

# Function to stop containers
stop_containers() {
    docker-compose down
}

# Function to stop and remove containers
stop_and_remove_containers() {
    docker-compose down --rmi all --volumes --remove-orphans
}

# Main script logic
if [ "$1" == "dev" ]; then
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
elif [ "$1" == "prod" ]; then
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
else
    echo "Usage: $0 {dev [up|down [delete] ] |prod [up|down [delete] ] }"
    exit 1
fi
