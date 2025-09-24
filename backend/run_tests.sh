#!/bin/bash

# Run tests for Keeda backend

echo "Starting MongoDB for testing..."
# Ensure MongoDB is running (you may need to adjust this for your setup)
docker ps | grep mongodb > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "Starting MongoDB container..."
    docker run -d -p 27017:27017 --name mongodb mongo:7.0
    sleep 3
fi

echo "Running tests..."

# Run specific test suites
if [ "$1" = "models" ]; then
    echo "Running model tests..."
    pytest tests/test_models.py -v
elif [ "$1" = "repos" ]; then
    echo "Running repository tests..."
    pytest tests/test_repositories.py -v
elif [ "$1" = "fast" ]; then
    echo "Running fast tests (no integration)..."
    pytest -m "not slow" -v
else
    echo "Running all tests..."
    pytest tests/ -v --cov=app --cov-report=term-missing
fi

echo "Tests completed!"