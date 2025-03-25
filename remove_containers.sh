#!/bin/bash

# Stop and remove all Docker containers
echo -e "\e[32m✓\e[0m Stopping all running Docker containers..."
docker stop $(docker ps -q)

echo -e "\e[32m✓\e[0m Removing all Docker containers..."
docker rm $(docker ps -a -q)
docker system prune -a -f

# Take down all Docker Compose services
echo -e "\e[32m✓\e[0m Taking down all Docker Compose services..."
docker-compose -f docker-compose.dev.yml down
docker-compose -f docker-compose.prod.yml down


echo -e "\e[32m✓\e[0m All Docker containers have been stopped and removed, and Docker Compose services have been taken down."
