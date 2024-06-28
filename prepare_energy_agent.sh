#!/bin/bash

# Update and upgrade the system
sudo apt-get update -y
sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh ./get-docker.sh

# Add current user to the Docker group
sudo usermod -aG docker "${USER}"

# Use newgrp docker to run the subsequent commands in a new shell with the updated group
newgrp docker << EOF

# Create a directory for the docker-compose file
mkdir -p ~/energy-agent
cd ~/energy-agent || exit

# Download the docker-compose file from GitHub
# Replace the URL with the actual URL of your docker-compose file
wget https://github.com/rddl-network/EnergyAgent/raw/main/docker-compose.yaml

# Start the Docker Compose
docker compose up -d

# Cleanup
rm ../get-docker.sh

echo "Docker and Docker Compose setup complete. The services are now running."

EOF
