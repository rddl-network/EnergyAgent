#!/bin/bash

# Update and upgrade the system
sudo apt-get update -y
sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Create a directory for the docker-compose file
mkdir -p ~/energy-agent
cd ~/energy-agent || exit

# Download the docker-compose file from GitHub
# Replace the URL with the actual URL of your docker-compose file
curl -L https://github.com/rddl-network/EnergyAgent/blob/main/docker-compose.yaml -o docker-compose.yml

# Start the Docker Compose
sudo docker compose up -d

# Cleanup
rm get-docker.sh

echo "Docker and Docker Compose setup complete. The services are now running."
