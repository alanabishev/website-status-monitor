#!/bin/bash
# build the Docker image
docker build --no-cache -t website_checker .

# ask user to enter the environment variables
read -p "Enter database host: " DATABASE_HOST
read -p "Enter database port: " DATABASE_PORT
read -p "Enter database name: " DATABASE_NAME
read -p "Enter database user: " DATABASE_USER
read -sp "Enter database password: " DATABASE_PASSWORD

# run the Docker container
docker run -p 8000:8000 \
    -e DATABASE_HOST="$DATABASE_HOST" \
    -e DATABASE_PORT="$DATABASE_PORT" \
    -e DATABASE_NAME="$DATABASE_NAME" \
    -e DATABASE_USER="$DATABASE_USER" \
    -e DATABASE_PASSWORD="$DATABASE_PASSWORD" \
    website_checker
