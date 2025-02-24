#!/bin/bash

# Set up logging
exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1

# Update and install packages
yum update -y
yum install -y docker git aws-cli

# Set up Docker
systemctl start docker
systemctl enable docker

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Add ec2-user to docker group
usermod -a -G docker ec2-user

# Set up application
mkdir -p /app
cd /app

# Create Docker Compose configuration
cat > docker-compose.yml <<'COMPOSE'
version: '3.8'
services:
  web:
    image: drupal:latest
    ports:
      - "80:80"
    environment:
      - MYSQL_HOST=${RDS_ENDPOINT}
      - MYSQL_USER=${DB_USER}
      - MYSQL_PASSWORD=${DB_PASSWORD}
      - MYSQL_DATABASE=${DB_NAME}
      - S3_BUCKET=${S3_BUCKET_NAME}
    volumes:
      - drupal_data:/var/www/html
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

volumes:
  drupal_data:
COMPOSE

# Pull and start the application
docker pull drupal:latest
docker-compose up -d